HeimdaLLM
=========

   Heimdall, the watchman of the gods, dwelt at its entrance, where he guarded Bifrost,
   the shimmering path connecting the realms.

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

.. ATTENTION::

   These docs are under active development. See an issue? Report it `here.
   <https://github.com/amoffat/HeimdaLLM/issues/new?title=Documentation%20fix&labels=documentation>`__
   Want to make sure something is included? Please request it `here.
   <https://github.com/amoffat/HeimdaLLM/discussions/3>`__

Welcome to the HeimdaLLM documentation!

HeimdaLLM safely bridges the gap between untrusted human input and trusted
machine-readable output by augmenting :term:`LLMs <LLM>` with a robust validation
framework. This enables you to :term:`externalize <externalizing>` LLM technology to
your users, so that you can do things like execute trusted SQL queries from their
untrusted input.

Imagine giving your users natural language access to their data in your database,
without having to worry about dangerous queries.

.. code-block:: python

   traverse("Show me the movies I rented the longest, and the number of days I had them for.")

.. code-block:: text

   ✅ Ensuring SELECT statement...
   ✅ Resolving column and table aliases... 
   ✅ Allowlisting selectable columns...
      ✅ Removing 4 forbidden columns...
   ✅ Ensuring correct row LIMIT exists...
      ✅ Lowering row LIMIT to 5...
   ✅ Checking JOINed tables and conditions...
   ✅ Checking required WHERE conditions...
   ✅ Ensuring query is constrained to requester's identity...
   ✅ Allowlisting SQL functions...

+-----------------+------------------------+------------------------+--------------+
| Title           | Rental Date            | Return Date            | Rental Days  |
+=================+========================+========================+==============+
| OUTLAW HANKY    | 2005-08-19 05:48:12.000| 2005-08-28 10:10:12.000| 9.181944     |
+-----------------+------------------------+------------------------+--------------+
| BOULEVARD MOB   | 2005-08-19 07:06:51.000| 2005-08-28 10:35:51.000| 9.145139     |
+-----------------+------------------------+------------------------+--------------+
| MINDS TRUMAN    | 2005-08-02 17:42:49.000| 2005-08-11 18:14:49.000| 9.022222     |
+-----------------+------------------------+------------------------+--------------+
| AMERICAN CIRCUS | 2005-07-12 16:37:55.000| 2005-07-21 16:04:55.000| 8.977083     |
+-----------------+------------------------+------------------------+--------------+
| LADY STAGE      | 2005-07-28 10:07:04.000| 2005-08-06 08:16:04.000| 8.922917     |
+-----------------+------------------------+------------------------+--------------+

.. TIP::

   Run this example safely in Github Codespaces |CodespacesLink|_

Interested in getting started quickly? Check out the :doc:`quickstart`. Otherwise,
browse the navigation on the left.

.. toctree::
   :hidden:
   :glob:
   :maxdepth: 5

   quickstart
   bifrost
   api/index
   reconstruction
   attack_surface
   tutorials
   llm_quirks
   glossary
   roadmap
   faq

.. |CodespacesLink| image:: https://img.shields.io/badge/Open%20in-Codespaces-purple.svg
.. _CodespacesLink: https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=656570421