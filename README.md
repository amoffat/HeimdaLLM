# HeimdaLLM

Pronounced `[ˈhaɪm.dɔl.əm]` or _HEIM-dall-EM_

HeimdaLLM is a robust static analysis framework for validating that LLM-generated
structured output is safe. It currently supports SQL.

In simple terms, it helps makes sure that AI won't wreck your systems.

[![Heimdall](https://raw.githubusercontent.com/amoffat/HeimdaLLM/main/docs/source/images/heimdall.png)](https://heimdallm.ai)
[![Build status](https://github.com/amoffat/HeimdaLLM/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/amoffat/HeimdaLLM/actions)
[![Docs](https://img.shields.io/badge/Documentation-purple.svg)](https://docs.heimdallm.ai)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/amoffat)](https://github.com/sponsors/amoffat)
[![PyPI](https://img.shields.io/pypi/v/heimdallm)](https://pypi.org/project/heimdallm/)
[![License: Commercial](https://img.shields.io/badge/License-Commercial-blue.svg)](https://forms.gle/frEPeeJx81Cmwva78)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Coverage Status](https://coveralls.io/repos/github/amoffat/HeimdaLLM/badge.svg?branch=dev)](https://coveralls.io/github/amoffat/HeimdaLLM?branch=dev)

Consider the following natural-language database query:

```
how much have i spent renting movies, broken down by month?
```

From this query (and a little bit of context), an LLM can produce the following SQL
query:

```sql
SELECT
   strftime('%Y-%m', payment.payment_date) AS month,
   SUM(payment.amount) AS total_amount
FROM payment
JOIN rental ON payment.rental_id=rental.rental_id
JOIN customer ON payment.customer_id=customer.customer_id
WHERE customer.customer_id=:customer_id
GROUP BY month
LIMIT 10;
```

But how can you ensure the LLM-generated query is safe and that it only accesses
authorized data?

HeimdaLLM performs static analysis on the generated SQL to ensure that only certain
columns, tables, and functions are used. It also automatically edits the query to add a
`LIMIT` and to remove forbidden columns. Lastly, it ensures that there is a column
constraint that would restrict the results to only the user's data.

It does all of this locally, without AI, using good ol' fashioned grammars and parsers:

```
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
```

The validated query can then be executed:

| month   | total_amount |
| ------- | ------------ |
| 2005-05 | 4.99         |
| 2005-06 | 22.95        |
| 2005-07 | 100.78       |
| 2005-08 | 87.82        |

Want to get started quickly? Go
[here](https://docs.heimdallm.ai/en/latest/quickstart/index.html).

# 🥽 Safety

I am in the process of organizing an independent security audit of HeimdaLLM. Until this
audit is complete, I do not recommend using HeimdaLLM against any production system
without a careful risk assessment. These audits are self-funded, so if you will get
value from the confidence that they bring, consider [sponsoring
me](https://github.com/sponsors/amoffat) or [inquire about interest in a commercial
license](https://forms.gle/frEPeeJx81Cmwva78).

To understand some of the potential vulnerabilities, take a look at the [attack
surface](https://docs.heimdallm.ai/en/latest/attack-surface.html) to see the risks and
the mitigations.

# 📚 Database support

- Sqlite
- MySQL
- Postgres

There is active development for the other top relational SQL databases. To help me
prioritize, please vote on which database you would like to see supported:

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
