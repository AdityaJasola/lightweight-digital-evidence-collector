"""SQLite access. All queries are parameterized."""
import sqlite3
import uuid
from datetime import datetime, timezone

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_code     TEXT NOT NULL UNIQUE,
    evidence_name     TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    stored_filename   TEXT NOT NULL UNIQUE,
    evidence_category TEXT NOT NULL,
    description       TEXT NOT NULL DEFAULT '',
    collected_by      TEXT NOT NULL,
    collected_at_utc  TEXT NOT NULL,
    file_size         INTEGER NOT NULL,
    sha256_hash       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS verification_logs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id         INTEGER NOT NULL,
    expected_hash       TEXT NOT NULL,
    actual_hash         TEXT,
    verification_status TEXT NOT NULL
        CHECK (verification_status IN ('MATCH', 'MISMATCH', 'MISSING')),
    verified_at_utc     TEXT NOT NULL,
    FOREIGN KEY (evidence_id) REFERENCES evidence (id)
);

CREATE INDEX IF NOT EXISTS idx_logs_evidence ON verification_logs (evidence_id);
"""


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(database_path):
    """Create tables if they do not exist yet."""
    conn = sqlite3.connect(database_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _new_code():
    return "EV-%s-%s" % (
        datetime.now(timezone.utc).strftime("%Y%m%d"),
        uuid.uuid4().hex[:6].upper(),
    )


def insert_evidence(name, original_filename, stored_filename, category,
                    description, collected_by, file_size, sha256_hash):
    """Insert a record and return its evidence code. Retries on a code clash."""
    conn = get_db()
    for _ in range(10):
        code = _new_code()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO evidence (evidence_code, evidence_name, "
                    "original_filename, stored_filename, evidence_category, "
                    "description, collected_by, collected_at_utc, file_size, "
                    "sha256_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (code, name, original_filename, stored_filename, category,
                     description, collected_by, utc_now(), file_size,
                     sha256_hash),
                )
            return code
        except sqlite3.IntegrityError as exc:
            if "evidence_code" not in str(exc):
                raise
    raise sqlite3.IntegrityError("Could not generate a unique evidence code")


def get_evidence(code):
    return get_db().execute(
        "SELECT * FROM evidence WHERE evidence_code = ?", (code,)
    ).fetchone()


def list_evidence(search=""):
    search = search.strip()
    if not search:
        return get_db().execute(
            "SELECT * FROM evidence ORDER BY collected_at_utc DESC, id DESC"
        ).fetchall()
    escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    like = "%" + escaped + "%"
    return get_db().execute(
        "SELECT * FROM evidence WHERE evidence_code LIKE ? ESCAPE '\\' "
        "OR evidence_name LIKE ? ESCAPE '\\' "
        "OR original_filename LIKE ? ESCAPE '\\' "
        "ORDER BY collected_at_utc DESC, id DESC",
        (like, like, like),
    ).fetchall()


def recent_evidence(limit=5):
    return get_db().execute(
        "SELECT * FROM evidence ORDER BY collected_at_utc DESC, id DESC LIMIT ?",
        (limit,),
    ).fetchall()


def count_evidence():
    return get_db().execute("SELECT COUNT(*) FROM evidence").fetchone()[0]


def count_verifications():
    return get_db().execute("SELECT COUNT(*) FROM verification_logs").fetchone()[0]


def add_verification(evidence_id, expected_hash, actual_hash, status):
    conn = get_db()
    with conn:
        conn.execute(
            "INSERT INTO verification_logs (evidence_id, expected_hash, "
            "actual_hash, verification_status, verified_at_utc) "
            "VALUES (?, ?, ?, ?, ?)",
            (evidence_id, expected_hash, actual_hash, status, utc_now()),
        )


def list_verifications(evidence_id):
    return get_db().execute(
        "SELECT * FROM verification_logs WHERE evidence_id = ? "
        "ORDER BY id DESC",
        (evidence_id,),
    ).fetchall()
