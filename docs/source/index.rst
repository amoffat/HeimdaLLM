HeimdaLLM
=========

.. role:: phonetic

Pronounced :phonetic:`[ˈhaɪm.dɔl.əm]` or HEIM-dall-em

HeimdaLLM is a robust static analysis framework for validating that LLM-generated
structured output is safe. It currently supports SQL.

In simple terms, it helps makes sure that AI won't wreck your systems.

.. image:: https://raw.githubusercontent.com/amoffat/HeimdaLLM/main/docs/source/images/heimdall.png
   :target: https://github.com/amoffat/HeimdaLLM
   :alt: Heimdall guarding the Bifrost

.. image:: https://github.com/amoffat/HeimdaLLM/actions/workflows/main.yml/badge.svg?branch=main
   :target: https://github.com/amoffat/HeimdaLLM/actions
   :alt: Build status

.. image:: https://img.shields.io/pypi/v/heimdallm
   :target: https://pypi.org/project/heimdallm/
   :alt: PyPI

.. image:: https://img.shields.io/badge/License-Commercial-blue.svg
   :target: https://forms.gle/frEPeeJx81Cmwva78
   :alt: License: Commercial

.. image:: https://img.shields.io/badge/License-AGPL_v3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0
   :alt: License: AGPL v3

.. image:: https://coveralls.io/repos/github/amoffat/HeimdaLLM/badge.svg?branch=dev
   :target: https://coveralls.io/github/amoffat/HeimdaLLM?branch=dev
   :alt: Coverage Status

.. image:: https://img.shields.io/github/stars/amoffat/HeimdaLLM.svg?style=social&label=Star
   :target: https://github.com/amoffat/HeimdaLLM
   :alt: GitHub Repo stars

Consider the following natural-language database query:

.. code-block:: text

   how much have i spent renting movies, broken down by month?

From this query, an LLM can produce the following SQL query:

.. code-block:: sql

   SELECT
      strftime('%Y-%m', payment.payment_date) AS month,
      SUM(payment.amount) AS total_amount
   FROM payment
   JOIN rental ON payment.rental_id=rental.rental_id
   JOIN customer ON payment.customer_id=customer.customer_id
   WHERE customer.customer_id=:customer_id
   GROUP BY month
   LIMIT 10;

But how can you ensure that its safe and that it only accesses authorized data?

HeimdaLLM performs static analysis on the generated SQL to ensure that only certain
columns, tables, and functions are used. It also automatically edits the query to add a
``LIMIT`` and to remove forbidden columns. Lastly, it ensures that there is a column
constraint that would restrict the results to only the user's data.

It does all of this locally, without AI, using good ol' fashioned grammars and parsers:

.. code-block:: text

   ✅ Ensuring SELECT statement...
   ✅ Resolving column and table aliases... 
   ✅ Allowlisting selectable columns...
      ✅ Removing 2 forbidden columns...
   ✅ Ensuring correct row LIMIT exists...
      ✅ Lowering row LIMIT to 10...
   ✅ Checking JOINed tables and conditions...
   ✅ Checking required WHERE conditions...
   ✅ Ensuring query is constrained to requester's identity...
   ✅ Allowlisting SQL functions...
      ✅ strftime
      ✅ SUM

The validated query can then be executed:

+---------+--------------+
|  month  | total_amount |
+---------+--------------+
| 2005-05 | 4.99         |
+---------+--------------+
| 2005-06 | 22.95        |
+---------+--------------+
| 2005-07 | 100.78       |
+---------+--------------+
| 2005-08 | 87.82        |
+---------+--------------+

Want to get started quickly? :doc:`quickstart/index`.

.. toctree::
   :hidden:
   :glob:
   :maxdepth: 5

   quickstart/index
   blog/index
   api/index
   reconstruction
   attack-surface/index
   tutorials/index
   llm-quirks/index
   glossary
   roadmap
   architecture/index
   faq

.. ATTENTION::

   These docs are under active development. See an issue? Report it `here.
   <https://github.com/amoffat/HeimdaLLM/issues/new?title=Documentation%20fix&labels=documentation>`__
   Want to make sure something is included? Please request it `here.
   <https://github.com/amoffat/HeimdaLLM/discussions/3>`__