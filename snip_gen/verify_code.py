"""Execute code."""

import argparse
import logging
import shutil
import subprocess  # noqa: S404
import sys
from pathlib import Path

from snip_gen.typehints import VerifyArgs

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


TCL_ROOT = Path(__file__).parent.resolve() / "tcl"


OPENROAD = shutil.which("openroad") or ""

OPENROAD_CMD = [OPENROAD, "-exit", "-no_init", "-no_splash", "-no_settings", "-threads", "max"]

VERIFY_DEF = [*OPENROAD_CMD.copy(), str(TCL_ROOT / "check_def.tcl")]


def _handle_result(result: subprocess.CompletedProcess[str], step: str) -> tuple[bool, str]:
    """Handle the result of a subprocess run.

    Args:
        result (subprocess.CompletedProcess): The result of the subprocess run.
        step (str): A description of the step being executed, used for logging.

    Returns:
        A tuple where the first element is a boolean indicating whether the code is valid,
        and the second element is a string containing any error messages or an empty string if valid.
    """
    debug_end = "-" * len(step)

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    res = stdout or stderr

    if stdout:
        if result.returncode != 0:
            logger.warning(f"--- {step} STDOUT ---")
            logger.warning(stdout)
            logger.warning(f"---------------{debug_end}")
        else:
            logger.debug(f"--- {step} STDOUT ---")
            logger.debug(stdout)
            logger.debug(f"---------------{debug_end}")

    if stderr:
        logger.error(f"--- {step} STDERR ---")
        logger.error(stderr)
        logger.error(f"---------------{debug_end}")

    if result.returncode != 0:
        logger.error(f"Error running OpenRoad: {res}")
        return False, res
    return True, res


def verify_code(file: Path, library_files: list[Path]) -> tuple[bool, str]:
    """Verify that the given file contains valid code.

    Args:
        file (Path): The path to the file to be verified.
        library_files (list[Path]): A list of paths to library files that are required for the verification.

    Returns:
        A tuple where the first element is a boolean indicating whether the code is valid,
        and the second element is a string containing any error messages or an empty string if valid.

    Raises:
        RuntimeError: If the verification is unavailable.
    """
    if not OPENROAD:
        msg = "OpenRoad is not available"
        raise RuntimeError(msg)

    # Safety: the executed command is hardcoded and does not include user input.
    result = subprocess.run(  # noqa: S603
        VERIFY_DEF,
        check=False,
        capture_output=True,
        encoding="utf-8",
        env={
            "DEF_FILE": str(file.resolve()),
            "LEF_FILES": " ".join(str(lef.resolve()) for lef in library_files),
        },
    )

    return _handle_result(result, "Verifying DEF file")


def write_code(file_path: Path, code: str) -> None:
    """Write the given code content to the specified file path, ensuring a trailing newline.

    Args:
        file_path (Path): The path where the code should be saved.
        code (str): The content of the code.
    """
    # Ensure directory exists, handle case where file_path is just a filename
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure the code ends with a newline
    if not code.endswith("\n"):
        code += "\n"
    with file_path.open("w", encoding="utf-8") as f:
        f.write(code)
    logger.info(f"Code successfully written to: {file_path}")


def register(parser: argparse.ArgumentParser) -> None:
    """Register the command-line parser for verifying code.

    Args:
        parser (argparse.ArgumentParser): The argument parser to register the command with.
    """
    parser.add_argument(
        "file",
        type=Path,
        help="The file to verify.",
    )

    parser.add_argument("--library", required=False, nargs="*", type=Path, help="Library files to be included")

    parser.set_defaults(func=main)


def validate_args(arguments: argparse.Namespace) -> VerifyArgs | None:
    """Validate the command-line arguments.

    Args:
        arguments (argparse.Namespace): The parsed command-line arguments.

    Returns:
        VerifyArgs | None: A VerifyArgs object if validation is successful, otherwise None.
    """
    args = VerifyArgs(
        file=Path(arguments.file),
        library=[Path(f) for f in arguments.library or []],
    )

    ret_args: VerifyArgs | None = args

    if not args.file.exists():
        logger.error(f"The specified file does not exist: {arguments.file}")
        ret_args = None

    for file in args.library:
        if not file.exists():
            logger.error(f"Library file does not exist: {file}")
            ret_args = None

    return ret_args


def main(arguments: argparse.Namespace) -> None:
    """Verify the code in the specified file.

    Args:
        arguments (argparse.Namespace): The parsed command-line arguments.

    Exit codes:
        0: Verification successful.
        1: Verification failed.
        2: Invalid arguments.
    """
    args = validate_args(arguments)
    if not args:
        logger.error("Invalid arguments provided. Exiting.")
        sys.exit(2)

    is_valid, error_message = verify_code(args.file, args.library)

    if is_valid:
        logger.info("Code verification successful.")
        sys.exit(0)
    else:
        logger.error(f"Code verification failed: {error_message}")
        sys.exit(1)


__all__ = ["register", "verify_code", "write_code"]


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(description="Verify code files.")
    register(_parser)
    main(_parser.parse_args())
