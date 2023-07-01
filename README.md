# HeimdaLLM

> Heimdall, the watchman of the gods, dwelt at its entrance, where he guarded Bifrost,
> the shimmering path connecting the realms.

[![Heimdall](./docs/source/images/heimdall.png)](https://docs.heimdallm.ai)
[![Build status](https://github.com/amoffat/HeimdaLLM/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/amoffat/HeimdaLLM/actions)
[![Docs](https://img.shields.io/badge/Docs-purple.svg)](https://docs.heimdallm.ai)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/amoffat)](https://github.com/sponsors/amoffat)
[![PyPI](https://img.shields.io/pypi/v/heimdallm)](https://pypi.org/project/heimdallm/)
[![License: Commercial](https://img.shields.io/badge/License-Commercial-blue.svg)](https://forms.gle/frEPeeJx81Cmwva78)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Coverage Status](https://coveralls.io/repos/github/amoffat/HeimdaLLM/badge.svg?branch=dev)](https://coveralls.io/github/amoffat/HeimdaLLM?branch=dev)

HeimdaLLM safely bridges the gap between untrusted human input and trusted
machine-readable input by augmenting LLMs with a robust validation framework. It allows
you to do things like construct trusted SQL queries from untrusted input, **using
validation that you have full control over.**

To accomplish this, HeimdaLLM introduces a new technology, the 🌈✨ Bifrost, composed of
4 parts: an LLM prompt envelope, an LLM integration, a grammar, and a constraint
validator. These 4 components operate as a single unit—a Bifrost—which is capable of
translating untrusted human input into trusted machine input.

✨ **This allows you to perform magic** ✨

Imagine giving your users natural language access to their data in your database,
without having to worry about dangerous queries. This is an actual query on the [Sakila
Sample
Database](https://www.kaggle.com/datasets/atanaskanev/sqlite-sakila-sample-database):

```python
traverse("Show me the 5 movies I rented the longest, and the number of days I had them for.")
```

|     | Title           | Rental Date             | Return Date             | Rental Days |
| --- | --------------- | ----------------------- | ----------------------- | ----------- |
| 0   | OUTLAW HANKY    | 2005-08-19 05:48:12.000 | 2005-08-28 10:10:12.000 | 9.181944    |
| 1   | BOULEVARD MOB   | 2005-08-19 07:06:51.000 | 2005-08-28 10:35:51.000 | 9.145139    |
| 2   | MINDS TRUMAN    | 2005-08-02 17:42:49.000 | 2005-08-11 18:14:49.000 | 9.022222    |
| 3   | AMERICAN CIRCUS | 2005-07-12 16:37:55.000 | 2005-07-21 16:04:55.000 | 8.977083    |
| 4   | LADY STAGE      | 2005-07-28 10:07:04.000 | 2005-08-06 08:16:04.000 | 8.922917    |

You can safely run this example here:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/amoffat/heimdallm/main)

or [view the read-only notebook](./notebooks/demo.ipynb)

# 📋 Explanation

So, what is actually happening above?

1. Unsafe free-form input is provided, presumably from some front end user interface.
1. That unsafe input is wrapped in a prompt envelope, producing a prompt with additional
   context to help an LLM produce a correct query.
1. The unsafe prompt is sent to an LLM of your choice, which then produces an unsafe
   SQL query.
1. The LLM response is parsed by a strict grammar which defines only the SQL features
   that are allowed.
1. If parsing succeeds, we know at the very least we're dealing with a valid SQL query
   albeit an untrusted one.
1. Different features of the parsed query are extracted for validation.
1. A soft validation pass is performed on the extracted features, and we potentially
   modify the query to be compliant, for example, to add a `LIMIT` clause, or to remove
   disallowed columns. See [reconstruction](TODO).
1. A hard validation pass is performed with your custom constraints to ensure that the
   query is only accessing allowed tables, columns, and functions, while containing
   required conditions. See [validation](TODO).
1. If validation succeeds, the resulting SQL query can then be sent to the database.
1. If validation fails, you'll see a helpful exception explaining exactly why.

# 🥽 Safety

I am in the process of organizing an independent security audit of HeimdaLLM. Until this
audit is complete, I do not recommend using HeimdaLLM against any production system
without a careful risk assessment. These audits are self-funded, so if you will get
value from the confidence that they bring, consider [sponsoring
me](https://github.com/sponsors/amoffat) or [inquire about interest in a commercial
license](https://forms.gle/frEPeeJx81Cmwva78).

To understand some of the potential vulnerabilities, take a look at the [attack surface
area](TODO) to see the risks and the mitigations.

# 📚 Database support

Currently, sqlite's flavor of SQL is supported. There is active development for the
other top relational SQL databases. To help me prioritize, please vote on which database
you would like to see supported:

[![Static Badge](https://img.shields.io/badge/Vote!-here-limegreen)](https://github.com/amoffat/HeimdaLLM/discussions/2)

# 📜 License

HeimdaLLM is dual-licensed for open-source or for commercial use.

## 🤝 Open-source license

The open-source license is [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.en.html),
which permits free usage, modification, and distribution, and is appropriate for
individual or open-source usage. For commercial usage, AGPLv3 has key obligations that
your organization may want to avoid:

- **Source Code Disclosure:** Any changes you make and use over a network must be made
  publicly available, potentially revealing your proprietary modifications.

- **Copyleft Clause:** If HeimdaLLM is integrated into your application, the whole
  application may need to adhere to AGPLv3 terms, including code disclosure of your
  application.

- **Service Providers:** If you use HeimdaLLM to provide services, your clients also
  need to abide by AGPLv3, complicating contracts.

## 📈 Commercial license

The commercial license eliminates the above restrictions, providing flexibility and
protection for your business operations. This commercial license is recommended for
commercial use. Please inquire about a commerical license here:

[![License Inquiry](https://img.shields.io/badge/License%20inquiry-blue)](https://forms.gle/frEPeeJx81Cmwva78)
