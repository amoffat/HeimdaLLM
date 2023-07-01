from abc import ABC, abstractmethod

from heimdallm.llm import LLMIntegration


class PromptEnvelope(ABC):
    """
    The purpose of the prompt envelope is to guide the wrapped untrusted query to
    produce the structured output. Itt is impossible to prevent prompt injection, so
    accept that up front. However, a malicious prompt will not produce a valid response,
    so our grammar will not parse it, and the validator will not validate it, so the
    malicious user will never see the result of their malicious output.

    :param llm: The LLM integration being sent the human input. This is passed in so
        that the envelope can change the way it wraps or unwraps data communicated with
        the LLM, based on different quirks of the LLM.
    """

    def __init__(self, *, llm: LLMIntegration):
        self.llm = llm

    @abstractmethod
    def wrap(self, untrusted_input: str) -> str:
        """Wrap the untrusted input with additional context to guide the LLM to produce
        the correct output.

        :param untrusted_input: The untrusted input from the user.
        :return: The wrapped input to send to the LLM."""
        return untrusted_input

    @abstractmethod
    def unwrap(self, untrusted_llm_output: str) -> str:
        """Unwrap the LLM's output to produce the original untrusted input. This method
        should work closely with the wrap method to coordinate how to delimit the
        structured response.

        :param untrusted_llm_output: The untrusted output from the LLM.
        :return: The structured response, unwrapped from the LLM's output."""
        return untrusted_llm_output


class NoOpEnvelope(PromptEnvelope):
    def wrap(self, untrusted_input: str) -> str:
        return untrusted_input

    def unwrap(self, untrusted_llm_output: str) -> str:
        return untrusted_llm_output
