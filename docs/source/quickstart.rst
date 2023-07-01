🚀 Quickstart
=============

.. TIP::

    You can also find this quickstart code in a Jupyter Notebook `here.
    <https://github.com/amoffat/HeimdaLLM/blob/dev/notebooks/quickstart.ipynb>`_


.. code-block:: python

    import logging
    from typing import Sequence

    import structlog

    from heimdallm.bifrosts.sql.sqlite.select.bifrost import SQLBifrost
    from heimdallm.bifrosts.sql.sqlite.select.envelope import SQLPromptEnvelope
    from heimdallm.bifrosts.sql.sqlite.select.validator import SQLConstraintValidator
    from heimdallm.bifrosts.sql.utils import FqColumn, JoinCondition, RequiredConstraint
    from heimdallm.llm_providers import openai

    logging.basicConfig(level=logging.ERROR)
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())

Set up your LLM integration. We'll use OpenAI. Remember to store your OpenAI API token
securely.

.. code-block:: python

    # load our openai api key secret from the environment.
    # create a `.env` file with your openai api secret.
    import os
    from dotenv import load_dotenv

    load_dotenv()
    open_api_key = os.getenv("OPENAI_API_SECRET")
    assert open_api_key

    llm = openai.Client(api_key=open_api_key)

Define our database schema that the LLM will work with. You can dump this directly from
your database, but a more practical and customizable method is to dump it beforehand to
a file, and manually trim out tables and columns that you don't want the LLM to know
about. You can also add inline SQL comments to help guide the LLM.

.. code-block:: python

    db_schema = """
    CREATE TABLE customer (
    customer_id INT NOT NULL,
    store_id INT NOT NULL,
    first_name VARCHAR(45) NOT NULL,
    last_name VARCHAR(45) NOT NULL,
    email VARCHAR(50) DEFAULT NULL,
    address_id INT NOT NULL,
    active CHAR(1) DEFAULT 'Y' NOT NULL,
    create_date TIMESTAMP NOT NULL,
    last_update TIMESTAMP NOT NULL,
    PRIMARY KEY  (customer_id),
    );
    """

Define our constraint validator(s). Each subclass must define some required abstract
base methods.

.. code-block:: python

    class ConstraintValidator(SQLConstraintValidator):
        def requester_identities(self) -> Sequence[RequiredConstraint]:
            return [
                RequiredConstraint(
                    column="customer.customer_id",
                    placeholder="customer_id",
                ),
            ]

        def required_constraints(self) -> Sequence[RequiredConstraint]:
            return []

        def select_column_allowed(self, column: FqColumn) -> bool:
            return True

        def allowed_joins(self) -> Sequence[JoinCondition]:
            return []

        def max_limit(self) -> int | None:
            return None


    validator = ConstraintValidator()

.. code-block:: python

    envelope = SQLPromptEnvelope(
        llm=llm,
        db_schema=db_schema,
        validators=[validator],
    )

Now bring everything together into a Bifrost.

.. code-block:: python

    bifrost = SQLBifrost(
        prompt_envelope=envelope,
        llm=llm,
        constraint_validators=[validator],
    )

You can now traverse untrusted human input with the Bifrost.

.. code-block:: python

    query = bifrost.traverse("Show me my email")
    print(query)