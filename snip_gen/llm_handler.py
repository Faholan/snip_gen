"""Handle interactions with LLMs using LiteLLM."""

import logging
import typing as t
from time import sleep

from snip_gen import BASE_WAIT, CODEBLOCK_STRIPPED_PREFIX, EXPONENTIAL_FACTOR, LITELLM_MODELS, MAX_ATTEMPTS

if t.TYPE_CHECKING:
    import litellm

    from snip_gen import MODEL_HINT
else:
    litellm = None


# Avoid the HTTP request that litellm does on import.
def _ensure_litellm() -> None:
    """Delay import of litellm until needed."""
    global litellm  # noqa: PLW0603

    if litellm is None:
        import litellm as _litellm  # noqa: PLC0415

        litellm = _litellm


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

Prompts = list[dict[str, str | dict[str, str]]]


class LLMHandler:
    """Handle interaction with different language models using LiteLLM.

    Attributes:
        model_name (str): The name of the model to use with LiteLLM.
    """

    def __init__(self, model_type: "MODEL_HINT") -> None:
        """Initialize the LLMHandler with the specified model type.

        Args:
            model_type (str): The type of language model provider.
                This will be used to determine the model string for LiteLLM.

        Raises:
            ValueError:  If the provided model type is unsupported.
        """
        model_name = LITELLM_MODELS.get(model_type)
        if model_name is None:
            msg = f"Unsupported model type: {model_type}"
            raise ValueError(msg)

        self.model_name = model_name

        logger.info(f"Using model via LiteLLM: {self.model_name}")

    def completion(self, messages: Prompts) -> str | None:
        """Invoke the language model via LiteLLM with the given messages.

        Retries on rate-limit errors with exponential backoff.

        Args:
            messages: List of message dictionaries containing role and content.

        Returns:
            str | None: The response from the language model.
        """
        for attempt in range(MAX_ATTEMPTS):
            logger.debug(f"Attempt {attempt + 1} to invoke LLM ({self.model_name}) via LiteLLM...")
            try:
                response = litellm.completion(model=self.model_name, messages=messages)
            except litellm.exceptions.RateLimitError:
                logger.warning(f"Rate limit error on attempt {attempt + 1}")

                delay = BASE_WAIT * (EXPONENTIAL_FACTOR**attempt)

                logger.warning(f"Waiting {delay} seconds before retrying...")

                sleep(delay)
            except litellm.exceptions.NotFoundError:
                logger.exception(f"No model found for {self.model_name}")
                raise
            else:
                if response.choices and response.choices[0].message:
                    content = response.choices[0].message.content
                    if isinstance(content, str):
                        return content

                raw_answer = getattr(response, "text", str(response))
                logger.warning(f"Raw response:\n\n{raw_answer}\n\n")
                return None

        logger.warning("Exceeded maximum attempts to invoke LLM.")
        return None

    def invoke_llm(self, prompt: str, *system_prompts: str) -> str:
        """Invoke the language model via LiteLLM with the given prompt.

        Args:
            prompt (str): The main user prompt for the LLM.
            *system_prompts (str): Optional system messages to guide the LLM’s behavior.

        Returns:
            str: The content of the LLM’s response as a string.
        """
        _ensure_litellm()

        messages: Prompts = [
            {"role": "system", "content": system_prompt, "cache_control": {"type": "ephemeral"}}
            for system_prompt in system_prompts
        ]

        messages.append({"role": "user", "content": prompt})

        logger.info(f"Invoking LLM ({self.model_name}) via LiteLLM...")

        content = self.completion(messages)
        logger.info("LLM invocation complete.")

        if content:
            content = content.strip()

            for prefix in CODEBLOCK_STRIPPED_PREFIX:
                if content.startswith(prefix):
                    content = content[len(prefix) :].strip()
                    break

            if content.endswith("```"):
                content = content[:-3].strip()
            return content

        logger.warning("LLM response did not contain expected content.")
        return ""
