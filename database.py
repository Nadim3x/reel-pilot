"""
ReelPilot — featherweight SQLite helper.

Designed for a 256 MB container: a single lazily-created connection,
WAL journaling (so the dashboard and bot never block each other),
and startup schema self-healing that tolerates older or partially
created databases without manual migration.
"""

import logging
import sqlite3
import threading
import time
from typing import Any, Iterable

import config

logger = logging.getLogger(__name__)

_SCHEMA_VERSION: int = 2

_CONN: sqlite3.Connection | None = None
_LOCK = threading.Lock()

EXPECTED_COLUMNS: dict[str, tuple[tuple[str, str], ...]] = {
    "accounts": (
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("platform", "TEXT NOT NULL"),
        ("username", "TEXT NOT NULL"),
        ("session_data", "TEXT NOT NULL"),
        ("is_active", "INTEGER DEFAULT 1"),
        ("created_at", "TEXT DEFAULT (datetime('now'))"),
        ("last_used_at", "TEXT"),
    ),
    "users": (
        ("user_id", "INTEGER PRIMARY KEY"),
        ("username", "TEXT"),
        ("first_name", "TEXT"),
        ("photo_url", "TEXT"),
        ("status", "TEXT DEFAULT 'pending'"),
        ("created_at", "TEXT DEFAULT (datetime('now'))"),
    ),
    "stats": (
        ("key", "TEXT PRIMARY KEY"),
        ("value", "INTEGER DEFAULT 0"),
        ("updated_at", "TEXT DEFAULT (datetime('now'))"),
    ),
    "upload_log": (
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("platform", "TEXT"),
        ("username", "TEXT"),
        ("source_url", "TEXT"),
        ("status", "TEXT"),
        ("created_at", "TEXT DEFAULT (datetime('now'))"),
    ),
}

_INDEXES: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS idx_accounts_platform ON accounts(platform)",
    "CREATE INDEX IF NOT EXISTS idx_accounts_active ON accounts(is_active)",
    "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)",
    "CREATE INDEX IF NOT EXISTS idx_stats_key ON stats(key)",
    "CREATE INDEX IF NOT EXISTS idx_upload_log_created ON upload_log(created_at)",
)


def get_conn() -> sqlite3.Connection:
    """Return the process-wide connection (lazily created, thread-safe)."""
    global _CONN
    with _LOCK:
        if _CONN is None:
            conn = sqlite3.connect(
                str(config.DB_PATH),
                timeout=30,
                check_same_thread=False,
                isolation_level=None,  # autocommit; WAL keeps readers safe
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA cache_size=-2000")  # 2 MB page cache max
            _CONN = conn
        return _CONN


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not


def _columns(conn: sqlite3.Connection, table: str) -> list[tuple[str, str]]:
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    except sqlite3.Error:
        return []
    return [(row["name"], (row["type"] or "TEXT").upper()) for row in rows]


def _should_rebuild(conn: sqlite3.Connection, table: str) -> bool:
    """
    Self-healing: a table is rebuilt when it is missing entirely or when the
    stored schema is critically incompatible (e.g. an old 'password' column
    from pre-2FA days, or 'is_active' typed as TEXT in a legacy layout).
    Renaming the broken table preserves old rows for inspection instead of
    destroying data outright.
    """
    if not _table_exists(conn, table):
        return True
    cols = {name.upper(): dtype for name, dtype in _columns(conn, table)}
    if "PASSWORD" in cols and "SESSION_DATA" not in cols:
        return True  # legacy credentials layout predating this schema
    expected = {name.upper() for name, _ in EXPECTED_COLUMNS[table]}
    if "IS_ACTIVE" in expected and "IS_ACTIVE" in cols and cols["IS_ACTIVE"].startswith("TEXT"):
        return True
    return False


def init_db() -> sqlite3.Connection:
    """Create/repair every table and index. Safe to call on every startup."""
    conn = get_conn()
    with _LOCK:
        for table, columns in EXPECTED_COLUMNS.items():
            try:
                if _should_rebuild(conn, table):
                    backup_name = f"{table}_legacy_{int(time.time())}"
                    if _table_exists(conn, table):
                        conn.execute(f"ALTER TABLE {table} RENAME TO {backup_name}")
                        logger.warning(
                            "self-heal: renamed incompatible table %s -> %s", table, backup_name
                        )
                if not _table_exists(conn, table):
                    defs = ", ".join(f"{name} {dtype}" for name, dtype in columns)
                    conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({defs})")
                    # backfill rows preserved from a legacy layout
                    backup_name = f"{table}_legacy_%"
                    legacy = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
                        (backup_name,),
                    ).fetchone()
                    if legacy:
                        legacy_table = legacy["name"]
                        legacy_cols = {n.upper() for n, _ in _columns(conn, legacy_table)}
                        target_cols = {name.upper() for name, _ in columns}
                        shared = target_cols & legacy_cols
                        if shared:
                            names = ", ".join(sorted(shared))
                            conn.execute(
                                f"INSERT OR IGNORE INTO {table} ({names}) "
                                f"SELECT {names} FROM {legacy_table}"
                            )
                            conn.execute(f"DROP TABLE {legacy_table}")
                            logger.info("self-heal: migrated rows from %s", legacy_table)
            except sqlite3.Error as exc:  # pragma: no cover - defensive
                logger.error("self-heal failed for %s: %s", table, exc)
        for stmt in _INDEXES:
            try:
                conn.execute(stmt)
            except sqlite3.Error as exc:
                logger.error("index heal failed: %s", exc)
        set_stat("schema_version", _SCHEMA_VERSION)
    logger.info("database ready at %s (schema v%s)", config.DB_PATH, _SCHEMA_VERSION)
    return conn


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def query(sql: str, params: Iterable = ()) -> list[dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(sql, tuple(params))
    return [dict(r) for r in cur.fetchall()]


def query_one(sql: str, params: Iterable = ()) -> dict[str, Any] | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: Iterable = ()) -> int:
    conn = get_conn()
    cur = conn.execute(sql, tuple(params))
    return cur.lastrowid or cur.rowcount


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

def add_account(platform: str, username: str, session_data: str) -> int:
    return execute(
        "INSERT INTO accounts (platform, username, session_data, is_active) VALUES (?,?,?,1)",
        (platform, username, session_data),
    )


def all_accounts(active_only: bool = False) -> list[dict[str, Any]]:
    sql = "SELECT * FROM accounts"
    if active_only:
        sql += " WHERE is_active=1"
    return query(sql + " ORDER BY id")


def accounts_by_platform(platform: str, active_only: bool = True) -> list[dict[str, Any]]:
    sql = "SELECT * FROM accounts WHERE platform=?"
    if active_only:
        sql += " AND is_active=1"
    return query(sql + " ORDER BY id", (platform,))


def set_account_active(account_id: int, is_active: bool) -> None:
    execute("UPDATE accounts SET is_active=? WHERE id=?", (1 if is_active else 0, account_id))


def touch_account(account_id: int) -> None:
    execute(
        "UPDATE accounts SET last_used_at=datetime('now') WHERE id=?", (account_id,)
    )


def delete_account(account_id: int) -> None:
    execute("DELETE FROM accounts WHERE id=?", (account_id,))


def account_count() -> int:
    row = query_one("SELECT COUNT(*) AS n FROM accounts")
    return int(row["n"]) if row else 0


# ---------------------------------------------------------------------------
# Telegram users / approvals
# ---------------------------------------------------------------------------

def upsert_user(user_id: int, username: str | None, first_name: str | None,
                photo_url: str | None = None) -> str:
    """Insert the user if new; returns the (possibly existing) status."""
    conn = get_conn()
    existing = query_one("SELECT status FROM users WHERE user_id=?", (user_id,))
    if existing:
        if photo_url:
            execute(
                "UPDATE users SET photo_url=? WHERE user_id=?", (photo_url, user_id)
            )
        return existing["status"]
    execute(
        "INSERT INTO users (user_id, username, first_name, photo_url, status) "
        "VALUES (?,?,?,?, 'pending')",
        (user_id, username, first_name, photo_url),
    )
    return "pending"


def set_user_status(user_id: int, status: str) -> None:
    execute("UPDATE users SET status=? WHERE user_id=?", (status, user_id))


def get_user(user_id: int) -> dict[str, Any] | None:
    return query_one("SELECT * FROM users WHERE user_id=?", (user_id,))


def users_by_status(status: str) -> list[dict[str, Any]]:
    return query(
        "SELECT * FROM users WHERE status=? ORDER BY user_id DESC", (status,)
    )


def all_users() -> list[dict[str, Any]]:
    return query("SELECT * FROM users ORDER BY user_id DESC")


def approved_user_ids() -> list[int]:
    rows = query("SELECT user_id FROM users WHERE status='approved'")
    return [int(r["user_id"]) for r in rows]


# ---------------------------------------------------------------------------
# Stats (key-value counters)
# ---------------------------------------------------------------------------

def get_stat(key: str, default: int = 0) -> int:
    row = query_one("SELECT value FROM stats WHERE key=?", (key,))
    return int(row["value"]) if row else default


def set_stat(key: str, value: int) -> None:
    execute(
        "INSERT INTO stats (key, value, updated_at) VALUES (?,?,datetime('now')) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')",
        (key, int(value)),
    )


def bump_stat(key: str, by: int = 1) -> None:
    execute(
        "INSERT INTO stats (key, value, updated_at) VALUES (?,?,datetime('now')) "
        "ON CONFLICT(key) DO UPDATE SET value=value+excluded.value, updated_at=datetime('now')",
        (key, int(by)),
    )


# ---------------------------------------------------------------------------
# Upload log (community analytics shown on the guest dashboard)
# ---------------------------------------------------------------------------

def log_upload(platform: str, username: str, source_url: str, status: str) -> None:
    execute(
        "INSERT INTO upload_log (platform, username, source_url, status) "
        "VALUES (?,?,?,?)",
        (platform, username, source_url, status),
    )


def upload_count() -> int:
    row = query_one("SELECT COUNT(*) AS n FROM upload_log WHERE status='success'")
    return int(row["n"]) if row else 0


def active_creators() -> int:
    row = query_one(
        "SELECT COUNT(DISTINCT username) AS n FROM upload_log "
        "WHERE status='success' AND username IS NOT NULL AND username != ''"
    )
    return int(row["n"]) if row else 0


def is_approved(user_id: int) -> bool:
    if user_id == config.SUPER_ADMIN_ID:
        return True
    row = query_one("SELECT 1 AS ok FROM users WHERE user_id=? AND status='approved'", (user_id,))
    return row is not None
