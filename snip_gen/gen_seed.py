"""Generate a seed."""

import argparse
import json
import logging
import re
import sys
import tempfile
import typing as t
from pathlib import Path

from snip_gen import COVERAGE_MAX, DEFAULT_COVERAGE, DEFAULT_FILE_EXTENSION, MAX_FILENAME_LENGTH, MODELS
from snip_gen.analyze_coverage import find_low_coverage_from_json
from snip_gen.gen_snippet import CodeGeneratorAgent
from snip_gen.snip_gen import MAX_FILE_SIZE_BYTES
from snip_gen.typehints import SeedGenArgs, load_coverage

if t.TYPE_CHECKING:
    from snip_gen.typehints import Coverage, LowCoverageFiles

logger = logging.getLogger(__name__)


def extract_function_code(file_content: str, start_line: int) -> str | None:
    """Extract the code for a function from file content based on start line and indentation.

    Args:
        file_content (str): The content of the file as a string.
        start_line (int): The line number where the function starts (1-based index).

    Returns:
        str | None: The extracted function code as a string, or None if extraction fails.
    """
    lines = file_content.splitlines()
    if start_line < 1 or start_line > len(lines):
        return None

    start_index = start_line - 1
    start_line_text = lines[start_index]
    match = re.match(r"^(\s*)", start_line_text)
    if not match:
        return None
    base_indent = len(match.group(1))

    extracted_lines = [start_line_text]
    for i in range(start_index + 1, len(lines)):
        line = lines[i]
        # Get indentation of the current line
        match = re.match(r"^(\s*)", line)
        indent = len(match.group(1)) if match else 0
        # Stop if indentation is less than base_indent and line is not empty
        if indent < base_indent and line.strip():
            break
        extracted_lines.append(line)
    return "\n".join(extracted_lines)


def sanitize_filename(name: str) -> str:
    """Sanitizes a string to be used as a filename.

    Args:
        name (str): The string to sanitize.

    Returns:
        str: A sanitized version of the string suitable for use as a filename.
    """
    # Replace characters that are not letters, numbers, or hyphens with underscores
    s = re.sub(r"[^\w-]", "_", name)
    # Collapse multiple underscores into one
    s = re.sub(r"_{2,}", "_", s)
    # Truncate if too long (optional, but good practice)
    if len(s) > MAX_FILENAME_LENGTH:
        s = s[:MAX_FILENAME_LENGTH]
    return s


def handle_function(args: SeedGenArgs, agent: CodeGeneratorAgent, coverage_data: "Coverage") -> tuple[int, int]:
    """Generate code for functions with zero coverage based on the provided coverage data.

    Args:
        args (SeedGenArgs): The arguments for seed generation.
        agent (CodeGeneratorAgent): The code generator agent to use.
        coverage_data (Coverage): The coverage data loaded from the fastcov JSON file.

    Returns:
        tuple[int, int]: A tuple containing the number of successful and failed generation attempts.
    """
    success = 0
    failure = 0

    logger.info("Analyzing coverage data for zero-coverage functions...")

    targeted_functions = []
    for file_path, coverage_info in coverage_data.items():
        file = Path(file_path)

        if not file.exists():
            logger.error(f"Target file '{file}' not found. Skipping.")
            continue

        for function_name, function_coverage_info in coverage_info["functions"].items():
            if function_coverage_info["execution_count"] == 0:
                targeted_functions.append((file, function_name, function_coverage_info["start_line"]))

    if not targeted_functions:
        logger.info("No zero-coverage functions found in the coverage report.")
        return 0, 0

    logger.info(f"Found {len(targeted_functions)} zero-coverage functions. Attempting to generate files...")

    for file, function_name, start_line in targeted_functions:
        logger.info(f"\n--- Processing function: {function_name} in {file} ---")

        with file.open(encoding="utf-8") as f:
            file_content = f.read()

        # Extract the function code based on the found line number
        function_code = extract_function_code(file_content, start_line)

        if function_code is None:
            logger.error(f"Failed to extract code snippet for function '{function_name}' in '{file}'. Skipping.")
            failure += 1
            continue

        # Sanitize function name for filename
        sanitized_function_name = sanitize_filename(function_name)

        output_file = args.output_dir / f"{file.stem}_{sanitized_function_name}{args.extension}"

        if output_file.exists():
            logger.warning(f"Output file '{output_file}' already exists. Skipping generation for this function.")
            continue

        logger.info(f"Attempting to generate code for function '{function_name}' -> '{output_file}'")
        logger.info("Writing extracted snippet to temporary file")
        with tempfile.NamedTemporaryFile(encoding="utf-8", mode="w+", delete_on_close=False) as f:
            f.write(function_code)
            f.close()

            logger.info("Calling agent with temporary snippet file")

            generated_code = agent.generate_code(
                target_file=Path(f.name), output_file=output_file, library=args.library, coverage={}
            )

        if generated_code:
            logger.info(
                f"Successfully generated and verified design for function '{function_name}'. Saved to '{output_file}'."
            )
            success += 1
        else:
            logger.error(
                f"Failed to generate a design for function '{function_name}' after {args.max_retries + 1} attempts."
            )
            failure += 1
        logger.info(f"--- Finished processing function {function_name} ---")

    return success, failure


def generate_files(
    args: SeedGenArgs, agent: CodeGeneratorAgent, low_coverage_files: "LowCoverageFiles"
) -> tuple[int, int]:
    """Generate code for files with low coverage based on the provided coverage data.

    Args:
        args (SeedGenArgs): The arguments for seed generation.
        agent (CodeGeneratorAgent): The code generator agent to use.
        low_coverage_files (LowCoverageFiles): List of files with low coverage.

    Returns:
        tuple[int, int]: A tuple containing the number of successful and failed generation attempts.
    """
    success = 0
    failure = 0

    for file_path, coverage_percent, coverage_details in low_coverage_files:
        logger.info(f"\n--- Processing file: {file_path} (Coverage: {coverage_percent:.2f}%) ---")

        if not file_path.exists():
            logger.error(f"Target file '{file_path}' not found. Skipping.")
            failure += 1
            continue

        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            logger.error(
                f"File '{file_path}' exceeds the maximum size of {MAX_FILE_SIZE_BYTES / 1024:.2f} KB. "
                "Skipping generation for this file."
            )
            failure += 1
            continue

        output_file = args.output_dir / file_path.with_suffix(args.extension).name

        if output_file.exists():
            logger.warning(f"Output file '{output_file}' already exists. Skipping generation for this file.")
            continue

        logger.info(f"Attempting to generate design for '{file_path}' -> '{output_file}'")

        generated_code = agent.generate_code(
            target_file=file_path, library=args.library, output_file=output_file, coverage=coverage_details["lines"]
        )
        if generated_code:
            logger.info(f"Successfully generated valid design for '{file_path}'. Saved to '{output_file}'.")
            success += 1
        else:
            logger.error(f"Failed to generate a design for '{file_path}' after {args.max_retries + 1} attempts.")
            failure += 1
    return success, failure


def handle_file(args: SeedGenArgs, agent: CodeGeneratorAgent, coverage_data: "Coverage") -> tuple[int, int]:
    """Handle generation targeting low-coverage files.

    Args:
        args (SeedGenArgs): The arguments for seed generation.
        agent (CodeGeneratorAgent): The code generator agent to use.
        coverage_data (Coverage): The coverage data loaded from the fastcov JSON file.

    Returns:
        tuple[int, int]: A tuple containing the number of successful and failed generation attempts.
    """
    if args.min_threshold > 0:
        logger.info(
            f"Analyzing coverage from {args.fastcov_json} for files with coverage between {args.min_threshold}% "
            f"and {args.threshold}%."
        )
    else:
        logger.info(f"Analyzing coverage from {args.fastcov_json} for files with coverage below {args.threshold}%.")

    low_coverage_files = find_low_coverage_from_json(coverage_data, args.threshold, args.min_threshold)

    if not low_coverage_files:
        if args.min_threshold > 0.0:
            logger.warning(f"No files found with coverage between {args.min_threshold:.2f}% and {args.threshold:.2f}%.")
        else:
            logger.warning(f"No files found with coverage below {args.threshold:.2f}%.")
        return 0, 0

    if args.min_threshold > 0:
        logger.info(
            f"Found {len(low_coverage_files)} files with coverage between "
            f"{args.min_threshold:.2f}% and {args.threshold:.2f}%."
        )
    else:
        logger.info(f"Found {len(low_coverage_files)} files with coverage below {args.threshold:.2f}%. ")

    return generate_files(args, agent, low_coverage_files)


def register(parser: argparse.ArgumentParser) -> None:
    """Register the command-line parser for seed generation.

    Args:
        parser (argparse.ArgumentParser): The argument parser to register the command with.
    """
    parser.add_argument(
        "--fastcov-json",
        default=DEFAULT_COVERAGE,
        type=Path,
        help="Path to the fastcov coverage.json file (default: coverage.json).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=40.0,
        help="Upper coverage threshold percentage (0-100). Files below this will be targeted (default: 40.0).",
    )
    parser.add_argument(
        "--min-threshold",
        type=float,
        default=0.0,
        help=(
            "Lower coverage threshold percentage (0-100). "
            "Files at or above this threshold (and below --threshold) will be targeted. Default: 0.0"
        ),
    )
    parser.add_argument(
        "--model", required=True, choices=MODELS, help="The language model to use for snippet generation."
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of attempts to fix errors for each snippet (default: 3).",
    )
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory to save the generated files.")
    parser.add_argument(
        "--target",
        choices=["file", "function"],
        default="file",
        help=(
            'Target for snippet generation: "file" for low-coverage files,'
            '"function" for zero-coverage functions (default: file).'
        ),
    )
    parser.add_argument(
        "--extension",
        default=DEFAULT_FILE_EXTENSION,
        help=f"File extension of generated code files. (default: {DEFAULT_FILE_EXTENSION})",
    )
    parser.add_argument("--library", required=False, nargs="*", type=Path, help="Library files to be included")

    parser.set_defaults(func=main)


def validate_args(arguments: argparse.Namespace) -> SeedGenArgs | None:
    """Validate arguments.

    Args:
        arguments (argparse.Namespace): The parsed command-line arguments.

    Returns:
        SeedGenArgs | None: A SeedGenArgs object if validation passes, None otherwise.
    """
    args = SeedGenArgs(
        threshold=arguments.threshold,
        min_threshold=arguments.min_threshold,
        fastcov_json=Path(arguments.fastcov_json),
        output_dir=Path(arguments.output_dir),
        model=arguments.model,
        max_retries=arguments.max_retries,
        target=arguments.target,
        library=[Path(f) for f in arguments.library],
        extension=arguments.extension,
    )

    ret_args: SeedGenArgs | None = args

    if not (0.0 <= args.threshold <= COVERAGE_MAX):
        logger.error("Threshold must be between 0.0 and 100.0.")
        ret_args = None
    if not (0.0 <= args.min_threshold <= COVERAGE_MAX):
        logger.error("Min-threshold must be between 0.0 and 100.0.")
        ret_args = None
    if args.min_threshold >= args.threshold:
        logger.error("Min-threshold must be less than threshold.")
        ret_args = None

    if not args.fastcov_json.exists():
        logger.error(f"Fastcov JSON file not found: {args.fastcov_json}")
        ret_args = None

    for file in args.library:
        if not file.exists():
            logger.error(f"Library file not found: {file}")
            ret_args = None

    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured output directory exists: {args.output_dir}")
    except OSError:
        logger.exception(f"Could not create output directory {args.output_dir}")
        ret_args = None
    return ret_args


def main(arguments: argparse.Namespace) -> None:
    """Generate code for files or functions with low code coverage.

    Args:
        arguments (argparse.Namespace): The parsed command-line arguments.
    """
    args = validate_args(arguments)

    if args is None:
        logger.critical("Invalid arguments provided. Exiting.")
        sys.exit(1)

    try:
        coverage_data: Coverage = load_coverage(args.fastcov_json)
    except json.JSONDecodeError:
        logger.critical(f"Error decoding JSON from {args.fastcov_json}. Is it a valid JSON file?")
        sys.exit(1)

    agent = CodeGeneratorAgent(model_type=args.model, max_retries=args.max_retries)

    if args.target == "file":
        success, failure = handle_file(args, agent, coverage_data)
    else:
        success, failure = handle_function(args, agent, coverage_data)

    logger.info("--- Generation summary ---")

    logger.info(f"Succeeded in generating {success} designs.")
    logger.info(f"Failed to generate {failure} designs.")
    logger.info(f"Success rate: {success / (success + failure) * 100:.2f}%")
    logger.info("--------------------------")

    sys.exit(1 if failure else 0)


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(description="Generate designs for files or functions with low code coverage.")

    register(_parser)

    main(_parser.parse_args())
