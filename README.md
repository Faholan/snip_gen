# snip_gen

Generate code snippets to maximize code coverage thanks to the power of LLMs

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

```bash
poetry install
```

## Usage

This utility is composed of three commands:

- `snippet`: Generate a snippet of code to exercise a specific target file.
- `coverage`: Analyze coverage data.
- `seed`: The main command, leverage coverage data to select the files to generate
  snippets for.

## Customization

### Target language

This module is configured to generate Design Exchange Format (DEF) files,
but can easily be customized to target any format.

This can be achieved by editing the `snip_gen/prompts.py` file,
and changing the implementation of the three functions it contains:

- `get_system_prompts`, which generates the system prompts for the LLM.
- `get_initial_prompt`, which generates the initial prompt for the LLM.
- `get_feedback_prompt`, which generates the feedback prompt for the LLM when verification fails.

The verification process should also be adapted to the target language.
It is implemented in the `verify_code` function in `snip_gen/verify_code.py`.

You might also want to change the `DEFAULT_FILE_EXTENSION` and `CODEBLOCK_STRIPPED_PREFIX`
constants in `snip_gen/__init__.py` to match the target language.

### Target LLM models

Any LLM model suported by [LiteLLM](https://docs.litellm.ai/) can be used with this utility.

To do so, you simply need to change the `MODELHINT` and `LITELLM_MODELS`
constants in `snip_gen/__init__.py`.

## Special thanks

Special thanks to [@toby-bro](https://github.com/toby-bro),
whose [pfuzz](https://github.com/toby-bro/pfuzz) was a big inspiration for this project.
