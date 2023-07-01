💡 Roadmap
==========

Below is a very high-level roadmap for HeimdaLLM.

.. TIP::

    Want to know when these features get implemented? Add your email to `this form
    <https://forms.gle/r3HjMPXBYwNjxANp7>`_ and I'll send you an email.

More databases
**************

I will be adding support for more SQL-based databases:

* MySQL
* PostgreSQL
* SQL Server
* Oracle
* Snowflake

.. NOTE::

    Want us to prioritize a specific database? Let us know by `voting here.
    <https://github.com/amoffat/HeimdaLLM/discussions/2>`_


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

More Bifrosts
*************

Bifrosts are not limited to converting human input to trusted SQL statements.
HeimdaLLM's has been deliberately designed to be general enough to support many kinds
of structured output. I intend to develop more powerful Bifrosts that supercharge your
ability to provide natural language interaction with your application. Stay tuned!