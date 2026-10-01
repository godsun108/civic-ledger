"""SQLite revision store. Configure CIVIC_LEDGER_DB to a durable mounted path in production."""
import os
import sqlite3
from pathlib import Path

def connect():
    path = os.environ.get("CIVIC_LEDGER_DB", "civic-ledger.sqlite3")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""CREATE TABLE IF NOT EXISTS packets (
        id TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL,
        stored_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id, revision))""")
    return db
