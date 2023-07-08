🌈 Bifrost
==========

The Bifrost is the key technology that enables the translation of untrusted human input
into trusted machine-readable input. It is composed of 4 parts:

#. 📩 The LLM prompt envelope
#. 🧠 The LLM integration
#. 📜 The grammar
#. ✅ The constraint validators

These components are assembled together to form a Bifrost instance, which can then
operate as a function on untrusted input.

.. note::

    The Bifrost is a general concept, and is not tied specifically to the SQL Bifrost,
    though the SQL Bifrost is the first implementation of a Bifrost in HeimdaLLM.


.. _bifrost-prompt-envelope:

📩 The prompt envelope
**********************

The prompt envelope is responsible for adding additional context to the untrusted input.
Concretely, this typically involves including specific instructions to the LLM abut the
original prompt. In the :class:`SQLPromptEnvelope
<heimdallm.bifrosts.sql.sqlite.select.envelope.PromptEnvelope>`, for example, we add:

* A copy of the database schema on which the LLM should operate
* That the LLM should use fully-qualified column names
* How to delimit the resulting SQL query so that we can easily extract it

Along with the prompt envelope's job to :meth:`wrap
<heimdallm.envelope.PromptEnvelope.wrap>` the untrusted input in this additional
context, it's job is also to :meth:`unwrap <heimdallm.envelope.PromptEnvelope.unwrap>`
the structured data from an LLM's output. This typically involves finding and parsing
out the structured data from the delimiters that you instructed the LLM to use.

🧠 The LLM Integration
**********************

The :term:`LLM <LLM>` itself is the brains of the Bifrost. We view it as a black box
with a :doc:`well-defined interface </api/abc/llm_integration>`. Because of this,
HeimdaLLM aims to make it easy to swap out LLMs in your Bifrost, so that as LLM
capabilities and prices change, your system can adapt to use them with minimal effort.

Current LLM integrations:

.. toctree::
    :maxdepth: 2

    api/llm_providers/index

📜 The grammar
**************

After the prompt envelope has unwrapped the structured data from the LLM's output, it's
the grammar's responsibility to enforce the syntax through an attempt at parsing the
data.

No formal validation happens at this stage, though parts of the grammar can be viewed as
validation. For example, if the grammar does not define the syntax for an ``DELETE`` SQL
statement, then the parsing of the LLM's output will not allow ``DELETE`` statements.

The grammar works very closely with the constraint validators, as the grammar can define
tokens and rules that make it easier for the validator to do its job.

✅ The constraint validators
****************************

The real meat of the Bifrost are the constraint validators. A constraint validator is
responsible for taking the tree produced by the grammar and validating it against rules
that you define.

A Bifrost can take multiple constraint validators, and **only one validator is required
to succeed** in order to pass the validation step.