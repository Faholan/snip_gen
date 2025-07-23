"""Fix generated DEF code."""

import re

REPLACEMENTS = [
    (
        re.compile(r"#.*?$", re.MULTILINE),  # Remove comments
        "",
    ),
    (  # Fiw bad UNITS definition
        re.compile(r"UNITS\s*?(?:DATABASE|DISTANCE)\s*?(?:MICRONS)?\s*?(\d+)\s*?;?(?:\s*END UNITS)?", re.IGNORECASE),
        r"UNITS DISTANCE MICRONS \1;",
    ),
    (  # Fix bad block definitions missing a semicolon
        re.compile(
            r"(COMPONENTS|FILLS|GROUPS|NETS|NONDEFAULTRULES|PINS|PINPROPERTIES|PROPERTYDEFINITIONS|REGIONS|SCANCHAINS|SPECIALNETS|VIAS)\s*?(\d)\s*?$",
            re.MULTILINE,
        ),
        r"\1 \2 ;",
    ),
    (  # Fix bad VIA LAYER definitions
        re.compile(r"(VIAS.*)LAYER (\w+) RECT(.*END VIAS)", re.DOTALL),
        r"\1RECT \2\3",
    ),
    (  # Remove ANTENNA definitions
        re.compile(r"\+\s*?ANTENNA\w*\d*\s*\w*\w*\s*"),
        "",
    ),
    (
        re.compile(r"(PINS.*^\s*)(LAYER|PORT)(.*END PINS)", re.MULTILINE | re.DOTALL),
        r"\1+ \2\3",  # Add a '+' before LAYER or PORT in PINS
    ),
    (  # Remove any MUSTJOIN net
        re.compile(r"^.*MUSTJOIN.*$", re.MULTILINE),
        "",
    ),
    (
        re.compile(r"(PINS.*)LAYER\s*(\w+)\s*RECT(.*END PINS)", re.DOTALL),
        r"\1LAYER \2\3",  # Remove LAYER xxx RECT from PINS
    ),
    (
        re.compile(r"(SPECIALNETS.*)WIDTH(.*END SPECIALNETS)", re.DOTALL),
        r"\1\2",  # Remove WIDTH from SPECIALNETS
    ),
    (
        re.compile(r"(NETS.*)WIDTH(?:\s*\d+)?(.*END NETS)", re.DOTALL),
        r"\1\2",  # Remove WIDTH from NETS
    ),
    (
        re.compile(r"(COMPONENTS.*)(PLACED|FIXED|COVER)\s*(\d+)\s*(\d+)(\s*\w+.*END COMPONENTS)", re.DOTALL),
        r"\1\2 ( \3 \4 )\5",
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
