🚀 Quickstart
=============

This quickstart will walk you through setting up a SQL Bifrost with OpenAI's LLM. The
end result is a function that takes natural language input and returns a trusted SQL
``SELECT`` query, constrained to your requirements.

.. TIP::

    You can also find this quickstart code in a Jupyter Notebook `here.
    <https://github.com/amoffat/HeimdaLLM/blob/dev/notebooks/quickstart.ipynb>`_


First let's set up our imports.

.. code-block:: python

    import logging
    from typing import Sequence

    import structlog

    from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost
    from heimdallm.bifrosts.sql.sqlite.select.envelope import PromptEnvelope
    from heimdallm.bifrosts.sql.sqlite.select.validator import ConstraintValidator 
    from heimdallm.bifrosts.sql.utils import FqColumn, JoinCondition, RequiredConstraint
    from heimdallm.llm_providers import openai

    logging.basicConfig(level=logging.ERROR)
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())

Now let's set up our LLM integration. We'll use OpenAI. Remember to store your OpenAI
API token securely.

.. code-block:: python

    # load our openai api key secret from the environment.
    # create a `.env` file with your openai api secret.
    import os
    from dotenv import load_dotenv

    load_dotenv()
    open_api_key = os.getenv("OPENAI_API_SECRET")
    assert open_api_key

    llm = openai.Client(api_key=open_api_key)

Now we'll define our database schema. You can dump this directly from your database, but
a better method is to dump it out beforehand to a file, manually trim out tables and
columns that you don't want the LLM to know about, and load it from that file. You can
also add SQL comments to help explain the schema to the LLM.

.. code-block:: python

    # abbreviated example schema
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

Let's define our constraint validator(s). These are used to constrain the SQL query so
that it only has access to tables and columns that you allow. For more information on
the methods that you can override in the derived class, look :doc:`here.
</api/bifrosts/sql/sqlite/select/validator>`

.. code-block:: python

    class CustomerConstraintValidator(SQLConstraintValidator):
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


    validator = CustomerConstraintValidator()

We'll define our prompt envelope. This adds additional context to any human input so
that the LLM is guided to produce a correct response.

.. code-block:: python

    envelope = PromptEnvelope(
        llm=llm,
        db_schema=db_schema,
        validators=[validator],
    )

Now we can bring everything together into a :doc:`/bifrost`

.. code-block:: python

    bifrost = Bifrost(
        prompt_envelope=envelope,
        llm=llm,
        constraint_validators=[validator],
    )

You can now traverse untrusted human input with the Bifrost.

.. code-block:: python

    query = bifrost.traverse("Show me my email")
    print(query)

The output should be something like:

.. code-block:: sql

    SELECT customer.email
    FROM customer
    WHERE customer.customer_id=:customer_id