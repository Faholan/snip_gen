"""Generate code with an LLM."""

import argparse
import sys

from .analyze_coverage import register as register_coverage
from .gen_seed import register as register_seed
from .gen_snippet import register as register_snippet


def main() -> None:
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

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_usage()
        sys.exit(1)


def snippet_command() -> None:
    """Run the snippet generation command."""
    sys.argv = [sys.argv[0], "snippet"] + sys.argv[1:]
    main()


def coverage_command() -> None:
    """Run the coverage analysis command."""
    sys.argv = [sys.argv[0], "coverage"] + sys.argv[1:]
    main()


def seed_command() -> None:
    """Run the seed generation command."""
    sys.argv = [sys.argv[0], "seed"] + sys.argv[1:]
    main()


if __name__ == "__main__":
    main()
