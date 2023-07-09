SQL Select Bifrost
==================

The SQL Select Bifrost produces a trusted SQL Select statement. It uses the following
components:

* :class:`SQLPromptEnvelope <heimdallm.bifrosts.sql.mysql.select.envelope.PromptEnvelope>`
* :class:`SQLConstraintValidator <heimdallm.bifrosts.sql.mysql.select.validator.ConstraintValidator>`
* `Grammar <https://github.com/amoffat/HeimdaLLM/blob/dev/heimdallm/bifrosts/sql/mysql/select/sqlite.lark>`_

.. autoclass:: heimdallm.bifrosts.sql.mysql.select.bifrost.Bifrost
    :members:
    :inherited-members: