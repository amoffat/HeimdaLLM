SQL Select Bifrost
==================

The SQL Select Bifrost produces a trusted SQL Select statement. It uses the following
components:

* :class:`SQLPromptEnvelope <heimdallm.bifrosts.sql.sqlite.select.envelope.PromptEnvelope>`
* :class:`SQLConstraintValidator <heimdallm.bifrosts.sql.sqlite.select.validator.ConstraintValidator>`
* `Grammar <https://github.com/amoffat/HeimdaLLM/blob/dev/heimdallm/bifrosts/sql/sqlite/select/sqlite.lark>`_

.. autoclass:: heimdallm.bifrosts.sql.sqlite.select.bifrost.Bifrost
    :members:
    :inherited-members: