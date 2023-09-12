Validation only
===============

This quickstart will walk you through setting up a HeimdaLLM to validate a SQL query
from an untrusted source, presumably from an LLM. The end result is a function that
takes natural language input and returns a trusted SQL ``SELECT`` query, constrained to
your requirements.

If you wish to also use HeimdaLLM to talk to an LLM for you to generate the SQL query,
see :doc:`this quickstart <llm>`.

.. TIP::

    You can also find this quickstart code in a Jupyter Notebook `here.
    <https://github.com/amoffat/HeimdaLLM/blob/dev/notebooks/quickstart/validation.ipynb>`_


First let's set up our imports.

.. code-block:: python

    import logging
    from typing import Sequence

    import structlog

    from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost
    from heimdallm.bifrosts.sql.sqlite.select.validator import ConstraintValidator 
    from heimdallm.bifrosts.sql.common import FqColumn, JoinCondition, ParameterizedConstraint

    logging.basicConfig(level=logging.ERROR)
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())


Let's define our constraint validator(s). These are used to constrain the SQL query so
that it only has access to tables and columns that you allow. For more information on
the methods that you can override in the derived class, look :doc:`here.
</api/bifrosts/sql/sqlite/select/validator>`

.. code-block:: python

    class CustomerConstraintValidator(ConstraintValidator):
        def requester_identities(self) -> Sequence[ParameterizedConstraint]:
            return [
                ParameterizedConstraint(
                    column="customer.customer_id",
                    placeholder="customer_id",
                ),
            ]

        def parameterized_constraints(self) -> Sequence[ParameterizedConstraint]:
            return []

        def select_column_allowed(self, column: FqColumn) -> bool:
            return True

        def allowed_joins(self) -> Sequence[JoinCondition]:
            return [
                JoinCondition("payment.rental_id", "rental.rental_id"),
                JoinCondition(
                    "customer.customer_id",
                    "payment.customer_id",
                    identity="customer_id",
                ),
            ]

        def max_limit(self) -> int | None:
            return 10


    validator = CustomerConstraintValidator()

Now let's construct a Bifrost that validates SQL:

.. code-block:: python

    bifrost = Bifrost.validation_only(
        constraint_validators=[validator],
    )

You can now validate constraints on SQL:

.. code-block:: python

    query = """
    SELECT
        strftime('%Y-%m', payment.payment_date) AS month,
        SUM(payment.amount) AS total_amount
    FROM payment
    JOIN rental ON payment.rental_id=rental.rental_id
    JOIN customer ON payment.customer_id=customer.customer_id
    WHERE customer.customer_id=:customer_id
    GROUP BY month
    """

    query = bifrost.traverse(query)
    print(query)