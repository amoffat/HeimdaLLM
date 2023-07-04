import hashlib
from typing import Dict

from ..llm import LLMIntegration


class LookupMockLLM(LLMIntegration):  # pragma: no cover
    """a mock LLM integration that simply returns a canned response for the
    hash of some input"""

    def __init__(self) -> None:
        self.responses: Dict[str, str] = {}

    def complete(self, untrusted_user_input: str) -> str:
        hash_id = hashlib.md5(untrusted_user_input.encode("utf8")).hexdigest()
        return self.responses[hash_id]


class EchoMockLLM(LLMIntegration):  # pragma: no cover
    """a mock LLM integration that simply returns the provided response. useful
    in our tests where we know the query that we want to attempt to parse +
    validate."""

    def complete(self, sql_output: str) -> str:
        return sql_output
