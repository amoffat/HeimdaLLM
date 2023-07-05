SQL Reconstruction
==================

Adjusting a ``LIMIT``
*********************

This adjustment only takes place if :meth:`SQLConstraintValidator.max_limit
<heimdallm.bifrosts.sql.sqlite.select.validator.SQLConstraintValidator.max_limit>` in
your validator subclass returns an integer.

If a query has no ``LIMIT`` clause, one will be added. For example:

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

Similarly, if an existing ``LIMIT`` is too high, it will be lowered to the maximum
returned by your validator.

Disallowed column removal
*************************

This adjustment takes place if a column appears in the result returned from
:meth:`SQLConstraintValidator.select_column_allowed
<heimdallm.bifrosts.sql.sqlite.select.validator.SQLConstraintValidator.select_column_allowed>`

The :doc:`prompt envelope </api/bifrosts/sql/sqlite/select/envelope>` (and consequently,
the LLM) isn't told what columns are allowlisted. This means that an LLM may produce a
``SELECT`` query that selects columns that are not allowed. For example, most of the
time, you probably don't want your users to see a id-like column:

.. code-block:: sql

    SELECT p.id, u.id, p.date
    FROM purchases p
    JOIN users u ON u.id=p.user_id
    WHERE u.id=:user_id

In a soft-validation pass, HeimdaLLM will test all selected columns and remove any
disallowed columns by modifying the parse tree directly, so that the resulting query
will pass validation:

.. code-block:: sql

    SELECT p.date
    FROM purchases p
    JOIN users u ON u.id=p.user_id
    WHERE u.id=:user_id

.. NOTE::

    Only selected columns are examined for reconstruction in this soft-validation pass.
    Other clauses of the query where columns are referenced, like the ``WHERE`` clause,
    are left alone until the hard-validation pass, where they could cause a failure.