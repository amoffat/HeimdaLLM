from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Sequence, Union

import lark
from lark import Lark, ParseTree
from lark.exceptions import VisitError

from heimdallm.bifrost import Bifrost as _BaseBifrost
from heimdallm.bifrosts.sql import exc
from heimdallm.llm import LLMIntegration
from heimdallm.llm_providers.mock import EchoMockLLM

if TYPE_CHECKING:
    import heimdallm.bifrosts.sql.envelope
    import heimdallm.bifrosts.sql.validator

from .envelope import TestSQLPromptEnvelope
from .visitors.ambiguity import AmbiguityResolver


class Bifrost(_BaseBifrost, ABC):
    """
    An abstract Bifrost for traversing SQL ``SELECT`` queries. This is used by the
    different SQL dialects.

    :param llm: The LLM integration to use.
    :param prompt_envelope: The prompt envelope used to wrap the untrusted human input
        and unwrap the untrusted LLM output.
    :param constraint_validators: A sequence of constraint validators that will be used
        to validate the parse tree returned by the ``tree_producer``. Only one validator
        needs to succeed for validation to pass.
    """

    # for tests
    @classmethod
    def mocked(
        cls,
        constraint_validators: Union[
            "heimdallm.bifrosts.sql.validator.ConstraintValidator",
            Sequence["heimdallm.bifrosts.sql.validator.ConstraintValidator"],
        ],
    ):
        """A convenience method for our tests. This creates a Bifrost that assumes its
        untrusted input is a SQL query already, so it does not need to communicate with
        the LLM, only parse and validate it.

        :param constraint_validators: A constraint validator or sequence of constraint
            validators to run on the untrusted input.

        :meta private:
        """
        if not isinstance(constraint_validators, Sequence):
            constraint_validators = [constraint_validators]

        llm = EchoMockLLM()
        return cls(
            llm=llm,
            constraint_validators=constraint_validators,
            prompt_envelope=TestSQLPromptEnvelope(
                llm=llm,
                db_schema="<schema>",  # doesn't matter
                validators=constraint_validators,
            ),
        )

    def __init__(
        self,
        *,
        llm: LLMIntegration,
        prompt_envelope: "heimdallm.bifrosts.sql.envelope.PromptEnvelope",
        constraint_validators: Sequence[
            "heimdallm.bifrosts.sql.validator.ConstraintValidator"
        ],
    ):
        super().__init__(
            llm=llm,
            prompt_envelope=prompt_envelope,
            grammar=self.build_grammar(),
            tree_producer=self.build_tree_producer(),
            constraint_validators=constraint_validators,
        )

    @classmethod
    @abstractmethod
    def reserved_keywords(cls) -> set[str]:
        """
        Returns the reserved keywords for the SQL dialect. Must be implemented in the
        subclass.

        :return: The reserved keywords.
        :meta private:
        """
        raise NotImplementedError

    @classmethod
    def build_tree_producer(cls) -> Callable[[Lark, str], ParseTree]:
        """
        Produces a that can create a single parse tree. May be implemented in a subclass
        if you want to do custom ambiguity resolution.

        :return: The parse tree producer.
        :meta private:
        """

        def parse(grammar: Lark, untrusted_query: str) -> ParseTree:
            ambig_tree = grammar.parse(untrusted_query)
            try:
                final_tree = AmbiguityResolver(
                    untrusted_query,
                    cls.reserved_keywords(),
                ).transform(ambig_tree)
            except VisitError as e:
                if isinstance(e.orig_exc, exc.BaseException):
                    raise e.orig_exc
                raise e
            return final_tree

        return parse

    @staticmethod
    @abstractmethod
    def build_grammar() -> Lark:
        """
        Produces the grammar that will be used to parse the dialect of SQL. Must be
        implemented in a subclass.

        :return: The Lark grammar for the SQL dialect.
        :meta private:
        """
        raise NotImplementedError

    def parse(self, untrusted_llm_output: str) -> ParseTree:
        """Parse the unwrapped SQL query from the LLM's output. Raise a SQL-specific
        exception if the query is not valid.

        :param untrusted_llm_output: The output from the LLM, which should be a SQL
            query. If it isn't, then our
            :meth:`heimdallm.bifrosts.sql.envelope.PromptEnvelope.unwrap` method failed.
        :raises InvalidQuery: If the query is not valid.
        :return: The Lark parse tree for the query.

        :meta private:
        """
        try:
            return super().parse(untrusted_llm_output)
        except lark.exceptions.UnexpectedEOF as e:
            raise exc.InvalidQuery(query=untrusted_llm_output) from e
        except lark.exceptions.UnexpectedCharacters as e:
            raise exc.InvalidQuery(query=untrusted_llm_output) from e
        except exc.BaseException as e:
            raise e
        except Exception as e:
            raise exc.InvalidQuery(query=untrusted_llm_output) from e
