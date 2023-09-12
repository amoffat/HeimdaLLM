SQL Select Bifrost
==================

The SQL Select Bifrost produces a trusted SQL Select statement. It uses the following
components:

* :class:`SQLPromptEnvelope <heimdallm.bifrosts.sql.postgres.select.envelope.PromptEnvelope>`
* :class:`SQLConstraintValidator <heimdallm.bifrosts.sql.postgres.select.validator.ConstraintValidator>`
* `Grammar <https://github.com/amoffat/HeimdaLLM/blob/dev/heimdallm/bifrosts/sql/postgres/select/grammar.lark>`_

.. autoclass:: heimdallm.bifrosts.sql.postgres.select.bifrost.Bifrost
    :members:
    :inherited-members: