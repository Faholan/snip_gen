"""Typehints."""

import json
import typing as t
from dataclasses import dataclass
from pathlib import Path

if t.TYPE_CHECKING:
    from snip_gen import MODEL_HINT


class CoverageFunction(t.TypedDict):
    """TypedDict for coverage function information.

    Attributes:
        execution_count (int): Number of times the function was executed.
        start_line (int): The line number where the function starts.
    """

    execution_count: int
    start_line: int


class RawCoverageFile(t.TypedDict):
    """Raw JSON coverage file information.

    Attributes:
        branches (dict[str, list[int]]): Branch coverage information.
        functions (dict[str, CoverageFunction]): Function coverage information.
        lines (dict[str, int]): Line coverage information.
    """

    branches: dict[str, list[int]]
    functions: dict[str, CoverageFunction]
    lines: dict[str, int]


_RawCoverageFile = t.TypedDict("_RawCoverageFile", {"": RawCoverageFile})


class RawCoverage(t.TypedDict):
    """Raw JSON coverage data.

    Attributes:
        sources (dict[str, _RawCoverageFile]): Mapping of source files to their coverage data.
    """

    sources: dict[str, _RawCoverageFile]


class CoverageFile(t.TypedDict):
    """Raw JSON coverage file information.

    Attributes:
        branches (dict[int, list[int]]): Branch coverage information.
        functions (dict[str, CoverageFunction]): Function coverage information.
        lines (dict[int, int]): Line coverage information.
    """

    branches: dict[int, list[int]]
    functions: dict[str, CoverageFunction]
    lines: dict[int, int]


Coverage = dict[str, CoverageFile]

LowCoverageFiles = list[tuple[Path, float, CoverageFile]]


def parse_coverage(raw: RawCoverage) -> Coverage:
    """Convert raw coverage data to a better-structured format.

    Args:
        raw (RawCoverage): Raw coverage data as loaded from a JSON file.

    Returns:
        Coverage: A structured dictionary mapping file paths to their coverage data.
    """
    coverage: Coverage = {}

    for source, file_info_ in raw["sources"].items():
        file_info = file_info_[""]
        branches = {}
        lines = {}

        for branch, branch_info in file_info["branches"].items():
            branches[int(branch)] = branch_info

        for line, count in file_info["lines"].items():
            lines[int(line)] = count

        coverage[source] = {"branches": branches, "functions": file_info["functions"], "lines": lines}

    return coverage


def load_coverage(file: Path) -> Coverage:
    """Load coverage data from a JSON file.

    Args:
        file (Path): Path to the JSON file containing raw coverage data.

    Returns:
        Coverage: A structured dictionary mapping file paths to their coverage data.
    """
    with file.open(encoding="utf-8") as f:
        raw_data: RawCoverage = json.load(f)

    return parse_coverage(raw_data)


@dataclass(slots=True)
class SeedGenArgs:
    """Arguments for the seed generation process.

    Attributes:
        threshold (float): Minimum coverage threshold for seed generation.
        min_threshold (float): Minimum threshold for coverage to be considered.
        fastcov_json (Path): Path to the fastcov JSON file containing coverage data.
        output_dir (Path): Directory where generated seeds will be saved.
        model (MODEL_HINT): Model to use for generating seeds.
        max_retries (int): Maximum number of retries for seed generation.
        target (Literal["file", "function"]): Target type for seed generation.
        library (list[Path]): List of library paths to include in the generation.
        extension (str): File extension for the generated seeds.
    """

    threshold: float
    min_threshold: float
    fastcov_json: Path
    output_dir: Path
    model: "MODEL_HINT"
    max_retries: int
    target: t.Literal["file", "function"]
    library: list[Path]
    extension: str


@dataclass(slots=True)
class CoverageArgs:
    """Arguments for coverage analysis.

    Attributes:
        threshold (float): Minimum coverage threshold for analysis.
        min_threshold (float): Minimum threshold for coverage to be considered.
        fastcov_json (Path): Path to the fastcov JSON file containing coverage data.
    """

    threshold: float
    min_threshold: float
    fastcov_json: Path


@dataclass(slots=True)
class SnippetGenArgs:
    """Arguments for snippet generation.

    Attributes:
        model (str): Model to use for generating snippets.
        target (Path): Path to the target file for snippet generation.
        output (Path): Path where the generated snippets will be saved.
        library (list[Path]): List of library paths to include in the generation.
        max_retries (int): Maximum number of retries for snippet generation.
    """

    model: "MODEL_HINT"
    target: Path
    output: Path
    library: list[Path]
    max_retries: int
