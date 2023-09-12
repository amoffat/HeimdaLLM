Sql
===

Fully-qualified columns
***********************

The LLM needs to be told explicitly to use fully-qualified column names.

.. HINT::
   A fully-qualified column is one that includes both the table name and the column
   name, joined by ``.``.

Sometimes it doesn't do this, and instead uses the column name on its own. We currently
have no support for unqualified column names, and the code will raise an exception when
it sees one. The reason for this is that unqualified column names require an analysis of
the schema to determine which table they belong to, which makes the validation process
much more complex. Instead, we attempt to convince the LLM to use fully-qualified column
names.

This may change in the future, but for now, it's a limitation of the system.

Arbitrary limits
****************

An LLM will sometimes include a ``LIMIT`` on a query, and other times it won't. This can
have performance impacts and is generally undesirable.

Instead, our constraint validator is capable of rebuilding the query to include a
``LIMIT`` if one is not present, or to adjust an existing ``LIMIT``, if the current one
is too high. See :doc:`/reconstruction/sql` for more information.

Superfluous selected columns
****************************

Often times, the LLM will include columns that the requester did not ask for. If your
constraints are set correctly, this is not a security problem, but the violation of your
constraints can cause a high rate of failure for the generated queries, because
validation fails.

Similarly to how we handle the ``LIMIT`` issue, our constraint validator is capable of
rebuilding the query to remove any columns from the ``SELECT`` that are disallowed.
See :doc:`/reconstruction/sql` for more information.

Misplaced ``WHERE`` conditions
******************************

When the LLM is instructed to include a requested identity, sometimes it includes that
identity constraint on a ``JOIN`` condition, instead of in the ``WHERE`` clause. For
example, if we ask it to assume that the requester is
``customer.customer_id=:customer_id``, you might expect the following:

.. code-block:: sql

    SELECT c.email
    FROM customer c
    JOIN rental r
        ON c.customer_id=r.customer_id
    WHERE c.customer_id=:customer_id

But in fact, you may get:

.. code-block:: sql
    
    SELECT c.email
    FROM customer c
    JOIN rental r
        ON c.customer_id=r.customer_id
        AND c.customer_id=:customer_id

This quirk is why it's so important to :ref:`only allow inner equi-joins <outer-joins>`,
because an outer join would return a different result set.