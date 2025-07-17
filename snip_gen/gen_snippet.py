"""Generate code snippets."""

import argparse
import logging
import sys
import typing as t
from pathlib import Path

from snip_gen import MODELS
from snip_gen.llm_handler import LLMHandler
from snip_gen.prompts import get_feedback_prompt, get_initial_prompt, get_system_prompts
from snip_gen.typehints import SnippetGenArgs
from snip_gen.verify_code import verify_code, write_code

if t.TYPE_CHECKING:
    from snip_gen import MODEL_HINT

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CodeGeneratorAgent:
    """Generate and refine a code snippet.

    This class uses a language model to generate code based on a target file.

    Attributes:
        llm_handler (LLMHandler): An instance of LLMHandler to interact with the language model.
        max_retries (int): Maximum number of attempts to fix linting errors.
    """

    def __init__(self, model_type: "MODEL_HINT", max_retries: int = 3) -> None:
        """Initialize the CodeGeneratorAgent.

        Args:
            model_type (str): The type of language model to use.
            max_retries (int): Maximum number of attempts to fix linting errors.

        Raises:
            ValueError: If writing to the file fails.
        """
        try:
            self.llm_handler = LLMHandler(model_type=model_type)
        except ValueError as e:
            msg = "Failed to initialize LLMHandler"
            raise ValueError(msg) from e

        self.max_retries = max_retries

        logger.debug(f"Max retries for fixing lint errors: {self.max_retries}")

    def generate_code(
        self, target_file: Path, library: list[Path], output_file: Path, coverage: dict[int, int]
    ) -> str | None:
        """Generate and refine code until it passes linting.

        This is guided by the content of the target file.

        Args:
            target_file (Path): The path to the target file to maximize coverage for.
            library (list[Path]): List of library files to be included in the generation process.
            output_file (Path): The path where the generated file will be saved.
            coverage (dict[int, int]): Coverage data to be used in the generation process.

        Returns:
            str | None: The generated code if successful, otherwise None.
        """
        target_filename = target_file.name

        try:
            with target_file.open(encoding="utf-8") as f:
                target_content = f.read()
        except (OSError, FileNotFoundError):
            logger.exception(f"Failed to read target file: {target_filename}")
            return None

        system_prompts = get_system_prompts(target_filename, target_content, str(coverage), library)

        initial_prompt = get_initial_prompt(target_filename, target_content, str(coverage), library)

        current_prompt = initial_prompt

        for attempt in range(self.max_retries + 1):
            current_file = output_file.with_suffix(f".{attempt}{output_file.suffix}")

            logger.info(f"--- Attempt {attempt + 1} of {self.max_retries + 1} ---")

            logger.info("Requesting code from LLM...")
            generated_code = self.llm_handler.invoke_llm(current_prompt, *system_prompts)

            if not generated_code.strip():
                logger.warning("LLM returned empty code. Retrying with initial prompt.")
                current_prompt = initial_prompt
                continue

            write_code(current_file, generated_code)

            lint_success, lint_stderr = verify_code(current_file, library)

            if lint_success:
                target_file.symlink_to(current_file)
                logger.info(f"Successfully generated and verified file: {output_file}")
                return generated_code

            logger.error(f"Verification failed for {current_file}.")
            logger.info("Attempting to fix the lint error...")
            current_prompt = get_feedback_prompt(
                target_filename, target_content, str(coverage), library, generated_code, lint_stderr
            )

        failure_suffix = f".failed.{{}}{output_file.suffix}"

        logger.info(
            f"Renaming the output files to indicate failure to {output_file.with_suffix(failure_suffix.format('x'))}."
        )

        for attempt in range(self.max_retries + 1):
            current_file = output_file.with_suffix(f".{attempt}{output_file.suffix}")
            current_file.rename(output_file.with_suffix(failure_suffix.format(attempt)))

        logger.error("Failed to generate a design after all attempts.")
        return None


def register(parser: argparse.ArgumentParser) -> None:
    """Register the command line arguments for the script.

    Args:
        parser (argparse.ArgumentParser): The argument parser to register the arguments with.
    """
    parser.add_argument("--model", required=True, choices=MODELS, help="The language model to use.")
    parser.add_argument(
        "--target", required=True, type=Path, help="The path to the target file within to maximize coverage for."
    )
    parser.add_argument("--output", required=True, type=Path, help="The path where the generated file will be saved.")
    parser.add_argument(
        "--library", required=True, nargs="+", type=Path, help="Library files to be included in the generation process."
    )
    parser.add_argument(
        "--max-retries", type=int, default=3, help="Maximum number of attempts to fix linting errors (default: 3)."
    )

    parser.set_defaults(func=main)


def validate_args(arguments: argparse.Namespace) -> SnippetGenArgs | None:
    """Validate the command line arguments.

    Args:
        arguments (argparse.Namespace): The parsed command line arguments.

    Returns:
        SnippetGenArgs | None: A SnippetGenArgs object if validation is successful, otherwise None.
    """
    args = SnippetGenArgs(
        model=arguments.model,
        target=arguments.target,
        output=arguments.output,
        library=[Path(f) for f in arguments.library],
        max_retries=arguments.max_retries,
    )

    ret_args: SnippetGenArgs | None = args

    if not args.target.exists():
        logger.error(f"Target file not found: {args.target}. Cannot generate code.")
        ret_args = None

    if args.target.resolve() == args.output.resolve():
        logger.error("Target and output file cannot be the same.")
        ret_args = None

    return ret_args


def main(arguments: argparse.Namespace) -> None:
    """Generate code snippets.

    Args:
        arguments (argparse.Namespace): The parsed command line arguments.
    """
    args = validate_args(arguments)
    if not args:
        logger.error("Invalid arguments provided. Exiting.")
        sys.exit(1)

    agent = CodeGeneratorAgent(model_type=args.model, max_retries=args.max_retries)
    successful_code = agent.generate_code(
        target_file=args.target, output_file=args.output, coverage={}, library=args.library
    )

    if successful_code:
        logger.info("--- Successfully generated and verified code ---")
        logger.info(f"Final verified file saved to: {args.output}")
        logger.info("------------------------------------------------")
        sys.exit(0)
    else:
        logger.error("--- Failed to generate valid design ---")
        logger.error("Check logs and the last generated file")
        logger.error("---------------------------------------")
        sys.exit(1)


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(description="Generate valid code exercise a target file using an LLM.")
    register(_parser)
    main(_parser.parse_args())
