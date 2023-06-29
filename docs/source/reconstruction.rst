Reconstruction
==============

HeimdaLLM is capable of composing a SQL query from another SQL query. In the code,
this is called "reconstruction" and "autofixing."

The goal of the LLM portion of HeimdaLLM is to coax an LLM into producing a SQL query
that has a high probability of being parsed and validated correctly. Whatever we can do
to facilitate a high success rate will result in a better user experience.

To that end, reconstruction was added to repair queries that have simple non-critical
issues. For example, adding a `LIMIT` to a query with no limit. The range of these
fixes is currently limited, but we plan on expanding them in the future.

Reconstruction is enabled by default, but it can be disabled on a per-query basis by
passing `autofix=False` to the `Bifrost.traverse()` method.

Adjusting `LIMIT`s
******************

If a query has no `LIMIT` clause