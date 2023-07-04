from enum import Enum
from typing import Callable

import openai

from heimdallm import llm


class OpenAIMethod(Enum):
    """How the OpenAI API should complete the prompt. OpenAI provides two main methods
    of completion, both appear to be similar in quality. TODO document the differences.
    """

    CHAT = "chat"
    COMPLETION = "completion"


class Client(llm.LLMIntegration):
    """The LLM integration with OpenAI's ChatGPT and Completion API.

    :param api_key: Your secret OpenAI API key.
    :param model: The model to use. Prefer a higher model with a high context window, as
        the prompt envelopes can make the LLM input quite long.
    :param method: The method to use to interact with the OpenAI API. I don't really
        know the difference in terms of quality, but the chat method has worked fine so
        far."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gpt-3.5-turbo-16k",
        method: OpenAIMethod = OpenAIMethod.CHAT,
    ):
        self.api_key = api_key
        self.model = model
        self.method = method

    def complete(self, untrusted_user_input: str) -> str:
        """Complete the untrusted user input and return some structured output.

        :param untrusted_user_input: The untrusted user input.
        :return: The structured output."""
        fn_map: dict[OpenAIMethod, Callable[[str], str]] = {
            OpenAIMethod.CHAT: self._complete_via_chatgpt,
            OpenAIMethod.COMPLETION: self._complete_via_completion,
        }
        fn = fn_map[self.method]
        return fn(untrusted_user_input)

    def _complete_via_chatgpt(self, untrusted_user_input: str) -> str:
        chat_completion = openai.ChatCompletion.create(
            api_key=self.api_key,
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": untrusted_user_input,
                }
            ],
        )
        untrusted_llm_output = chat_completion.choices[0].message.content
        return untrusted_llm_output

    def _complete_via_completion(self, prompt):
        response = openai.Completion.create(
            engine=self.model,
            prompt=prompt,
            max_tokens=256,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
