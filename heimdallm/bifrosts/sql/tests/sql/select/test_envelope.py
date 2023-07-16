from typing import Type

import jinja2

from heimdallm.bifrosts.sql.sqlite.select.envelope import PromptEnvelope
from heimdallm.llm_providers.mock import EchoMockLLM

from ..utils import dialects
from .utils import CustomerConstraints, PermissiveConstraints


@dialects(bifrost=False, envelope=True)
def test_quoted(dialect: str, PromptEnvelope: Type[PromptEnvelope]):
    resp = """
    ```
    select t1.col from t1
    ```
    """
    unwrapped = PromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[PermissiveConstraints()],
    ).unwrap(resp)
    assert unwrapped == "select t1.col from t1"


@dialects(bifrost=False, envelope=True)
def test_quoted_with_sql(dialect: str, PromptEnvelope: Type[PromptEnvelope]):
    resp = """
    ```sql
    select t1.col from t1
    ```
    """
    unwrapped = PromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[PermissiveConstraints()],
    ).unwrap(resp)
    assert unwrapped == "select t1.col from t1"


@dialects(bifrost=False, envelope=True)
def test_with_sql(dialect: str, PromptEnvelope: Type[PromptEnvelope]):
    resp = """sql
    select t1.col from t1
    """
    unwrapped = PromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[PermissiveConstraints()],
    ).unwrap(resp)
    assert unwrapped == "select t1.col from t1"


@dialects(bifrost=False, envelope=True)
def test_raw_unquoted(dialect: str, PromptEnvelope: Type[PromptEnvelope]):
    resp = """
    select t1.col from t1
    """
    unwrapped = PromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[PermissiveConstraints()],
    ).unwrap(resp)
    assert unwrapped == "select t1.col from t1"


@dialects(bifrost=False, envelope=True)
def test_no_idents(dialect: str, PromptEnvelope: Type[PromptEnvelope]):
    input = """
    select t1.col from t1
    """
    envelope = PromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[PermissiveConstraints()],
    ).wrap(input)
    # brittle
    assert "unrestricted access" in envelope


@dialects(bifrost=False, envelope=True)
def test_multi_idents(dialect: str, PromptEnvelope: Type[PromptEnvelope]):
    input = """
    select t1.col from t1
    """
    envelope = PromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[CustomerConstraints()],
    ).wrap(input)
    # brittle
    assert ":customer_id" in envelope


@dialects(bifrost=False, envelope=True)
def test_custom_envelope(dialect: str, PromptEnvelope: Type[PromptEnvelope]):
    def template(self, env: jinja2.Environment) -> jinja2.Template:
        tmpl = """
        {% extends "sql/sqlite/select.j2" %}

        {% block delimiters %}
        Delimit with &&&
        {% endblock %}

        {% block extras %}
        {{abc}} do a barrel roll
        {% endblock %}
        """
        return env.from_string(tmpl)

    def params(self) -> dict:
        return {"abc": 123}

    MyEnvelope = type(
        "MyEnvelope",
        (PromptEnvelope,),
        {
            "template": template,
        },
    )
    setattr(MyEnvelope, "params", property(params))

    envelope = MyEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[PermissiveConstraints()],
    ).wrap(input)

    # shows that we overrode the `delimiters` block
    assert '"```"' not in envelope
    assert "&&&" in envelope

    # shows that we can include extra data in the `extras` block
    assert "123 do a barrel roll" in envelope

    # shows that the base template was included
    assert "unrestricted access" in envelope
