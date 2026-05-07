import importlib

import pytest


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Give every test its own isolated SQLite DB and migrations applied."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db_path))

    # Reset cached settings so the new env var is picked up.
    import src.config as config_mod

    config_mod._settings = None
    importlib.reload(config_mod)

    from src import db as db_mod

    importlib.reload(db_mod)
    db_mod.run_migrations(db_path)
    return db_path
