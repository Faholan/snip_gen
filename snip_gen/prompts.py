"""Manage prompts."""

import typing as t

# ruff: noqa: E501, ARG001

if t.TYPE_CHECKING:
    from pathlib import Path


_TECHNOLOGY_SYSTEM_PROMPT = """You are an expert chip designer.
Your task is to generate a chip design in the form of a Design Exchange Format (DEF) file.
The goal is to create diverse patterns in the design, in order to maximize the coverage of OpenROAD's source code.

You have mastered the following technology platform, described in the form of Library Exchange Format (LEF) files:

{lef_files}

CRITICAL REQUIREMENTS:
1. The generated DEF file MUST be syntactically correct and will be verified by OpenROAD.
2. Provide only the complete DEF design in a single code block. Do not include explanations or markdown formatting.
"""

_DEF_SYNTAX_PROMPT = """To be valid, the DEF file must follow the syntax rules of the DEF format, version 5.8.

The statements MUST be in the following order:

[ VERSION statement ]
[ DIVIDERCHAR statement ]
[ BUSBITCHARS statement ]
DESIGN statement
[ UNITS statement ]
[ PROPERTYDEFINITIONS section ]
[ DIEAREA statement ]
[ ROW statement ] ...
[ TRACKS statement ] ...
[ GCELLGRID statement ] ...
[ VIAS statement ]
[ NONDEFAULTRULES statement ]
[ REGIONS statement ]
[ COMPONENTMASKSHIFT statement ]
[ COMPONENTS section ]
[ PINS section ]
[ PINPROPERTIES section ]
[ BLOCKAGES section ]
[ FILLS section ]
[ SPECIALNETS section ]
[ NETS section ]
[ SCANCHAINS section ]
[ GROUPS section ]
END DESIGN statement

The syntax of the every statement (in alphabetical order, NOT the correct order for inclusion in a design file) is as follows:

BLOCKAGES numBlockages ;
    [- LAYER layerName
         [ + SLOTS | + FILLS]
         [ + PUSHDOWN]
         [ + EXCEPTPGNET]
         [ + COMPONENT compName]
         [ + SPACING minSpacing | + DESIGNRULEWIDTH effectiveWidth]
              {RECT pt pt | POLYGON pt pt pt ...} ...
    ;] ...
    [- PLACEMENT
         [ + SOFT | + PARTIAL maxDensity]
         [ + PUSHDOWN]
         [ + COMPONENT compName
           {RECT pt pt} ...
    ;] ...

END BLOCKAGES

BUSBITCHARS "delimiterPair" ;

COMPONENTMASKSHIFT layer1 [layer2 ...] ;

COMPONENTS numComps ;
    [- compName modelName
        [+ SOURCE {NETLIST | DIST | USER | TIMING}]
        [+ {FIXED pt orient | COVER pt orient | PLACED pt orient
               | UNPLACED} ]
        [+ HALO [SOFT] left bottom right top]
        [+ WEIGHT weight]
        [+ REGION regionName]
        [+ PROPERTY {propName propVal} ...]...
    ;] ...

END COMPONENTS

DESIGN designName ;

DIEAREA pt pt [pt] ... ;

DIVIDERCHAR "character" ;

FILLS numFills ;
    [- LAYER layerName [+ MASK maskNum] [+ OPC]
        {RECT pt pt} ... ;] ...

END FILLS

[GCELLGRID {X|Y} start DO num+1 STEP space ;] ...

GROUPS numGroups ;
    [- groupName [compNamePattern ... ]
       [+ REGION regionNam]
       [+ PROPERTY {propName propVal} ...] ...
    ;] ...

END GROUPS

NETS numNets ;
    [- { netName
           [ ( {compName pinName | PIN pinName} [+ SYNTHESIZED] ) ] ...
       | MUSTJOIN ( compName pinName ) }
       [+ NONDEFAULTRULE ruleName]
       [{+ COVER | + FIXED | + ROUTED | + NOSHIELD}
        layerName [TAPER | TAPERRULE ruleName] [STYLE styleNum]
           routingPoints
        [NEW layerName [TAPER | TAPERRULE ruleName] [STYLE styleNum]
           routingPoints
        ] ...] ...
       [+ SOURCE {DIST | NETLIST | TEST | TIMING | USER}]
       [+ FIXEDBUMP]
       [+ USE {ANALOG | CLOCK | GROUND | POWER | RESET | SCAN | SIGNAL
                 | TIEOFF}]
       [+ WEIGHT weight]
       [+ PROPERTY {propName propVal} ...] ...
    ;] ...

END NETS

NONDEFAULTRULES numRules ;
    {- ruleName
          [+ HARDSPACING]
          {+ LAYER layerName
               WIDTH minWidth
               [SPACING minSpacing]
               [WIREEXT wireExt]
          } ...
          [+ VIA viaName] ...
          [+ VIARULE viaRuleName] ...
          [+ MINCUTS cutLayerName numCuts] ...
          [+ PROPERTY {propName propVal} ...] ...
    ;} ...

END NONDEFAULTRULES

PINS numPins ;
    [ - pinName + NET netName
        [+ SPECIAL]
        [+ DIRECTION {INPUT | OUTPUT | INOUT | FEEDTHRU}]
        [+ SUPPLYSENSITIVITY powerPinName]
        [+ GROUNDSENSITIVITY groundPinName]
        [+ USE {SIGNAL | POWER | GROUND | CLOCK | TIEOFF | ANALOG
                  | SCAN | RESET}]
        [+ ANTENNAPINGATEAREA value [LAYER layerName]] ...
        [+ ANTENNAPINMAXAREACAR value LAYER layerName] ...
        [+ ANTENNAPINMAXSIDEAREACAR value LAYER layerName] ...
        [+ ANTENNAPINMAXCUTCAR value LAYER layerName] ...
        [[+ PORT]
         [+ LAYER layerName
             [MASK maskNum]
             [SPACING minSpacing | DESIGNRULEWIDTH effectiveWidth]
               pt pt
         ] ...
         [+ COVER pt orient | FIXED pt orient | PLACED pt orient]
        ]...
    ; ] ...

END PINS

PINPROPERTIES num;
    [- {compName pinName | PIN pinName}
          [+ PROPERTY {propName propVal} ...] ...
    ;] ...

END PINPROPERTIES

PROPERTYDEFINITIONS
    [objectType propName propType [RANGE min max]
       [value | stringValue]
    ;] ...

END PROPERTYDEFINITIONS

REGIONS numRegions ;
    [- regionName {pt pt} ...
       [+ TYPE {FENCE | GUIDE}]
       [+ PROPERTY {propName propVal} ...] ...
    ;] ...

END REGIONS

[ROW rowName siteName origX origY siteOrient
    [DO numX BY numY [STEP stepX stepY]]
    [+ PROPERTY {propName propVal} ...] ... ;] ...

SCANCHAINS numScanChains ;
    [- chainName
       [+ PARTITION partitionName [MAXBITS maxbits]]
       [+ COMMONSCANPINS [ ( IN pin )] [( OUT pin ) ] ]
        + START {fixedInComp | PIN} [outPin]
       [+ FLOATING
          {floatingComp [ ( IN pin ) ] [ ( OUT pin ) ] [ ( BITS numBits ) ]} ...]
       [+ ORDERED
          {fixedComp [ ( IN pin ) ] [ ( OUT pin ) ] [ ( BITS numBits ) ]} ...
       ] ...
        + STOP {fixedOutComp | PIN} [inPin] ]
    ;] ...

END SCANCHAINS

SPECIALNETS numNets ;
    [- netName
       [ ( {compName pinName | PIN pinName} [+ SYNTHESIZED] ) ] ...
      [[+ COVER | + FIXED | + ROUTED]
             [+ SHAPE shapeType] [+ MASK maskNum]
              + RECT layerName pt pt
        |{+ COVER | + FIXED | + ROUTED}
             layerName routeWidth
                  [+ SHAPE
                       {RING | PADRING | BLOCKRING | STRIPE | FOLLOWPIN
                       | IOWIRE | COREWIRE | BLOCKWIRE | BLOCKAGEWIRE | FILLWIRE
                       | FILLWIREOPC | DRCFILL}]
                   routingPoints
             [NEW layerName routeWidth
                  [+ SHAPE
                       {RING | PADRING | BLOCKRING | STRIPE | FOLLOWPIN
                       | IOWIRE | COREWIRE | BLOCKWIRE | BLOCKAGEWIRE | FILLWIRE
                       | FILLWIREOPC | DRCFILL}]
                   routingPoints
                ]...
      ]...
      [+ SOURCE {DIST | NETLIST | TIMING | USER}]
      [+ FIXEDBUMP]
      [+ USE {ANALOG | CLOCK | GROUND | POWER | RESET | SCAN | SIGNAL | TIEOFF}]
      [+ WEIGHT weight]
      [+ PROPERTY {propName propVal} ...] ...
    ;] ...

END SPECIALNETS

[TRACKS
    [{X | Y} start DO numtracks STEP space
      [MASK maskNum [SAMEMASK]]
      [LAYER layerName ...]
    ;] ...]

UNITS DISTANCE MICRONS dbuPerMicron ;

VERSION 5.8 ;

VIAS numVias ;
    [- viaName
       [   + VIARULE viaRuleName
              + CUTSIZE xSize ySize
              + LAYERS botmetalLayer cutLayer topMetalLayer
              + CUTSPACING xCutSpacing yCutSpacing
              + ENCLOSURE xBotEnc yBotEnc xTopEnc yTopEnc
              [+ ROWCOL numCutRows NumCutCols]
              [+ ORIGIN xOffset yOffset]
              [+ OFFSET xBotOffset yBotOffset xTopOffset yTopOffset]
              [+ PATTERN cutPattern] ]
       | [ + RECT layerName pt pt] ...]
    ;] ...

END VIAS

The routing points are defined as follows:

{ ( x y [extValue] )
    {[MASK maskNum] ( x y [extValue] )
    |[MASK viaMaskNum] viaName [orient]
    |[MASK maskNum] RECT ( deltax1 deltay1 deltax2 deltay2 )
    } } ...

All points are in the form of ( x y ) where x and y are integers.

The orientation of components can be one of N, S, W, E, FN, FS, FW, or FE.

ROW statements can be either horizontal, in which case numY is 1 and stepY is 0,
or vertical, in which case numX is 1 and stepX is 0.

In a row statement, if STEP is present, then both stepX and stepY must be present.

TRACKS is a statement, not a section.

Some sections do not have a semicolon at the end of each statement in the list.

You cannot include mathematic operations in the DEF file.

CRITICAL REQUIREMENT: RESPECT EXACTLY THE PROVIDED SYNTAX. DO NOT ADD ANYTHING ELSE.
DO NOT ADD SEMICOLONS WHERE SEMICOLONS ARE NOT INDICATED IN THE SYNTAX.
DO NOT ADD PARENTHESIS WHERE PARENTHESIS ARE NOT INDICATED IN THE SYNTAX.
You can add comments to the DEF file, but they are not required.
"""


_TARGET_SYSTEM_PROMPT = """The goal is to create diverse patterns in the design,
each targeting as many lines as possible in the file '{target_file}'.

The content of the target C++ file `{target_file}` is:
```cpp
{target_content}
```

The coverage of this file is:

`{coverage_excerpt}`.

The overall goal is to maximise the coverage of the cpp file."""


_INITIAL_PROMPT = """FIRST identify all the different features this file is supposed to handle or simulate.
THEN once you identified all the features, that are specific to this file, then generate a single DEF file.
This file should target as many lines as possible from the OpenROAD C++ file '{target_file}'.
Analyze the C++ code to understand the constructs it handles.
Generate a complex but valid DEF design snippets using these constructs, maximising the coverage of the C++ file.
The objective is MAXIMIZING the coverage of the C++ file.

Generate only the design file for this single C++ file based on the given platform."""

# Feedback Prompt - Updated to reinforce snippet requirements
_FEEDBACK_PROMPT = """The following DEF design was generated to maximise coverage of the OpenROAD C++ file '{target_file}', but it was rejected by OpenROAD.
The goal was to generate a complex design, valid, targeting as many features of this file as possible.

Faulty generated design:
```def
{generated_code}
```

OpenROAD Error Output (Stderr focused):
```text
{error_summary}
```

Please analyze the faulty DEF design, and the errors.
Provide a corrected version of the design that fixes the error(s) while adhering strictly to ALL the requirements:
1.  Each part of the design targets a specific construct relevant to the C++ file, try not to simplify too much the design.
2.  Maximize the coverage of the C++ file.
3.  No comments
Generate only the corrected DEF design."""


def format_technology_prompt(lef_files: list["Path"]) -> str:
    """Format the technology system prompt with the provided LEF files.

    Args:
        lef_files (list[Path]): List of LEF files for the technology platform.

    Returns:
        str: The formatted technology system prompt.
    """
    lef = "\n\n".join(f"File: {file.name}\nContent:\n```lef\n{file.read_text()}\n```" for file in lef_files)

    return _TECHNOLOGY_SYSTEM_PROMPT.format(lef_files=lef)


def get_system_prompts(target_file: str, target_content: str, coverage: str, library_files: list["Path"]) -> list[str]:
    """Generate the system prompts.

    Args:
        target_file (str): The target file name.
        target_content (str): The content of the target file.
        coverage (str): The coverage excerpt for the target file.
        library_files (list[Path]): List of library files to be included.

    Returns:
        list[str]: A list of system prompts.
    """
    technology_prompt = format_technology_prompt(lef_files=library_files)
    target_prompt = _TARGET_SYSTEM_PROMPT.format(
        target_file=target_file, target_content=target_content, coverage_excerpt=coverage
    )

    return [technology_prompt, _DEF_SYNTAX_PROMPT, target_prompt]


def get_initial_prompt(target_file: str, target_content: str, coverage: str, library_files: list["Path"]) -> str:
    """Generate the initial prompt.

    Args:
        target_file (str): The target file name.
        target_content (str): The content of the target file.
        coverage (str): The coverage excerpt for the target file.
        library_files (list[Path]): List of library files to be included.

    Returns:
        str: The initial prompt.
    """
    return _INITIAL_PROMPT.format(target_file=target_file)


def get_feedback_prompt(  # noqa: PLR0913, PLR0917
    target_file: str,
    target_content: str,
    coverage: str,
    library_files: list["Path"],
    generated_code: str,
    error_summary: str,
) -> str:
    """Generate the feedback prompt.

    Args:
        target_file (str): The target file name.
        target_content (str): The content of the target file.
        coverage (str): The coverage excerpt for the target file.
        library_files (list[Path]): List of library files to be included.
        generated_code (str): The generated code that was rejected.
        error_summary (str): The summary of errors.

    Returns:
        str: The feedback prompt to be given to the LLM..
    """
    return _FEEDBACK_PROMPT.format(target_file=target_file, generated_code=generated_code, error_summary=error_summary)


__all__ = ["get_feedback_prompt", "get_initial_prompt", "get_system_prompts"]
