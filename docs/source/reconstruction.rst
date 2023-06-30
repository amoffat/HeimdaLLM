.. _reconstruction:

🧩 Reconstruction
=================

HeimdaLLM is capable of doing limited repairs on a SQL query by re-composing it from a
modified parse tree. In the code, this is called "reconstruction" or "autofixing."

Rationale
*********

The goal of a :ref:`prompt envelope<prompt_envelope>` is to coax an LLM into producing a
SQL query that has a high probability of being parsed and validated correctly. Whatever
we can do to facilitate a high success rate will result in a better user experience.
Otherwise, the user may see many queries rejected.

While developing HeimdaLLM, I noticed two major sources of validation failures:

#. Queries with no ``LIMIT`` clause, or an incorrect ``LIMIT`` clause.
#. Queries that select columns that are forbidden.

This is not the fault of the LLM. It's unreliable and doesn't always do what you ask.
However, frequently failing validation is not a good user experience. To that end,
reconstruction was added to repair queries that have simple non-critical issues.

Reconstruction is enabled by default, but it can be disabled on a per-query basis by
passing ``autofix=False`` to the :meth:`Bifrost.traverse()
<heimdallm.bifrost.Bifrost.traverse>` method.

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

Removing disallowed columns
************************

The :ref:`prompt envelope <prompt-envelope>` (and consequently, the LLM) doesn't know
what columns are allowlisted. This means that an LLM may produce a ``SELECT`` query that
selects columns that are not allowed. For example, most of the time, you probably don't
want your users to see a id-like column:

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