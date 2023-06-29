from abc import ABC, abstractmethod

from heimdallm.llm import LLMIntegration


class PromptEnvelope(ABC):
    """
    the purpose of the prompt envelope is to guide the wrapped untrusted query
    to produce the structured output. it is impossible to prevent prompt
    injection, so accept that up front. however, a malicious prompt will not
    produce a valid query, so our grammar will not parse it, and the user will
    not see the result of their malicious query, so everything is fine.
    """

    def __init__(self, *, llm: LLMIntegration):
        """record the LLM integration so that we can use it to wrap and unwrap,
        because different LLMs have different tendencies in what they produce."""
        self.llm = llm

    @abstractmethod
    def wrap(self, untrusted_input: str) -> str:
        pass

    @abstractmethod
    def unwrap(self, untrusted_input: str) -> str:
        pass


class NoOpEnvelope(PromptEnvelope):
    def wrap(self, untrusted_input: str) -> str:
        return untrusted_input

    def unwrap(self, untrusted_llm_output: str) -> str:
        return untrusted_llm_output
