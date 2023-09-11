🛡️ Safely executing LLM-generated SQL
=====================================

.. image:: https://img.shields.io/badge/Upvote%20on%20HN-ff6600.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAABhWlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AYht+2SlUqCu0g4pChOlkRFXHUKhShQqgVWnUwufQPmjQkKS6OgmvBwZ/FqoOLs64OroIg+APi6uKk6CIlfpcUWsR4x3EP733vy913gL9eZqrZMQ6ommWkEnEhk10Vgq/ophnGGPolZupzopiE5/i6h4/vdzGe5V335+hVciYDfALxLNMNi3iDeHrT0jnvE0dYUVKIz4lHDbog8SPXZZffOBcc9vPMiJFOzRNHiIVCG8ttzIqGSjxFHFVUjfL9GZcVzluc1XKVNe/JXxjKaSvLXKc1hAQWsQQRAmRUUUIZFmK0a6SYSNF53MM/6PhFcsnkKoGRYwEVqJAcP/gf/O6tmZ+ccJNCcaDzxbY/hoHgLtCo2fb3sW03ToDAM3CltfyVOjDzSXqtpUWPgL5t4OK6pcl7wOUOMPCkS4bkSAFa/nweeD+jb8oC4VugZ83tW/Mcpw9AmnqVvAEODoGRAmWve7y7q71v/9Y0+/cDaTFyo01kSV8AAAAGYktHRAD/AP8A/6C9p5MAAAAJcEhZcwAALiMAAC4jAXilP3YAAAAHdElNRQfnCQkUMwK2x6PRAAAAGXRFWHRDb21tZW50AENyZWF0ZWQgd2l0aCBHSU1QV4EOFwAAALxJREFUOMtj/P///38GKgIWBgYGBoY6deqY1nQTaiADAwPDy1uUGcYrxsDAwMDAxEBlQEcD4+czMBTvZ2AQVkCICStAxOLnk2Hg7YMMDGoODAyW8Qgxy3iI2PGFZBh4bAEDw9sHDAxWCQhX+jZAxG4dIJBscIEFiRAvIrtyQSIR6RAXuHUA4lKYK28dwOs64mJ5SyPRriPsQgYGSJgh48GTDgeLgSxEqSIiMkgzkIjIoIOXoeUZpYCR2lUAAM9jNTfnrPBaAAAAAElFTkSuQmCC
    :target: https://news.ycombinator.com/item?id=37463987
    :alt: Hackernews post


LLMs are surprisingly good at generating SQL from natural-language prompts. When given
the schema of a database and a few guiding instructions, LLMs can construct
reasonably-complex SQL queries that answer natural language questions about the data in
a database.

Consider this natural language query:

.. code-block:: text

    what are some popular al pacino movies?

When given that query and the schema of a movie database, an LLM constructs the
following response:

.. code-block:: sql

    SELECT
        movies.title,
        movies.imdb_id,
        movies.description
    FROM movies
    JOIN "cast" ON "cast".movie_id=movies.id
    JOIN people ON people.id="cast".person_id
    WHERE 
        movies.popularity > 0.5
        AND people.name='Al Pacino'
    ORDER BY movies.popularity DESC
    LIMIT 5;

When executed, the SQL query correctly returns some popular Al Pacino movies. Hoo-ah!
This mapping of natural language to SQL can be very powerful, and, for internal use in a
safe environment, with trusted users, the risks it carries can be justified.

But what if you wanted to give untrusted end-users this same kind of access to your
database? If your immediate reaction isn't one of horror 😱, then you probably aren't
fully considering the consequences! For starters, how do you ensure that the LLM isn't
tricked into generating harmful queries? Can you even identify a harmful query
reliably? How do you ensure that untrusted users can only see their data, and not
everyone's data? How do you prevent the execution of performance-degrading functions,
like `pg_sleep(999999) <https://www.postgresql.org/docs/current/functions-datetime.html#FUNCTIONS-DATETIME-DELAY>`_?

The stakes are high and failure can be catastrophic.

☠️ The risks
************

Not only is the structure of your database at risk, but your data security as well. If
an attacker can trick an LLM into producing any desired query, then they can do anything
from dropping tables and deleting rows to exfiltrating PII and other private
information. The results to your application can be disastrous, including:

* Account hijacking
* Stolen passwords
* Stolen private information, PII, and PHI
* Database destruction (dropped tables, columns, rows)

Just imagine all the horrible things that an attacker could do if given direct
read/write access to your database, then ask yourself: are these risks worth it?

.. image:: /images/grail.jpg
  :alt: Indiana Jones holding the Holy Grail

🌄 The rewards
**************

While the risks are high, so are the rewards. Tech workers spend a staggering number of
design & development hours making complex, custom UIs & API endpoints that serve
primarily as elaborate frontends to a database. These bespoke components often carry
enormous complexity, both in their ever-changing dependencies, and in the management of
tech debt that accrues naturally over time.

The components can look something like this:

* Complex frontend form UI for each relevant platform (mobile, web, etc).
* Responsive design to support many device sizes and orientations.
* Frontend visual regression test cases to ensure form looks correct.
* Frontend integration test cases to ensure form submits data correctly.
* Frontend error handling.
* A data interface/contract for the shape of the data submitted to the backend.
* A backend API endpoint to handle data submission.
* Authorization checks on the user submitting the data.
* Data validators to ensure that the submitted data is the correct shape and contains
  valid values.
* An ORM layer that translates form values into a valid SQL query.
* Unpacking the results of the query into something that can be serialized to the frontend.
* Backend error handling.
* Backend integration tests on the new API endpoint.
* Frontend response rendering to show the results.

Reducing this complexity by even 10% would have an enormous impact on the overall
maintainability of software. Until LLMs, there hasn't been a way to interface with
databases using natural language, but now that this technology exists, we have the
option to simplify many of the aforementioned steps.

But how to do it safely?

🧩 The solutions
****************

Solutions for executing untrusted, LLM-generated SQL safely span a broad range of
complexity, safety, and capability. We'll use the following properties to rate each
solution:

+------------------+------------------------------------------------------+
| Property         | Description                                          |
+==================+======================================================+
| Complexity       | How difficult is it to implement or integrate?       |
+------------------+------------------------------------------------------+
| Database safety  | How well does it protect against                     |
|                  | destructive queries?                                 |
+------------------+------------------------------------------------------+
| Data security    | How well does it restrict access to unauthorized     |
|                  | data?                                                |
+------------------+------------------------------------------------------+
| Flexibility      | How well can it handle valid but unanticipated       |
|                  | queries?                                             |
+------------------+------------------------------------------------------+
| Maintenance      | How much effort does it require to maintain?         |
+------------------+------------------------------------------------------+
| Cost             | What is the relative monetary cost of this solution? |
+------------------+------------------------------------------------------+
| Portability      | Can this solution be used with different databases?  |
+------------------+------------------------------------------------------+
| Failure          | What is the perceived likelihood that this solution  |
| probability      | will fail?                                           |
+------------------+------------------------------------------------------+
| Theoretically    | Can this solution ever fully solve the problem?      |
| complete         |                                                      |
+------------------+------------------------------------------------------+


🔒 Read-only db user
--------------------

.. figure:: /images/ghost.jpg

    "You can't push it with your finger, you're dead!"

The first obvious solution to limiting dangerous SQL queries is to create a read-only
database user. By using this RO user, untrusted queries cannot mutate your database or
your data. However, a RO user can still see all of the data in the database, making it
useless for data security.

It's a low cost solution that eliminates one class of problems with very little effort
or maintenance. This solution is generally recommended *in addition* to other solutions,
but it is not a viable solution on its own.

+----------------------+-------+--------------------------------------------------------------------------+
| Property             | Rank  | Rationale                                                                |
+======================+=======+==========================================================================+
| Complexity           | ✅    | A simple database change is required.                                    |
+----------------------+-------+--------------------------------------------------------------------------+
| Database safety      | ✅    | Read-only users cannot mutate the database.                              |
+----------------------+-------+--------------------------------------------------------------------------+
| Data security        | ❌    | Read-only users can still see restricted data.                           |
+----------------------+-------+--------------------------------------------------------------------------+
| Flexibility          | ✅    | End users can construct many kinds of queries.                           |
+----------------------+-------+--------------------------------------------------------------------------+
| Maintenance          | ✅    | Nothing to maintain.                                                     |
+----------------------+-------+--------------------------------------------------------------------------+
| Cost                 | ✅    | A read-only user is free.                                                |
+----------------------+-------+--------------------------------------------------------------------------+
| Portability          | ✅    | All serious databases have the concept of read-only users.               |
+----------------------+-------+--------------------------------------------------------------------------+
| Failure probability  | ✅    | Would require a bug in the database.                                     |
+----------------------+-------+--------------------------------------------------------------------------+
| Theoretically        | ❌    | It can never protect the contents of your database.                      |
| complete             |       |                                                                          |
+----------------------+-------+--------------------------------------------------------------------------+



🚷 Restricted db user
---------------------

.. figure:: /images/truman.jpg

    "Oh, Truman. You know you can't drive over water."

A stricter variation of the read-only user solution, this involves defining extra
database-level permissions to the database user. In addition to providing read-only
access, a restricted user may also provide RO access only to specific tables, and
specific columns in those tables (if supported by the database).

It is a broad brush solution, and while it is good at preventing general access to data
that nobody should be able to see, it cannot be used to restrict a query based on the
values held in columns. This means that in order to say "a user cannot see orders that
don't belong to them," you must say that the user cannot access the orders table at all,
which can be overly restrictive.

+-----------------------+--------+---------------------------------------------------------------------------------------+
| Property              | Rank   | Rationale                                                                             |
+=======================+========+=======================================================================================+
| Complexity            | ⚠️     | Varies based on database engine.                                                      |
+-----------------------+--------+---------------------------------------------------------------------------------------+
| Database safety       | ✅     | The database enforces what actions this user may perform.                             |
+-----------------------+--------+---------------------------------------------------------------------------------------+
| Data security         | ⚠️     | The database enforces what tables and columns may be used.                            |
+-----------------------+--------+---------------------------------------------------------------------------------------+
| Flexibility           | ❌     | No fine-grained controls.                                                             |
+-----------------------+--------+---------------------------------------------------------------------------------------+
| Maintenance           | ✅     | Once set, minimal maintenance required.                                               |
+-----------------------+--------+---------------------------------------------------------------------------------------+
| Cost                  | ✅     | It's free.                                                                            |
+-----------------------+--------+---------------------------------------------------------------------------------------+
| Portability           | ⚠️     | Different databases have varying levels of permissions.                               |
+-----------------------+--------+---------------------------------------------------------------------------------------+
| Failure probability   | ✅     | Would require a bug or misconfiguration in the database.                              |
+-----------------------+--------+---------------------------------------------------------------------------------------+
| Theoretically complete| ❌     | It cannot restrict based on the contents of data.                                     |
+-----------------------+--------+---------------------------------------------------------------------------------------+


🔐 Row-level security
---------------------

.. figure:: /images/gattaca.jpg
  
    "What about the interview?"

Row-level security (RLS) is a database-level security mechanism that allows queries to
be constrained based on the values of the rows that they are accessing. This can be used
to ensure that all returned rows have a column with a specific value, like the user's
id. If the RLS rules pass, the row is included in the results. If the RLS rules fail,
the row is excluded from the results. This filtering happens transparently, without
the user's knowledge.

Not all databases support RLS, nor do they support it in a consistent way. Furthormore,
RLS rule syntax can be complex, especially when trying to enforce complicated
constraints across many tables.

+-----------------------+--------+-----------------------------------------------------------------------------+
| Property              | Rank   | Rationale                                                                   |
+=======================+========+=============================================================================+
| Complexity            | ❌     | Configuring RLS for every table is non-trivial.                             |
+-----------------------+--------+-----------------------------------------------------------------------------+
| Database safety       | ❌     | RLS does not protect against DDL.                                           |
+-----------------------+--------+-----------------------------------------------------------------------------+
| Data security         | ✅     | Rules are enforced by the database.                                         |
+-----------------------+--------+-----------------------------------------------------------------------------+
| Flexibility           | ✅     | A broad scope of queries can be protected by RLS.                           |
+-----------------------+--------+-----------------------------------------------------------------------------+
| Maintenance           | ❌     | New rules required as schemas change.                                       |
+-----------------------+--------+-----------------------------------------------------------------------------+
| Cost                  | ✅     | It's free.                                                                  |
+-----------------------+--------+-----------------------------------------------------------------------------+
| Portability           | ❌     | RLS support is not part of an SQL standard.                                 |
+-----------------------+--------+-----------------------------------------------------------------------------+
| Failure probability   | ⚠️     | The complexity makes it easy to misconfigure.                               |
+-----------------------+--------+-----------------------------------------------------------------------------+
| Theoretically complete| ❌     | Requires another solution to protect against DDL.                           |
+-----------------------+--------+-----------------------------------------------------------------------------+


🤖 AI guards
------------

.. figure:: /images/bridge-of-death.jpg

    "An African or European swallow?"

An AI guard is a system of prompt augmentation and AI post-processing on untrusted
input. The purpose is to constrain the untrusted input to stay within some boundaries,
or to ensure that the input does not attempt to reveal some information. Think of it as
an assistant that looks at input skeptically to see if it is being tricked into doing
something that it has been instructed not to do. `See a live demo.
<https://gandalf.lakera.ai/>`_

In the context of SQL safety, an AI guard may be instructed to not allow certain tables
or columns to be mentioned in parts of the query, although I am not aware of any system
that currently offers this.

These systems are generally considered to be SOTA for prompt security, and while at
first glance they appear impressive, they are `trivially bypassed
<https://news.ycombinator.com/item?id=35905876>`_ by creative attackers, making them
ineffective at guarding information or enforcing constraints.


+------------------------+---------+----------------------------------------------------------------+
| Property               | Rank    | Rationale                                                      |
+========================+=========+================================================================+
| Complexity             | ⚠️      | May need many custom rules to provide some safety.             |
+------------------------+---------+----------------------------------------------------------------+
| Database safety        | ⚠️      | Unknown safety.                                                |
+------------------------+---------+----------------------------------------------------------------+
| Data security          | ⚠️      | Unknown security.                                              |
+------------------------+---------+----------------------------------------------------------------+
| Flexibility            | ❌      | Guards may be overzealous in their attempts to be secure.      |
+------------------------+---------+----------------------------------------------------------------+
| Maintenance            | ✅      | Managed SaaS solutions require less maintenance.               |
+------------------------+---------+----------------------------------------------------------------+
| Cost                   | ❌      | SaaS solutions are not free.                                   |
+------------------------+---------+----------------------------------------------------------------+
| Portability            | ✅      | Can hypothetically process any SQL dialect.                    |
+------------------------+---------+----------------------------------------------------------------+
| Failure probability    | ❌      | Trivial to trick.                                              |
+------------------------+---------+----------------------------------------------------------------+
| Theoretically complete | ❌      | Will always be a cat-and-mouse game with attackers.            |
+------------------------+---------+----------------------------------------------------------------+


Examples
^^^^^^^^

* `Lakera Guard <https://www.lakera.ai/>`_


🐑 Cloned db views
------------------

.. figure:: /images/sam-gerty.jpg
  
    "Gerty, am I clone?"

A cloned database view is some representation of your database that has been
post-processed to only contain data that the user is allowed to see. This representation
would typically be in the form of a separate user-specific sqlite database file. Because
the cloned database only contains data that is theirs, a user may issue any query
against it, and there is no risk to data security. And if a malicious user was able to
issue a DDL statement, it would only affect their cloned database.

To make this system work, each user needs their own processed view of the data that
they're allowed to access. Schema changes to the primary database will need to propagate
downwards to all user databases, and some system will need to determine when to
regenerate a user's database when their rows change. User-owned data, like id columns,
would also need to be obfuscated during this generation step, because the LLM may need
these columns for JOINs, but you probably don't want your users knowing the record's
authoritative id.

+-----------------------+---------+---------------------------------------------------------------------------+
| Property              | Rank    | Rationale                                                                 |
+=======================+=========+===========================================================================+
| Complexity            | ❌      | Requires a system to create cloned databases.                             |
+-----------------------+---------+---------------------------------------------------------------------------+
| Database safety       | ✅      | Mutations of cloned database aren't shared.                               |
+-----------------------+---------+---------------------------------------------------------------------------+
| Data security         | ✅      | Users can only access their own data.                                     |
+-----------------------+---------+---------------------------------------------------------------------------+
| Flexibility           | ❌      | Devs must anticipate access patterns in advance.                          |
+-----------------------+---------+---------------------------------------------------------------------------+
| Maintenance           | ❌      | Changes in access patterns require regenerating views.                    |
+-----------------------+---------+---------------------------------------------------------------------------+
| Cost                  | ⚠️      | Extra infra required to host and maintain cloned dbs.                     |
+-----------------------+---------+---------------------------------------------------------------------------+
| Portability           | ✅      | All databases engines can be dumped.                                      |
+-----------------------+---------+---------------------------------------------------------------------------+
| Failure probability   | ✅      | Failure would require privileged data to land in cloned dbs.              |
+-----------------------+---------+---------------------------------------------------------------------------+
| Theoretically complete| ✅      | A cloned db is a secure sandbox for queries.                              |
+-----------------------+---------+---------------------------------------------------------------------------+



🧠 Constraint validation
------------------------

.. figure:: /images/smiley.jpg

    "Where did it come from? What's the access?"


Constraint validation uses a real grammar to parse SQL queries into an AST. Static
analysis can then be performed on this parse tree to determine which tables and columns
are being used, how they're being used, if required conditions are present, and a range
of other features.

Additionally, these frameworks may automatically add nodes or replace nodes on the AST
to help ensure the SQL query conforms to constraint validation. In other words, the
query may be automatically edited to be compliant. Examples of this are to ensure a
correct ``LIMIT`` on the query, or remove a forbidden column from the ``SELECT``.

These frameworks can be treated as denylists or allowlists. You can list which tables,
columns, joins, and functions are allowed, or which are denied. This allows for a higher
degree of flexibility in the valid queries that an LLM may generate.

The risks of these frameworks are in the grammar and parsing. SQL is a complex spec and
each database type has its own quirks. Accounting for every way that a query can be
exploited is a tedious and complicated task, and so 0-days may exist that very dedicated
attackers will find. However, each bug and regression can be added to automated testing
to help converge on a robust solution.

+-----------------------+--------+-----------------------------------------------------------+
| Attribute             | Rank   | Rationale                                                 |
+=======================+========+===========================================================+
| Complexity            | ⚠️     | Configuring the validator can have some complexity.       |
+-----------------------+--------+-----------------------------------------------------------+
| Database safety       | ✅     | Harmful queries are stopped by the grammar.               |
+-----------------------+--------+-----------------------------------------------------------+
| Data security         | ✅     | Insecure queries are stopped by the validator.            |
+-----------------------+--------+-----------------------------------------------------------+
| Flexibility           | ✅     | Constraints generally stay out of the way of queries.     |
+-----------------------+--------+-----------------------------------------------------------+
| Maintenance           | ✅     | Once configured, maintenance is minimal.                  |
+-----------------------+--------+-----------------------------------------------------------+
| Cost                  | ✅     | Open-source solutions exist.                              |
+-----------------------+--------+-----------------------------------------------------------+
| Portability           | ⚠️     | Grammar and validator must explicitly support db engine.  |
+-----------------------+--------+-----------------------------------------------------------+
| Failure probability   | ⚠️     | Tests can mitigate bugs, but SQL spec is complex.         |
+-----------------------+--------+-----------------------------------------------------------+
| Theoretically complete| ✅     | Can theoretically prevent all unsafe or invalid queries.  |
+-----------------------+--------+-----------------------------------------------------------+


Examples
^^^^^^^^

* `HeimdaLLM <https://github.com/amoffat/HeimdaLLM>`_

🤔 Conclusion
*************

Are these solutions worth pursuing? I strongly believe so. Natural language interfaces
are playing an increasing role in the future of UI and UX, and relational databases are
not going away any time soon. For them to work together effectively, tooling needs to
bridge the gap to make them safer.

The most promising solutions are cloned databases and constraint validators, because
they are theoretically complete solutions that can offer the highest levels of security.
They vary primarily in their complexity and flexibility: cloned databases views are a
high-complexity allowlist, while constraint validators are a low-complexity allowlist or
denylist.

Other, non-complete solutions should not be considered if you value the safety of your
data.

.. image:: https://img.shields.io/badge/Upvote%20on%20HN-ff6600.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAABhWlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AYht+2SlUqCu0g4pChOlkRFXHUKhShQqgVWnUwufQPmjQkKS6OgmvBwZ/FqoOLs64OroIg+APi6uKk6CIlfpcUWsR4x3EP733vy913gL9eZqrZMQ6ommWkEnEhk10Vgq/ophnGGPolZupzopiE5/i6h4/vdzGe5V335+hVciYDfALxLNMNi3iDeHrT0jnvE0dYUVKIz4lHDbog8SPXZZffOBcc9vPMiJFOzRNHiIVCG8ttzIqGSjxFHFVUjfL9GZcVzluc1XKVNe/JXxjKaSvLXKc1hAQWsQQRAmRUUUIZFmK0a6SYSNF53MM/6PhFcsnkKoGRYwEVqJAcP/gf/O6tmZ+ccJNCcaDzxbY/hoHgLtCo2fb3sW03ToDAM3CltfyVOjDzSXqtpUWPgL5t4OK6pcl7wOUOMPCkS4bkSAFa/nweeD+jb8oC4VugZ83tW/Mcpw9AmnqVvAEODoGRAmWve7y7q71v/9Y0+/cDaTFyo01kSV8AAAAGYktHRAD/AP8A/6C9p5MAAAAJcEhZcwAALiMAAC4jAXilP3YAAAAHdElNRQfnCQkUMwK2x6PRAAAAGXRFWHRDb21tZW50AENyZWF0ZWQgd2l0aCBHSU1QV4EOFwAAALxJREFUOMtj/P///38GKgIWBgYGBoY6deqY1nQTaiADAwPDy1uUGcYrxsDAwMDAxEBlQEcD4+czMBTvZ2AQVkCICStAxOLnk2Hg7YMMDGoODAyW8Qgxy3iI2PGFZBh4bAEDw9sHDAxWCQhX+jZAxG4dIJBscIEFiRAvIrtyQSIR6RAXuHUA4lKYK28dwOs64mJ5SyPRriPsQgYGSJgh48GTDgeLgSxEqSIiMkgzkIjIoIOXoeUZpYCR2lUAAM9jNTfnrPBaAAAAAElFTkSuQmCC
   :target: https://news.ycombinator.com/item?id=37463987
   :alt: Hackernews post