.. _api:

📚 Api
======

Bifrosts
********

Bifrosts are the fundamental unit of translating untrusted input into trusted input.

SQL
---

We will expand this to support more relational databases. To vote for your favorite
database, please participate in `this poll.
<https://github.com/amoffat/HeimdaLLM/discussions/2>`_

Sqlite
~~~~~~

* :doc:`Select <bifrosts/sql/sqlite/select/bifrost>`
* Insert (coming soon)
* Update (coming soon)
* Delete (coming soon)

.. toctree::
    :glob:

    bifrosts/sql/sqlite/index

Abstract classes
****************

Below are the abstract classes that support the building of new Bifrosts. They aren't
intended for direct use.

Bifrost
-------

.. toctree::
    
    bifrost

LLM Providers
*************

As the LLM API ecosystem expands, we'll add new LLM providers here.

.. toctree::
    :glob:

    llm_providers/*