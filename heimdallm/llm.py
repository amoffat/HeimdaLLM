from abc import ABC, abstractmethod


class LLMIntegration(ABC):
    @abstractmethod
    def complete(self, untrusted_user_input: str) -> str:
        pass
