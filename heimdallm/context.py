class TraverseContext:
    """Captures the context of a Bifrost traversal. For example, this will store the
    user's untrusted input, the LLM's untrusted output, the trusted output, etc, at
    different stages. This is used for logging and exceptions."""

    def __init__(self) -> None:
        # the input as submitted by the user
        self.untrusted_human_input: str | None = None
        # the output as returned by the LLM
        self.untrusted_llm_output: str | None = None
        # the output from the LLM, validated
        self.trusted_llm_output: str | None = None
