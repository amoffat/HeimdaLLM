import re
from abc import abstractmethod
from itertools import chain
from pathlib import Path
from typing import Sequence, cast

import jinja2

from heimdallm.envelope import PromptEnvelope as _BasePromptEnvelope
from heimdallm.llm import LLMIntegration

from .validator import ConstraintValidator

THIS_DIR = Path(__file__).parent
_TMPL_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(THIS_DIR / "envelopes"),
    undefined=jinja2.StrictUndefined,
)


class PromptEnvelope(_BasePromptEnvelope):
    """The purpose of the prompt envelope is to wrap the untrusted input in additional
    context for the LLM to produce the correct output. We do not do validation in the
    envelope, because it is impossible to prevent prompt injection.

    While not necessary to subclass, you are recommended to do so if you want to
    customize the envelope.

    :param llm: The LLM integration being sent the human input. This can be used to
        tweak the :meth:`wrap` and :meth`unwrap` methods to account for quirks of the
        specific LLM.
    :param db_schema: The database schema of the database being queried. It is passed to
        the LLM so that the LLM knows how the tables and columns are connected.
    :param validators: The validators to use to validate the output of the LLM. They
        aren't used to validate here, but some of the validator's properties are added
        to the envelope to help guide the LLM to produce the correct output.
    """

    def __init__(
        self,
        *,
        llm: LLMIntegration,
        db_schema: str,
        validators: Sequence[ConstraintValidator],
    ):
        self.db_schema = db_schema
        self.validators = validators
        super().__init__(llm=llm)

    @abstractmethod
    def template(self, env: jinja2.Environment) -> jinja2.Template:
        """
        Returns the template to use for the envelope. Override in a subclass for
        complete customization.

        :param env: The environment to use to load the template.
        :return: The template to use for the envelope.
        """
        raise NotImplementedError

    @property
    def params(self) -> dict:
        """Returns a dictionary of additional parameters to be passed to the template.
        Override in a subclass for complete control over values that you want in the
        envelope.

        :return: The extra parameters to pass to the template."""
        return {}

    def wrap(self, untrusted_input: str) -> str:
        """Performs the wrapping of the untrusted input with the envelope. Not
        intended to be overridden, but not foribben either. Consider overriding the
        :meth:`template` and :meth:`params` properties first instead.

        :param untrusted_input: The untrusted input from the user.
        :return: The wrapped input to send to the LLM."""
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
        """Unpack the SQL query from the LLM output by finding it (hopefully) among the
        delimiters.

        :param untrusted_llm_output: The output from the LLM.
        :return: The SQL query."""
        # assume the LLM did what we said and delimited the output with ```
        if "```" in untrusted_llm_output:
            # sometimes the LLM is silly and likes to include the word "sql" inside
            # the delimiters. silly LLM!
            match = cast(
                re.Match,
                re.search(
                    r"```(?:sql)?(.*?)```",
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


class TestSQLPromptEnvelope(PromptEnvelope):
    """
    A test envelope specifically for :meth:`SQLBifrost.mocked
    <heimdallm.bifrosts.sql.SQLBifrost.mocked>`
    """

    def wrap(self, untrusted_input: str) -> str:
        # build the envelope, but don't actually use it. this exercises the
        # envelope code as part of a full integration
        super().wrap(untrusted_input)
        return untrusted_input

    def template(self, env: jinja2.Environment) -> jinja2.Template:
        """
        Returns the template to use for the envelope. Override in a subclass for
        complete customization.

        :param env: The environment to use to load the template.
        :return: The template to use for the envelope.
        """
        return env.get_template("sql/test.j2")
