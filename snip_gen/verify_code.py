"""Execute code."""

import logging
import shutil
import subprocess  # noqa: S404
from pathlib import Path

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


def verify_code(generated_file: Path, library_files: list[Path]) -> tuple[bool, str]:
    """Verify that the given file contains valid code.

    Args:
        generated_file (Path): The path to the file to be verified.
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
            "DEF_FILE": str(generated_file.resolve()),
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


__all__ = ["verify_code", "write_code"]
