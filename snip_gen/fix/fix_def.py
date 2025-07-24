"""Fix generated DEF code."""

import re

BLOCK_RE = (
    "COMPONENTS|FILLS|GROUPS|NETS|NONDEFAULTRULES|PINS|PINPROPERTIES|"
    "PROPERTYDEFINITIONS|REGIONS|SCANCHAINS|SPECIALNETS|VIAS"
)

REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"#.*?$", re.MULTILINE),  # Remove comments
        "",
    ),
    (  # Fiw bad UNITS definition
        re.compile(r"^\s*UNITS\s*?(?:DATABASE)?\s*?(?:MICRONS)?\s*?(\d+)\s*?;?", re.MULTILINE),
        r"UNITS DISTANCE MICRONS \1;",
    ),
    (re.compile(r"END UNITS"), ""),
    (  # Fix bad block definitions missing a semicolon
        re.compile(
            rf"^\s*({BLOCK_RE})\s*?(\d)\s*?$",
            re.MULTILINE,
        ),
        r"\1 \2 ;",
    ),
    (  # Fix bad VIA LAYER definitions
        re.compile(r"^\s*(VIAS.*)LAYER (\w+) RECT(.*END VIAS)", re.DOTALL | re.MULTILINE),
        r"\1RECT \2\3",
    ),
    (  # Remove ANTENNA definitions
        re.compile(r"^\s*\+\s*?ANTENNA\w+\s+[\d.]+\s+\w+\s+\w+", re.MULTILINE),
        "",
    ),
    (
        re.compile(r"^\s*(PINS.*^\s*)(LAYER|PORT)(.*END PINS)", re.DOTALL | re.MULTILINE),
        r"\1+ \2\3",  # Add a '+' before LAYER or PORT in PINS
    ),
    (  # Remove any MUSTJOIN net
        re.compile(r"^.*MUSTJOIN.*$", re.MULTILINE),
        "",
    ),
    (
        re.compile(r"^\s*(PINS.*)LAYER\s+(\w+)\s+RECT(.*END PINS)", re.DOTALL | re.MULTILINE),
        r"\1LAYER \2\3",  # Remove LAYER xxx RECT from PINS
    ),
    (
        re.compile(r"^\s*(SPECIALNETS.*)WIDTH(.*END SPECIALNETS)", re.DOTALL | re.MULTILINE),
        r"\1\2",  # Remove WIDTH from SPECIALNETS
    ),
    (
        re.compile(r"^\s*(NETS.*)WIDTH(?:\s+\d+)?(.*END NETS)", re.DOTALL | re.MULTILINE),
        r"\1\2",  # Remove WIDTH from NETS
    ),
    (
        re.compile(
            r"^\s*((COMPONENTS|PINS).*)(PLACED|FIXED|COVER)\s+(\d+)\s+(\d+)(\s+\w+.*END \2)", re.DOTALL | re.MULTILINE
        ),
        r"\1\2 ( \3 \4 )\5",
    ),
    (
        re.compile(r"^\s*ROW\s+(\w+)\s+(\w+)\s+\((\d+)\s+(\d+)\s*\)?", re.MULTILINE),
        r"ROW \1 \2 \3 \4",
    ),  # Fix issue where generated ROW have parentheses around coordinates
    (
        re.compile(r"^\s*(ROW\s+\w+\s+\w+\s+\d+\s+\d+\s+\w+\s+DO\s+\d+\s+BY\s+\d+\s+STEP\s+\d+\s+);", re.MULTILINE),
        r"\1 0 ;",  # Add missing 0 Y coordinate in ROW definition
    ),
    (
        re.compile(
            r"^\s*(NETS.*)(COVER|FIXED|ROUTED|NOSHIELD|NEW)\s+(\w+)\s+\d+(.*END NETS)", re.DOTALL | re.MULTILINE
        ),
        r"\1\2 \3 \4",  # Remove incorrect width specification in NETS
    ),
    (
        re.compile(
            r'^\s*(PROPERTYDEFINITIONS.*)^(\s*\w+)\s+"(\w+)"?(.*END PROPERTYDEFINITIONS)', re.DOTALL | re.MULTILINE
        ),
        r"\1\2 \3\4",  # Remove quotes around property names in PROPERTYDEFINITIONS
    ),
    (
        re.compile(r"\bR0\b"),
        "N",
    ),
    (
        re.compile(r"\bR180\b"),
        "S",
    ),
    (
        re.compile(r"\bR90\b"),
        "W",
    ),
    (
        re.compile(r"\bR180\b"),
        "E",
    ),
    (
        re.compile(r"\bMY\b"),
        "FN",
    ),
    (
        re.compile(r"\bMX\b"),
        "FS",
    ),
    (
        re.compile(r"\bMX90\b"),
        "FW",
    ),
    (
        re.compile(r"\bMY90\b"),
        "FE",
    ),
    (
        re.compile(r"^(\s*NETS.*)\+\s*PIN\s+\w+(.*END NETS)", re.DOTALL | re.MULTILINE),
        r"\1 \2",  # Remove wrong PIN definition in NETS
    ),
    (re.compile(r"(^\s*VIAS.*^\s*-[\w\s()]*)$(\s*(?:-.*)?END VIAS)", re.DOTALL | re.MULTILINE), r"\1 ; \2"),
    (
        re.compile(r"\b([()])"),
        r" \1",  # Add space before parentheses
    ),
    (
        re.compile(r"([()])\b"),
        r"\1 ",  # Add space before parentheses
    ),
    (
        re.compile(
            rf"^\s*({BLOCK_RE})(?!.*END \1)(.*^\s*(?={BLOCK_RE}))",
            re.DOTALL | re.MULTILINE,
        ),
        r"\1\2END \1\n",
    ),
]


def fix_def(code: str) -> str:
    """Fix the generated DEF design.

    Args:
        code (str): The DEF code to be fixed.

    Returns:
        str: The fixed DEF code.
    """
    for pattern, replacement in REPLACEMENTS:
        subs = 1
        while subs:
            code, subs = pattern.subn(replacement, code)

    return code
