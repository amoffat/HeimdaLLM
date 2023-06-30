from typing import Any, Callable, Sequence

import structlog
from lark import Lark, ParseTree

from heimdallm.constraints import ConstraintValidator
from heimdallm.envelope import PromptEnvelope
from heimdallm.llm import LLMIntegration

LOG = structlog.get_logger(__name__)


class Bifrost:
    """The Bifrost is the bridge from the outside world to your secure systems. It is
    responsible for a rigorous parsing and validation of the output of the LLM. This
    class is not used directly, but is subclassed to provide a Bifrost for a specific
    problem, like constructing trusted SQL queries. It is general enough to be adapted
    to other problems.

    :param llm: The LLM integration to use.
    :param prompt_envelope: The prompt envelope used to wrap the untrusted human input
        and unwrap the untrusted LLM output.
    :param grammar: The grammar that defines the structured output that we expect from
        the LLM.
    :param tree_producer: A callable that takes a grammar and the untrusted input and
        returns a parse tree. Using a callback allows us to do Bifrost-specific parsing,
        for example, to collapse ambiguous parse trees into a single parse tree.
    :param constraint_validators: A sequence of constraint validators that will be used
        to validate the parse tree returned by the ``tree_producer``. Only one validator
        needs to succeed for validation to pass.
    """

    def __init__(
        self,
        *,
        llm: LLMIntegration,
        prompt_envelope: PromptEnvelope,
        grammar: Lark,
        tree_producer: Callable[[Lark, str], ParseTree],
        constraint_validators: Sequence[ConstraintValidator],
    ):
        self.llm = llm
        self.prompt_envelope = prompt_envelope
        self.grammar = grammar
        self.tree_producer = tree_producer
        self.constraint_validators = constraint_validators

    def traverse(
        self,
        untrusted_human_input: str,
        autofix: bool = True,
    ) -> Any:
        """Run the full chain of the bifrost, from untrusted input to trusted
        input.

        :param untrusted_human_input: The untrusted input from the user.
        :param autofix: Whether or not to attempt to reconstruct the input to satisfy
            the constraint validator.

        :return: The LLM output that has passed the constraint validator.
        """

        log = LOG.bind(input=untrusted_human_input, autofix=autofix)
        log.info("Traversing untrusted input")

        # wrap the untrusted input in our prompt
        log.info("Wrapping input in prompt envelope")
        untrusted_llm_input = self.prompt_envelope.wrap(untrusted_human_input)
        log.debug("Produced prompt envelope")

        # talk to our LLM
        log.info("Sending envelope to LLM")
        untrusted_llm_output: str = self.llm.complete(untrusted_llm_input)
        log = log.bind(llm_output=untrusted_llm_output)
        log.info("Received raw result from LLM")

        # trim any cruft off of the LLM output
        log.info("Unwrapping prompt envelope")
        try:
            untrusted_llm_output = self.prompt_envelope.unwrap(untrusted_llm_output)
        except Exception as e:
            log.exception("Unwrap failed")
            raise e
        log = log.bind(unwrapped=untrusted_llm_output)
        log.info("Unwrap succeeded")

        # throws a parse error
        log.info("Parsing result via grammar")
        try:
            tree = self.parse(untrusted_llm_output)
        except Exception as e:
            log.exception("Parse failed")
            raise e
        log.info("Parse succeeded")

        # try each of our constraint validators until one succeeds
        validation_exc = None
        for validator in self.constraint_validators:
            log.info(
                "Trying constraint validator",
                validator=validator.__class__.__name__,
            )
            try:
                trusted_llm_output = self._try_validator(
                    log,
                    validator,
                    autofix,
                    untrusted_llm_output,
                    tree,
                )
            except Exception as e:
                validation_exc = e
            # the first validator to validate the input wins
            else:
                validation_exc = None
                break

        if validation_exc:
            # ugly, but this is the easiest way to log the exception that we have
            # already caught
            try:
                raise validation_exc
            except Exception as e:
                log.exception("Validation failed")
                raise e

        log = log.bind(trusted=untrusted_llm_output)
        log.info("Validation succeeded")

        return trusted_llm_output

    def _try_validator(
        self,
        log: structlog.BoundLogger,
        validator: ConstraintValidator,
        autofix: bool,
        untrusted_llm_input: str,
        tree: ParseTree,
    ) -> str:
        """Attempt validation with an individual constraint validator."""

        if autofix:
            log.info("Autofixing parse tree and reconstructing the input")
            try:
                untrusted_llm_output = validator.fix(self.grammar, tree)
            except Exception as e:
                log.exception("Autofix failed")
                raise e
            log.info("Re-parsing reconstructed output")
            try:
                tree = self.parse(untrusted_llm_output)
            except Exception as e:
                log.exception("Reparse failed")
                raise e
            log.info("Reconstruction succeeded")

        # throws a bifrost-specific exception
        log.info("Validating parse tree")
        validator.validate(untrusted_llm_input, tree)
        log.info("Validation succeeded")

        return untrusted_llm_output

    def parse(self, untrusted_llm_output: str) -> ParseTree:
        """Converts the llm output into a parse tree. Override it in a subclass
        to throw custom exceptions based on the grammar and parse state.

        :param untrusted_llm_output: The unwrapped output from the LLM.

        :return: The Lark parse tree.
        """
        return self.tree_producer(self.grammar, untrusted_llm_output)
