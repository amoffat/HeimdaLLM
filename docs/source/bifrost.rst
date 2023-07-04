🌈 Bifrost
==========

The Bifrost is the key technology that enables the translation of untrusted human input
into trusted machine-readable input. It is composed of 4 parts:

* The LLM prompt envelope
* The LLM integration
* The grammar
* The constraint validators

These components are assembled together to form a Bifrost instance, which can then
operate as a function on untrusted input.

.. note::

    The Bifrost is a general concept, and is not tied specifically to the SQL Bifrost,
    though the SQL Bifrost is the first implementation of the Bifrost in HeimdaLLM.


.. _bifrost-prompt-envelope:

The prompt envelope
*******************

The prompt envelope is responsible for adding additional context to the untrusted input.
Concretely, this typically involves including specific instructions to the LLM, for
example:

* A copy of the database schema on which the LLM should operate
* That the LLM should use fully-qualified column names
* How to delimit the resulting SQL query

Along with the prompt envelope's job to :meth:`wrap
<heimdallm.envelope.PromptEnvelope.wrap>` the untrusted input in this additional
context, it's job is also to :meth:`unwrap <heimdallm.envelope.PromptEnvelope.unwrap>`

Current implemented prompt envelopes:

.. currentmodule:: heimdallm.bifrosts

* :class:`SQLPromptEnvelope <sql.sqlite.select.envelope.SQLPromptEnvelope>`

The LLM Integration
*******************

:term:`LLMs <LLM>` should be treated as a commodity. As such, HeimdaLLM aims to make it
easy to swap out LLMs in your Bifrost, so that as capabilities and prices change, your
system can adapt.

Current LLM integrations:

.. toctree::
    :maxdepth: 2

    api/llm_providers/index

The grammar
***********

The grammar is the first stage that a handles an LLM's untrusted output. After the
:term:`prompt envelope` has unpacked the structured data, the grammar is responsible for
defining how the structured data is to be parsed into a machine-readable format.

No validation happens at this stage, though parts of the grammar can be viewed as
validation. For example, if the grammar does not define the syntax for an ``DELETE`` SQL
statement, then the parsing of the LLM's output will not allow ``DELETE`` statements.

The grammar works very closely with the constraint validators, as the grammar can define
tokens and rules that make it easier for the validator to do its job.

The constraint validators
*************************

The real meat of the Bifrost are the constraint validators. A constraint validator is
responsible for taking the tree produced by the grammar and validating it against rules
that you define.