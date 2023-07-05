from abc import ABC, abstractmethod


class LLMIntegration(ABC):
    """This captures the integration of an LLM provider. It is designed to be
    subclassed and implemented for a specific LLM provider. It has one method, complete,
    which takes some untrusted input and returns the LLM's output, unfiltered."""

    @abstractmethod
    def complete(self, untrusted_input: str) -> str:
        """Send the untrusted input to the LLM and return the LLM's output.

        :param untrusted_input: The untrusted input from the user, but almost always
            wrapped in a :class:`PromptEnvelope <heimdallm.envelope.PromptEnvelope>`.
        :return: The untrusted output from the LLM.
        """
        raise NotImplementedError
