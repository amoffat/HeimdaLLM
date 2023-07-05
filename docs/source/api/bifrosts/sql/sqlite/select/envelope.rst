SQL Select Envelope
===================

.. CAUTION::

    The ``db_schema`` argument of the constructor is passed to the LLM. This is how the
    LLM knows how to construct the query. If this concerns you, limit the information
    that you include in the schema.

.. autoclass:: heimdallm.bifrosts.sql.sqlite.select.envelope.SQLPromptEnvelope
    :members:
    :inherited-members: