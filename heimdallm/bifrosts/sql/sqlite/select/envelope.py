import re
from itertools import chain
from pathlib import Path
from typing import Sequence, cast

import jinja2

from heimdallm.envelope import PromptEnvelope as _PromptEnvelope
from heimdallm.llm import LLMIntegration

from .validator import SQLConstraintValidator

THIS_DIR = Path(__file__).parent
_TMPL_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(THIS_DIR / "envelopes"),
    undefined=jinja2.StrictUndefined,
)


class SQLPromptEnvelope(_PromptEnvelope):
    def __init__(
        self,
        *,
        llm: LLMIntegration,
        db_schema: str,
        validators: Sequence[SQLConstraintValidator],
    ):
        self.db_schema = db_schema
        self.validators = validators
        super().__init__(llm=llm)

    def template(self, env: jinja2.Environment) -> jinja2.Template:
        return env.get_template("base.j2")

    @property
    def params(self) -> dict:
        return {}

    def wrap(self, untrusted_input: str) -> str:
        """Performs the wrapping of the untrusted input with the envelope. Not
        intended to be overridden, but not foribben either. Consider overriding the
        :meth:`envelope` and :meth:`params` properties instead."""
        all_idents = chain.from_iterable(
            v.requester_identities() for v in self.validators
        )
        id_constraints = " or ".join(str(ident) for ident in all_idents)
        params = {
            "id_constraints": id_constraints,
            "db_schema": self.db_schema,
            "query": untrusted_input,
        }
        params.update(self.params)

        tmpl = self.template(_TMPL_ENV)
        prompt = tmpl.render(params)
        return prompt

    def unwrap(self, untrusted_llm_output: str) -> str:
        # assume the LLM did what we said and delimited the output with ```
        if "```" in untrusted_llm_output:
            # sometimes the LLM is silly and likes to include the word "sql" inside
            # the delimiters. silly LLM!
            match = cast(
                re.Match,
                re.search(
                    r"```(?:sql)?(.*)```",
                    untrusted_llm_output,
                    flags=re.DOTALL | re.IGNORECASE,
                ),
            )
            unpacked = match.group(1)
        # otherwise, just return the whole thing, and we'll attempt to parse it
        # as is
        else:
            # for some reason, the LLM is returning "sql\n" as a prefix, even
            # when instructed not to, oh well.
            unpacked = re.sub(r"^\s*sql\n+", "", untrusted_llm_output)

        unpacked = unpacked.strip()
        return unpacked


class TestSQLPromptEnvelope(SQLPromptEnvelope):
    def wrap(self, untrusted_input: str) -> str:
        # build the envelope, but don't actually use it. this exercises the
        # envelope code as part of a full integration
        super().wrap(untrusted_input)
        return untrusted_input
