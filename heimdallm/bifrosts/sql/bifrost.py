from abc import ABC, abstractmethod
from typing import Callable, Sequence, Union

import lark
from lark import Lark, ParseTree
from lark.exceptions import VisitError

from heimdallm.bifrost import Bifrost as _BaseBifrost
from heimdallm.bifrosts.sql import exc
from heimdallm.llm import LLMIntegration
from heimdallm.llm_providers.mock import EchoMockLLM

from .envelope import PromptEnvelope, TestSQLPromptEnvelope
from .validator import ConstraintValidator
from .visitors import AmbiguityResolver


class Bifrost(_BaseBifrost, ABC):
    """A Bifrost for traversing SQL ``SELECT`` queries.

    :vartype value: str
    """

    # for tests
    @classmethod
    def mocked(
        cls,
        constraint_validators: Union[
            ConstraintValidator,
            Sequence[ConstraintValidator],
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
        prompt_envelope: PromptEnvelope,
        constraint_validators: Sequence[ConstraintValidator],
    ):
        super().__init__(
            llm=llm,
            prompt_envelope=prompt_envelope,
            grammar=self.build_grammar(),
            tree_producer=self.build_tree_producer(),
            constraint_validators=constraint_validators,
        )

    @staticmethod
    def build_tree_producer() -> Callable[[Lark, str], ParseTree]:
        """
        Produces a that can create a single parse tree. May be implemented in a subclass
        if you want to do custom ambiguity resolution.

        :return: The parse tree producer.
        """

        def parse(grammar: Lark, untrusted_query: str) -> ParseTree:
            ambig_tree = grammar.parse(untrusted_query)
            try:
                final_tree = AmbiguityResolver(untrusted_query).transform(ambig_tree)
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
            query. If it isn't, then our :meth:`SQLPromptEnvelope.unwrap` method failed.
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
