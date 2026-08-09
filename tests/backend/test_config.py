"""
Regression tests for backend configuration.

Covers the SQLite relative-path resolution that previously made the web
backend fail to start when launched from the backend/ directory
("unable to open database file").
"""
from app.config import PROJECT_ROOT, _resolve_sqlite_url


def test_relative_sqlite_url_resolves_to_project_root():
    assert _resolve_sqlite_url("sqlite+aiosqlite:///data/hinata.db") == (
        f"sqlite+aiosqlite:///{PROJECT_ROOT}/data/hinata.db"
    )


def test_plain_relative_sqlite_url_resolves_to_project_root():
    assert _resolve_sqlite_url("sqlite:///data/hinata.db") == (
        f"sqlite:///{PROJECT_ROOT}/data/hinata.db"
    )


def test_absolute_sqlite_url_unchanged():
    assert _resolve_sqlite_url("sqlite+aiosqlite:////var/data/hinata.db") == (
        "sqlite+aiosqlite:////var/data/hinata.db"
    )


def test_in_memory_sqlite_url_unchanged():
    assert _resolve_sqlite_url("sqlite+aiosqlite:///:memory:") == (
        "sqlite+aiosqlite:///:memory:"
    )


def test_non_sqlite_url_unchanged():
    assert _resolve_sqlite_url("postgresql+asyncpg://host:5432/db") == (
        "postgresql+asyncpg://host:5432/db"
    )
