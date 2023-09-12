🧩 Reconstruction
=================

A Bifrost is capable of reconstructing the structured output from an LLM, to help ensure
that it will pass validation. In the code and docs, this is called "reconstruction" or
"autofixing." Although reconstruction is a general HeimdaLLM concept, This page will
explain it concretely in the context of the :class:`SQL SELECT Bifrost.
<heimdallm.bifrosts.sql.sqlite.select.bifrost.Bifrost>`

Rationale
*********

The goal of a :ref:`prompt envelope <bifrost-prompt-envelope>` is to coax an LLM into
producing a SQL query that has a high probability of being parsed and validated
correctly. Whatever we can do to facilitate a high success rate will result in a better
user experience. Otherwise, the end user may see their input frequently rejected due to
validation failures that are easy to fix.

While developing the :class:`SQLite SELECT Bifrost
<heimdallm.bifrosts.sql.sqlite.select.bifrost.Bifrost>` for HeimdaLLM, I noticed two
major sources of validation failures:

#. Queries with no ``LIMIT`` clause, or an incorrect ``LIMIT`` clause.
#. Queries that select columns that are forbidden by the validator.

This is not the fault of the LLM. It's unreliable and doesn't always do what you ask.
However, frequently failing validation is not a good user experience. To that end,
reconstruction was added to repair queries that have simple non-critical issues.

Reconstruction is enabled by default, but it can be disabled on a per-validation basis
by passing ``autofix=False`` to the :meth:`Bifrost.traverse
<heimdallm.bifrost.Bifrost.traverse>` method.


Bifrost-specific reconstruction
*******************************

.. toctree::
    :glob:

    reconstruction/*