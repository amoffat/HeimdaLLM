class TraverseContext:
    """Captures the context of a Bifrost traversal. For example, this will store the
    user's untrusted input, the LLM's untrusted output, the trusted output, etc, at
    different stages. This is used for logging and exceptions."""

    def __init__(self) -> None:
        self.untrusted_human_input: str | None = None
        self.untrusted_llm_output: str | None = None
        self.trusted_llm_output: str | None = None
