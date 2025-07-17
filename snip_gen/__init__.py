"""Generate code from an LLM based on coverage data."""

import typing as t
from pathlib import Path

COVERAGE_MAX: int = 100
MAX_FILENAME_LENGTH: int = 100

MODULE_ROOT: Path = Path(__file__).parent

DEFAULT_COVERAGE: Path = MODULE_ROOT.parent / "coverage" / "coverage.json"

# Default file extension for generated code snippets.
DEFAULT_FILE_EXTENSION: str = ".def"
# Prefixes to be removed from the LLM output, if present.
CODEBLOCK_STRIPPED_PREFIX: list[str] = ["```def", "```"]

MODEL_HINT = t.Literal["openai", "mistral", "gemini", "gemini-pro"]

LITELLM_MODELS: dict[str, str] = {
    "openai": "o3",  # 'o4-mini'
    "mistral": "mistral/codestral-latest",
    "gemini-pro": "gemini-2.5-pro-exp-06-05",
    "gemini": "gemini/gemini-2.5-flash-preview-05-20",
}

MODELS: list[str] = list(LITELLM_MODELS.keys())

MAX_FILE_SIZE_BYTES: int = 100 * 1024  # 100 KB

MAX_ATTEMPTS = 6  # Maximum number of attempts to invoke the LLM before giving up.
# In case we hit the per-minute rate limit, we will wait for 60 seconds before retrying.
BASE_WAIT = 60  # Base of the exponential backoff in seconds
EXPONENTIAL_FACTOR = 6  # Exponential factor for backoff
