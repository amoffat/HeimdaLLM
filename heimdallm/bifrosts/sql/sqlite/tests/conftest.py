import hashlib
import sqlite3
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent.parent.parent
_DB_FILE = _REPO_ROOT / "notebooks" / "sakila.sqlite3"


def sha256sum(filename):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, "rb", buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()


@pytest.fixture()
def conn():
    starting_hash = sha256sum(_DB_FILE)
    _conn = sqlite3.connect(_DB_FILE)
    yield _conn
    _conn.close()
    # ensure that no test is manipulating our database
    ending_hash = sha256sum(_DB_FILE)
    assert starting_hash == ending_hash
