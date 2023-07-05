SQL Select Bifrost
==================

The SQL Select Bifrost produces a trusted SQL Select statement. It uses the following
components:

* :class:`SQLPromptEnvelope <heimdallm.bifrosts.sql.sqlite.select.envelope.SQLPromptEnvelope>`
* :class:`SQLConstraintValidator <heimdallm.bifrosts.sql.sqlite.select.validator.SQLConstraintValidator>`
* `Grammar <https://github.com/amoffat/HeimdaLLM/blob/dev/heimdallm/bifrosts/sql/sqlite/select/sqlite.lark>`_

.. autoclass:: heimdallm.bifrosts.sql.sqlite.select.bifrost.SQLBifrost
    :members:
    :inherited-members: