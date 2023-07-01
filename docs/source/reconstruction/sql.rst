SQL Reconstruction
==================

Adjusting a ``LIMIT``
*********************

If a query has no ``LIMIT`` clause, or a limit clause exists, but the value is too high,
HeimdaLLM will add a limit or adjust the limit.

For example:

.. code-block:: sql

    SELECT p.date
    FROM purchases p
    JOIN users u ON u.id=p.user_id
    WHERE u.id=:user_id

Will become:

.. code-block:: sql

    SELECT p.date
    FROM purchases p
    JOIN users u ON u.id=p.user_id
    WHERE u.id=:user_id
    LIMIT 100

Disallowed column removal
*************************

The :doc:`prompt envelope </api/bifrosts/sql/sqlite/select/envelope>` (and consequently,
the LLM) doesn't know what columns are allowlisted. This means that an LLM may produce a
``SELECT`` query that selects columns that are not allowed. For example, most of the
time, you probably don't want your users to see a id-like column:

.. code-block:: sql

    SELECT p.id, u.id, p.date
    FROM purchases p
    JOIN users u ON u.id=p.user_id
    WHERE u.id=:user_id

In a soft-validation pass, HeimdaLLM will test all selected columns and remove any
disallowed columns by modifying the parse tree directly, so that the resulting query
will pass validation.

.. code-block:: sql

    SELECT p.date
    FROM purchases p
    JOIN users u ON u.id=p.user_id
    WHERE u.id=:user_id

.. NOTE::

    Only selected columns are examined for reconstruction in this soft-validation pass.
    Other clauses of the query where columns are referenced, like the ``WHERE`` clause,
    are left alone until the hard-validation pass.