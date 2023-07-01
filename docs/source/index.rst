HeimdaLLM
=========

   Heimdall, the watchman of the gods, dwelt at its entrance, where he guarded Bifrost,
   the shimmering path connecting the realms.

.. ATTENTION::

   These docs are under active development. Want to make sure something is included?
   Please request it `here. <https://github.com/amoffat/HeimdaLLM/discussions/3>`_

Welcome to the HeimdaLLM documentation!

HeimdaLLM safely bridges the gap between untrusted human input and trusted
machine-readable input by augmenting LLMs with a robust validation framework. It allows
you to do things like construct trusted SQL queries from untrusted input, **using
validation that you have full control over.**

.. image:: images/heimdall.png
   :target: https://docs.heimdallm.ai
   :alt: Heimdall guarding the Bifrost

.. .. image:: https://img.shields.io/github/stars/amoffat/HeimdaLLM.svg?style=social&label=Star
..    :target: https://github.com/amoffat/HeimdaLLM
..    :alt: GitHub Repo stars

.. image:: https://github.com/amoffat/HeimdaLLM/actions/workflows/main.yml/badge.svg?branch=main
   :target: https://github.com/amoffat/HeimdaLLM/actions
   :alt: Build status

.. image:: https://img.shields.io/github/sponsors/amoffat
   :target: https://github.com/sponsors/amoffat
   :alt: GitHub Sponsors

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


.. toctree::
   :hidden:
   :glob:
   :maxdepth: 5

   quickstart
   api/index
   validation
   reconstruction
   prompt_engineering
   attack_surface
   tutorials
   llm_quirks
   hints
   faq