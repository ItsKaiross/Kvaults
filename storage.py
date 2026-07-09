import sqlite3
import json
import os
from cryptography.fernet import InvalidToken
from crypto import derive_key, new_salt

DB_FILE = "vault.db"


def _connect():
    return sqlite3.connect(DB_FILE)


def _init_db():
    with _connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                name      TEXT PRIMARY KEY,
                data      TEXT NOT NULL,
                created   TEXT DEFAULT (datetime('now')),
                modified  TEXT DEFAULT (datetime('now'))
            )
        """)


def vault_exists() -> bool:
    if not os.path.exists(DB_FILE):
        return False
    with _connect() as con:
        row = con.execute("SELECT value FROM meta WHERE key='salt'").fetchone()
    return row is not None


def unlock(master_password: str) -> tuple[dict, bytes]:
    _init_db()
    if not vault_exists():
        salt = new_salt()
        with _connect() as con:
            con.execute("INSERT OR REPLACE INTO meta VALUES ('salt', ?)",
                        (salt.hex(),))
        return {}, salt

    with _connect() as con:
        salt_hex = con.execute(
            "SELECT value FROM meta WHERE key='salt'").fetchone()[0]
        rows = con.execute(
            "SELECT name, data FROM entries").fetchall()

    salt   = bytes.fromhex(salt_hex)
    fernet = derive_key(master_password, salt)
    entries = {}
    try:
        for name, enc_data in rows:
            entries[name] = json.loads(fernet.decrypt(enc_data.encode()))
    except InvalidToken:
        raise ValueError("Wrong master password.")
    return entries, salt


def save_entry(name: str, data: dict, master_password: str, salt: bytes):
    _init_db()
    fernet    = derive_key(master_password, salt)
    enc_data  = fernet.encrypt(json.dumps(data).encode()).decode()
    with _connect() as con:
        con.execute("""
            INSERT INTO entries (name, data, created, modified)
            VALUES (?, ?, datetime('now'), datetime('now'))
            ON CONFLICT(name) DO UPDATE SET
                data     = excluded.data,
                modified = datetime('now')
        """, (name, enc_data))


def delete_entry(name: str):
    _init_db()
    with _connect() as con:
        con.execute("DELETE FROM entries WHERE name=?", (name,))


def save(entries: dict, master_password: str, salt: bytes):
    """Bulk save — syncs all entries to DB (used after import/restore)."""
    _init_db()
    fernet = derive_key(master_password, salt)
    with _connect() as con:
        con.execute("DELETE FROM entries")
        for name, data in entries.items():
            enc_data = fernet.encrypt(json.dumps(data).encode()).decode()
            con.execute(
                "INSERT INTO entries (name, data) VALUES (?, ?)",
                (name, enc_data))


def get_entry_dates() -> dict[str, dict]:
    """Returns {name: {created, modified}} for all entries."""
    _init_db()
    with _connect() as con:
        rows = con.execute(
            "SELECT name, created, modified FROM entries").fetchall()
    return {r[0]: {"created": r[1], "modified": r[2]} for r in rows}


def backup(path: str):
    """Copy the vault DB to a backup path."""
    import shutil
    shutil.copy2(DB_FILE, path)


def restore(path: str):
    """Replace the vault DB with a backup file."""
    import shutil
    shutil.copy2(path, DB_FILE)
