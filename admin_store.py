"""Persistent on-disk settings store for admin panel state."""
import os
import sqlite3
import threading
import time
from uuid import uuid4

import config

_DB_LOCK = threading.Lock()
_SETTINGS_TABLE = "admin_settings"
_SESSIONS_TABLE = "admin_sessions"


def _connect() -> sqlite3.Connection:
    db_path = config.ADMIN_DB_PATH
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def initialize_admin_store() -> None:
    """Create settings DB and seed defaults when missing."""
    with _DB_LOCK:
        with _connect() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_SETTINGS_TABLE} (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_SESSIONS_TABLE} (
                    token TEXT PRIMARY KEY,
                    expires_at INTEGER NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            now = int(time.time())
            conn.execute(
                f"INSERT OR IGNORE INTO {_SETTINGS_TABLE} (key, value, updated_at) VALUES (?, ?, ?)",
                ("banner_enabled", "1" if config.ENABLE_CTF_INFO_BANNER else "0", now),
            )
            conn.execute(
                f"INSERT OR IGNORE INTO {_SETTINGS_TABLE} (key, value, updated_at) VALUES (?, ?, ?)",
                ("banner_message", config.CTF_INFO_BANNER_TEXT, now),
            )
            conn.execute(
                f"INSERT OR IGNORE INTO {_SETTINGS_TABLE} (key, value, updated_at) VALUES (?, ?, ?)",
                ("banner_version", str(uuid4()), now),
            )
            conn.commit()


def prune_admin_sessions() -> None:
    """Remove expired admin sessions from persistent store."""
    initialize_admin_store()
    now = int(time.time())
    with _DB_LOCK:
        with _connect() as conn:
            conn.execute(
                f"DELETE FROM {_SESSIONS_TABLE} WHERE expires_at <= ?",
                (now,),
            )
            conn.commit()


def create_admin_session(token: str, expires_at: int) -> None:
    """Create or replace an admin session token in persistent store."""
    initialize_admin_store()
    with _DB_LOCK:
        with _connect() as conn:
            conn.execute(
                f"""
                INSERT INTO {_SESSIONS_TABLE} (token, expires_at, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(token) DO UPDATE SET
                    expires_at=excluded.expires_at,
                    created_at=excluded.created_at
                """,
                (token, int(expires_at), int(time.time())),
            )
            conn.commit()


def is_admin_session_valid(token: str) -> bool:
    """Check whether an admin session token exists and is not expired."""
    if not token:
        return False

    prune_admin_sessions()
    with _DB_LOCK:
        with _connect() as conn:
            row = conn.execute(
                f"SELECT expires_at FROM {_SESSIONS_TABLE} WHERE token = ?",
                (token,),
            ).fetchone()
    if not row:
        return False
    return int(row[0]) > int(time.time())


def delete_admin_session(token: str) -> None:
    """Delete a single admin session token from persistent store."""
    if not token:
        return
    initialize_admin_store()
    with _DB_LOCK:
        with _connect() as conn:
            conn.execute(
                f"DELETE FROM {_SESSIONS_TABLE} WHERE token = ?",
                (token,),
            )
            conn.commit()


def get_setting(key: str, default: str) -> str:
    """Fetch a setting by key from the admin store."""
    initialize_admin_store()
    with _DB_LOCK:
        with _connect() as conn:
            row = conn.execute(
                f"SELECT value FROM {_SETTINGS_TABLE} WHERE key = ?",
                (key,),
            ).fetchone()
    if not row:
        return default
    return str(row[0])


def set_setting(key: str, value: str) -> None:
    """Set or update a setting value in the admin store."""
    initialize_admin_store()
    with _DB_LOCK:
        with _connect() as conn:
            conn.execute(
                f"""
                INSERT INTO {_SETTINGS_TABLE} (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value,
                    updated_at=excluded.updated_at
                """,
                (key, value, int(time.time())),
            )
            conn.commit()


def get_banner_settings() -> tuple[bool, str, str]:
    """Read persisted banner enabled state, message, and version."""
    enabled_raw = get_setting("banner_enabled", "1" if config.ENABLE_CTF_INFO_BANNER else "0")
    message = get_setting("banner_message", config.CTF_INFO_BANNER_TEXT)
    version = get_setting("banner_version", str(uuid4()))
    enabled = enabled_raw.strip().lower() in {"1", "true", "yes", "on"}
    return enabled, message, version


def set_banner_settings(enabled: bool, message: str) -> None:
    """Persist banner enabled state and message."""
    set_setting("banner_enabled", "1" if enabled else "0")
    set_setting("banner_message", message)


def rotate_banner_version() -> str:
    """Rotate banner visibility version so dismissed banners reappear."""
    new_version = str(uuid4())
    set_setting("banner_version", new_version)
    return new_version
