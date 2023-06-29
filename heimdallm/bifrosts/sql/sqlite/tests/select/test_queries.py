"""
When we reconstruct queries from the AST, the constructed query needs to be semantically
identical. This tests that by comparing the reconstructed query to the original query
via the results they produce. The results are hashed and stored with the original query.
"""

import hashlib
import json
import re
import sqlite3
import time
from datetime import date
from pathlib import Path
from typing import Any, Optional

import pytest

from heimdallm.bifrosts.sql.sqlite.select.bifrost import SQLBifrost

from .utils import PermissiveConstraints

_THIS_DIR = Path(__file__).parent
_QUERY_DIR = _THIS_DIR / "queries"


def _load(name: str) -> tuple[str, Optional[str]]:
    """loads the sql query by name and returns a results hash, if one exists"""
    with open(_QUERY_DIR / name) as f:
        maybe_hash_line = f.readline()
        sql = f.read()
        res_hash = None
        if match := re.search(r"/\*(.*)\*/", maybe_hash_line):
            res_hash = match.group(1).strip()
        else:
            sql = maybe_hash_line + sql

        return sql, res_hash


def _add_hash(sql_name: str, res_hash: str) -> None:
    """adds a results hash to a sql query file that (presumably) doesn't have one.
    we don't check though."""
    with open(_QUERY_DIR / sql_name, "r+") as f:
        sql = f.read()
        f.seek(0)
        f.write(f"/* {res_hash} */\n")
        f.write(sql)


def _calc_res_hash(res: Any) -> str:
    return hashlib.sha256(json.dumps(res, sort_keys=True).encode()).hexdigest()


def _execute(conn: sqlite3.Connection, query: str) -> Any:
    now = date.fromisoformat("2005-09-05")
    params = {"timestamp": time.mktime(now.timetuple()), "customer_id": 148}
    cur = conn.cursor()
    cur.execute(query, params)
    res = cur.fetchall()
    return res


def test_query(conn: sqlite3.Connection, sql_name: str):
    query, correct_hash = _load(sql_name)
    res = _execute(conn, query)
    actual_hash = _calc_res_hash(res)

    if correct_hash is None:
        _add_hash(sql_name, actual_hash)
        pytest.fail(f"Verify results and re-run test: {res!r}")

    # first confirm that our results match the expected hash.
    # this is a sanity check.
    assert actual_hash == correct_hash

    # now we're going to reconstruct the query, execute it, and confirm that the results
    # are the same.
    bifrost = SQLBifrost.mocked(PermissiveConstraints())
    reconstructed_query = bifrost.traverse(query, autofix=True)
    reconstructed_res = _execute(conn, reconstructed_query)
    reconstructed_hash = _calc_res_hash(reconstructed_res)
    assert reconstructed_hash == correct_hash


# parametrizes our test functions based on the contents of the `_QUERY_DIR` directory
def pytest_generate_tests(metafunc):
    def pred(f: Path):
        return f.is_file() and f.name.endswith(".sql")

    if "sql_name" in metafunc.fixturenames:
        files = [f.name for f in _QUERY_DIR.iterdir() if pred(f)]
        metafunc.parametrize("sql_name", files)
