💡 Roadmap
==========

Below is a very high-level roadmap for HeimdaLLM.

.. TIP::

    Want to know when these features get implemented? Add your email to `this form
    <https://forms.gle/r3HjMPXBYwNjxANp7>`_ and I will contact you.


More SQL statement types
************************

``SELECT`` gets the biggest bang for the buck, but other SQL statements are also very
useful and would benefit tremendously from a Bifrost. For example, ``INSERT``:

.. code-block:: python

    traverse("Add a new calendar entry for Dinner at 7 on friday")

Could produce a validated SQL query:

.. code-block:: sql

    INSERT INTO calendar (title, when, user_id)
    VALUES ('Dinner at 7 on friday', '2023-07-01 19:00:00', 123)

Generalized constraint spec
***************************

The current implementation requires a Python application to use HeimdaLLM, because
constraint validators are defined by subclassing a Python class. A future implementation
could be language agnostic by providing an api and a JSON or YAML spec for constraining
LLM output.


More LLM integrations
*********************

Currently we support OpenAI, but I intend to add support for all major LLM API services,
and private LLMs, as they become more capable.

More databases
**************

I will be adding support for more SQL-based databases:

* SQL Server
* Oracle
* Snowflake

.. NOTE::

    Want us to prioritize a specific database? Let us know by `voting here.
    <https://github.com/amoffat/HeimdaLLM/discussions/2>`_


More Bifrosts
*************

Bifrosts are not limited to converting human input to trusted SQL statements. HeimdaLLM
is generalized enough to support many kinds of structured output. I intend to develop
more Bifrosts that facilitate natural language interactions with your application.
Stay tuned!