SQL
===

.. currentmodule:: heimdallm.bifrosts.sql.sqlite.select

Below are some of the ways that a SQL ``SELECT`` query can be vulnerable to attack in
HeimdaLLM. This is not intended to be an exhaustive list, but rather a starting point
for understanding the ways that a query can be vulnerable, and the controls that
HeimdaLLM has in place to mitigate these attacks.

The two primary points of mitigation are `the grammar
<https://github.com/amoffat/HeimdaLLM/blob/dev/heimdallm/bifrosts/sql/sqlite/select/grammar.lark>`_,
which defines if a query is syntactically correct, and the :class:`constraint validator
<validator.ConstraintValidator>`, which defines the constraints that the query must
satisfy. Some controls are implemented in the grammar, and some are in the constraint
validator. They work together to provide validation. For example, outer joins are
stopped at the grammar, while required conditions are checked at the constraint
validator.

.. DANGER::

    Have a concern about the topics on this page? Take a look at our
    `security policy <https://github.com/amoffat/HeimdaLLM/security/policy>`_ if you
    wish to contribute.

.. TIP::

    Want to test these attacks yourself? See the `Penetration Testing Notebook
    <https://github.com/amoffat/HeimdaLLM/blob/main/notebooks/pentest.ipynb>`_

Side-channel attacks
********************

Queries can be susceptible to `side-channel attacks
<https://en.wikipedia.org/wiki/Side-channel_attack>`_, like an `Oracle Attack
<https://en.wikipedia.org/wiki/Oracle_attack>`_. This is where an attacker can gather
information about your database, like restricted columns, by analyzing the differences
in the results of queries, and then incrementally refining their queries to get more
information.

Condition injection
-------------------

Even if a requester is not allowed to select a column, it is still possible to see the
value of that column if they are allowed to use it in a condition. To understand how
this works, consider the following query:

.. code-block:: sql

    SELECT user.username
    FROM users
    WHERE
        user.secret LIKE 'a%'
        AND user.user_id=123

Assume the attacker cannot select the ``secret`` column, but can use it in a condition.
This query allows them to determine the first letter of the ``secret`` column by observing
the results. They can then refine their query to discover subsequent letters until they
know the full contents of the column.

Conditions can also appear appended to a ``JOIN`` condition:

.. code-block:: sql

    SELECT user.username
    FROM users
    JOIN rentals
        ON rentals.user_id = user.user_id
        AND user.secret LIKE 'a%'
    WHERE
        user.user_id=123

The same goes with ``HAVING`` and ``GROUP BY``:

.. code-block:: sql

    SELECT user.username
    FROM users
    WHERE
        user.user_id=123
    GROUP BY user.secret
    HAVING user.secret LIKE 'a%'

They can also be effective in the ``ORDER BY``:

.. code-block:: sql
    
    SELECT user.user_id
    FROM users
    ORDER BY (substr(user.secret, 1, 1)='a') DESC

Mitigations
^^^^^^^^^^^

HeimdaLLM takes an overzealous approach to this problem by examining the parse tree for
any usage of a column in ``WHERE``, ``HAVING``, ``GROUP BY``, ``ORDER BY``, and
``JOIN``. Whether they are nested deep in an expression or not, HeimdaLLM will find
them. The resulting columns are then sent to the constraint validator's
:meth:`ConstraintValidator.condition_column_allowed
<validator.ConstraintValidator.condition_column_allowed>` predicate and either
allowed or denied. By using a broad application of the allowlist, we can prevent the use
of columns that can be used in side-channel attacks.

By default, HeimdaLLM will not allow the use of a column in a condition if it is not
allowed to be selected. This means that if they can't see it, they can't use it. While
this is a good default, it can be overly restrictive. You may choose to separate these
two allowlists, in which case your constraint validator would define one predicate for
:meth:`ConstraintValidator.select_column_allowed
<validator.ConstraintValidator.select_column_allowed>` and another for
:meth:`ConstraintValidator.condition_column_allowed
<validator.ConstraintValidator.condition_column_allowed>`.

Star select
-----------

An attacker could trick the LLM to ``SELECT *`` from a table. This could reveal more
columns than you intended.

Mitigations
^^^^^^^^^^^

HeimdaLLM does not allow ``*`` as a selectable column. It does, however, allow
``COUNT(*)``, since that is a very common way of counting rows, and it does not reveal
any additional information when a :meth:`requester identity
<validator.ConstraintValidator.requester_identities>` is also applied.

Optional conditions
-------------------

When required conditions are defined, either as a :meth:`requester identity
<validator.ConstraintValidator.requester_identities>`, or as some other
:meth:`parameterized constraint <validator.ConstraintValidator.parameterized_constraints>`, an
attacker may attempt to bypass the condition by coaxing the LLM to produce a query that
includes the condition as part of an ``OR`` clause. For example:

.. code-block:: sql

    SELECT user.email
    FROM users
    WHERE
        user.user_id=123
        OR 1=1

This query will return all rows in the table, because the ``OR 1=1`` condition is always
true. This simplified example is easy to spot, but it can be more difficult to spot
when the condition is more complex with nested expressions, for example:

.. code-block:: sql

    SELECT user.email
    FROM users
    WHERE
        1=1
        AND (
            1=1
            AND (
                user.user_id=123
                AND 1=1
            )
            OR 1=1 /* <------- UH OH */
        )
        AND 1=1

Here, the ``OR`` condition occurs at a different level than the required condition, making
the required condition's entire branch optional.

Mitigations
^^^^^^^^^^^

HeimdaLLM takes careful steps to ensure that required conditions are not executed
optionally. We do this by examining the tree of ``WHERE`` conditions and walking the tree
according to the following rules:

#. Start at the root of the ``WHERE`` clause.
#. Examine the immediate child conditions.
#. If any of the immediate child conditions are connected via ``OR``, all sibling nodes
   are tainted. Abort the current level and move to the previous level, or stop if the
   current level is the root.
#. If any of the immediate child conditions satisfy a required condition, mark that
   condition as satisfied.
#. If any unsatisfied required conditions remain, recurse into each child condition and
   goto step 2.

Another way to think about it is: the required condition and all of its sibling
conditions must be connected to the tree of ``WHERE`` conditions via ``AND``, and the same
for every ancestor node of the required condition. This guarantees that the requried
condition is always evaluated.

.. _outer-joins:

Outer-joins
-----------

Outer joins are considered harmful because they can be used to bypass conditions and
reveal information that should not be visible to the requester. Consider the following
query:

.. code-block:: sql
    
    SELECT user.user_id
    FROM users
    RIGHT JOIN purchases
        ON purchases.user_id = user.user_id
        AND user.user_id=123

Although the ``JOIN`` is an equi-join, and we have a required condition, it is not
sufficient to prevent the user from seeing rows they should not be able to see. This is
because the ``RIGHT JOIN`` will include every unmatched row in the right table,
including rows that do not belong to the user.

Mitigations
^^^^^^^^^^^

All outer joins are rejected by HeimdaLLM at the grammar level. The only joins which are
allowed are inner equi-joins.

Side effects
************

Mutating queries
----------------

This is where an attacker causes an LLM to produce a query that mutates the database,
such as an ``UPDATE`` or ``DELETE`` query.

You could also have a trigger that mutates the database on ``SELECT``, or a stored
function that a ``SELECT`` query calls. Both of those would have a side-effect.

Mitigations
^^^^^^^^^^^

HeimdaLLM's SQL grammar does not define support for any other query type besides
``SELECT``. This means that any other query type will be rejected by the parser. The
grammar also does not support ``SELECT INTO``. A vulnerability would need to be present
in the grammar that could allow for a mutation inside a ``SELECT`` query.

You will want to audit your database to ensure that no triggers are present on the
selectable tables. You will also want to audit your stored functions and ensure that
they are not allowlisted via the :meth:`ConstraintValidator.can_use_function
<validator.ConstraintValidator.can_use_function>` predicate.

Acquiring locks
---------------

An attacker could cause a query to contain ``SELECT FOR UPDATE``, which would result in
the database acquiring a lock on the rows that are returned. This can also happen
implicitly if your transaction isolation level is set to ``SERIALIZABLE`` or ``REPEATABLE
READ``.

Acquiring locks during a ``SELECT`` could cause problems if your connections are recycled
without rolling back or committing the transaction, because the lock would remain in
place.

Mitigations
^^^^^^^^^^^

HeimdaLLM's SQL grammar does not define the ``SELECT FOR UPDATE`` syntax, so explicit lock
acquisition is not possible. However, implicit lock acquisition is still possible based
on your isolation level, so you will want to ensure that your connection pool is
configured to rollback or commit connections that are returned to the pool.

Function execution
------------------

An attacker could execute a ``SELECT`` query that contains function that has side-effects,
such as ``sleep()``. This could be used to cause a denial of service attack or other
harmful behavior.

Mitigations
^^^^^^^^^^^

HeimdaLLM allows you to configure a function allowlist predicate, through
:meth:`ConstraintValidator.can_use_function
<validator.ConstraintValidator.can_use_function>`, which can be used to prevent the
execution of functions. We have chosen what we believe are sensible defaults, but you
may customize these in your subclassed constraint validator.

The detection of functions is done by examining the parse tree for function calls, and
the grammar has been defined to easily detect the usage of a function, no matter where
it appears in the query. This means that a fault in the grammar must exist for a
function to be executed undetected.