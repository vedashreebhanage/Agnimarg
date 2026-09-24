"""SQLite-backed audit log — per the Prototype Plan's 'basic audit logs'
security minimum. A real deployment would use managed Postgres (per that same
doc); SQLite is enough to give the demo a real durable audit trail across
server restarts tonight, with zero extra infra or accounts to set up.
"""
import json
import os
import sqlite3
import time

DB_PATH = os.environ.get(
    "AGNIMARG_AUDIT_DB_PATH", os.path.join(os.path.dirname(__file__), "data", "audit.db")
)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL
        )
        """
    )
    return conn


def record(action: str, actor: str, details: dict | None = None) -> dict:
    ts = time.time()
    details = details or {}
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO audit_log (timestamp, actor, action, details) VALUES (?, ?, ?, ?)",
            (ts, actor, action, json.dumps(details)),
        )
        seq = cur.lastrowid
    return {"seq": seq, "timestamp": ts, "actor": actor, "action": action, "details": details}


def all_entries() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT seq, timestamp, actor, action, details FROM audit_log ORDER BY seq").fetchall()
    return [
        {"seq": r[0], "timestamp": r[1], "actor": r[2], "action": r[3], "details": json.loads(r[4])}
        for r in rows
    ]
