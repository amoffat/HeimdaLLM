import jinja2

from heimdallm.bifrosts.sql.sqlite.select.envelope import SQLPromptEnvelope
from heimdallm.llm_providers.mock import EchoMockLLM

from .utils import CustomerConstraints, PermissiveConstraints


def test_quoted():
    resp = """
    ```
    select t1.col from t1
    ```
    """
    unwrapped = SQLPromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[PermissiveConstraints()],
    ).unwrap(resp)
    assert unwrapped == "select t1.col from t1"


def test_quoted_with_sql():
    resp = """
    ```sql
    select t1.col from t1
    ```
    """
    unwrapped = SQLPromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[PermissiveConstraints()],
    ).unwrap(resp)
    assert unwrapped == "select t1.col from t1"


def test_with_sql():
    resp = """sql
    select t1.col from t1
    """
    unwrapped = SQLPromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[PermissiveConstraints()],
    ).unwrap(resp)
    assert unwrapped == "select t1.col from t1"


def test_raw_unquoted():
    resp = """
    select t1.col from t1
    """
    unwrapped = SQLPromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[PermissiveConstraints()],
    ).unwrap(resp)
    assert unwrapped == "select t1.col from t1"


def test_no_idents():
    input = """
    select t1.col from t1
    """
    envelope = SQLPromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[PermissiveConstraints()],
    ).wrap(input)
    # brittle
    assert "unrestricted access" in envelope


def test_multi_idents():
    input = """
    select t1.col from t1
    """
    envelope = SQLPromptEnvelope(
        llm=EchoMockLLM(),
        db_schema="<schema>",
        validators=[CustomerConstraints()],
    ).wrap(input)
    # brittle
    assert ":customer_id" in envelope


def test_custom_envelope():
    class MyEnvelope(SQLPromptEnvelope):
        def template(self, env: jinja2.Environment) -> jinja2.Template:
            tmpl = """
            {% extends "base.j2" %}

            {% block delimiters %}
            Delimit with &&&
            {% endblock %}

            {% block extras %}
            {{abc}} do a barrel roll
            {% endblock %}
            """
            return env.from_string(tmpl)

        @property
        def params(self) -> dict:
            return {"abc": 123}

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
