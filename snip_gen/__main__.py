"""Generate code with an LLM."""

import argparse
import sys

from .analyze_coverage import register as register_coverage
from .gen_seed import register as register_seed
from .gen_snippet import register as register_snippet


def main(args: list[str] | None = None) -> None:
    """Main CLI entry point for snip_gen."""
    parser = argparse.ArgumentParser(description="Generate code and analyze coverage.", prog="snip_gen")
    subparsers = parser.add_subparsers(help="Command to run")
    register_coverage(
        subparsers.add_parser(
            "coverage", description="Analyze coverage files to find low line coverage.", help="Analyze coverage"
        )
    )
    register_snippet(
        subparsers.add_parser(
            "snippet", description="Generate code snippets from a specific file.", help="Generate a code snippet"
        )
    )
    register_seed(
        subparsers.add_parser(
            "seed",
            description="Generate code seeds to exercise target files using an LLM.",
            help="Handle code seed generation",
        )
    )
    parsed_args = parser.parse_args(args)
    if hasattr(parsed_args, "func"):
        parsed_args.func(parsed_args)
    else:
        parser.print_usage()
        sys.exit(1)


def snippet_command() -> None:
    """Run the snippet generation command."""
    main(["snippet", *sys.argv[1:]])


def coverage_command() -> None:
    """Run the coverage analysis command."""
    main(["coverage", *sys.argv[1:]])


def seed_command() -> None:
    """Run the seed generation command."""
    main(["seed", *sys.argv[1:]])


if __name__ == "__main__":
    main()
