import sqlite3
from pathlib import Path
from typing import Callable, Sequence, Union

import lark
from lark import Lark, ParseTree
from lark.exceptions import VisitError

from heimdallm.bifrost import Bifrost as _Bifrost
from heimdallm.bifrosts.sql import exc
from heimdallm.envelope import PromptEnvelope as _PromptEnvelope
from heimdallm.llm import LLMIntegration
from heimdallm.llm_providers.mock import EchoMockLLM

from .envelope import TestSQLPromptEnvelope
from .validator import SQLConstraintValidator
from .visitors import AmbiguityResolver

_THIS_DIR = Path(__file__).parent
_GRAMMAR_PATH = _THIS_DIR / "sqlite.lark"


def _build_grammar() -> Lark:
    """
    returns a limited sqlite SELECT grammar

    noteworthy:
        - no outer joins
        - no subqueries

    theoretically, subqueries could be allowed, but it would be more work, and
    i'm not yet convinced that an LLM produces subqueries often enough to make
    it worth it.

    outer joins are unsafe because the join constraint is not applied to the
    rows that would be considered "outer."
    """
    with open(_GRAMMAR_PATH, "r") as h:
        grammar = Lark(
            ambiguity="explicit",
            maybe_placeholders=False,
            grammar=h,
        )
    return grammar


def _build_tree_producer() -> Callable[[Lark, str], ParseTree]:
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


def get_schema(conn: sqlite3.Connection):
    """a convenience function to get the schema of a sqlite database. you
    probably want to write your own function to do this, one that doesn't
    include tables and columns that you care about sending to the LLM"""
    schema = []
    for line in conn.iterdump():
        if "CREATE TABLE" in line:
            schema.append(line)
    return "\n".join(schema)


class SQLBifrost(_Bifrost):
    """A Bifrost for traversing SQL ``SELECT`` queries."""

    # for tests
    @classmethod
    def mocked(
        cls,
        constraint_validators: Union[
            SQLConstraintValidator, Sequence[SQLConstraintValidator]
        ],
    ):
        """A convenience method for our tests. This creates a Bifrost that assumes its
        untrusted input is a SQL query already, so it does not need to communicate with
        the LLM, only parse and validate it.

        :param constraint_validators: A constraint validator or sequence of constraint
            validators to run on the untrusted input.
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
        prompt_envelope: _PromptEnvelope,
        constraint_validators: Sequence[SQLConstraintValidator],
    ):
        super().__init__(
            llm=llm,
            prompt_envelope=prompt_envelope,
            grammar=_build_grammar(),
            tree_producer=_build_tree_producer(),
            constraint_validators=constraint_validators,
        )

    def parse(self, untrusted_llm_output: str) -> ParseTree:
        """Parse the unwrapped SQL query from the LLM's output. Raise a SQL-specific
        exception if the query is not valid.

        :param untrusted_llm_output: The output from the LLM, which should be a SQL
            query. If it isn't, then our :meth:`SQLPromptEnvelope.unwrap` method failed.
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
