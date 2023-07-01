.. _prompt-engineering:

🛠️ Prompt Engineering
=====================

The problem
***********
LLMs can hallucinate. This results in queries that use columns that don't exist. LLMs
can ignore instructions. This results

To achieve a high rate of success in parsing and validating an LLM's output, we must use
certain techniques to inspire the LLM to produce the desired output. You, the engineer,
have control over these techniques. To understand how to use them, we will first discuss
how a prompt is composed.

When untrusted input is received for traversing, it is wrapped in a prompt envelope.
This envelope consists of many different pieces of information, for example:

* The database's schema, so that the LLM can figure out how to compose the query.
* Some general SQL hints, like the database engine.
* Some general constraints, like "use fully-qualified column names."
* A description of the requester's identity, for adding the appropriate `WHERE` conditions.
* A description of the SQL output's delimiters, for easy parsing.
* The actual untrusted prompt.

This list is not exhaustive, but it should give you an idea of what goes into the
wrapped prompt. With this additional context, the LLM is primed to produce the desired
output with a high probability.

Manipulating the prompt
***********************

The database schema
-------------------
The database schema is one of the most important pieces of information in the final
prompt because it informs the LLM exactly how the query should be connected to achieve
the desired result. Because of this, annotating your schema with comments is a powerful
technique.

For example, consider the following schema:

.. code-block:: sql


The prompt envelope
-------------------
The prompt envelope is the outermost layer of the prompt. It wraps the prompt's content
with additional context