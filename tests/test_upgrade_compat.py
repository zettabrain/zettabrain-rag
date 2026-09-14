"""Upgrading from 0.5.x must not lose anyone's library, settings, or commands.

These are the tests that decide whether an in-place `pip install -U` is safe.
"""

import importlib
from pathlib import Path

import pytest
import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def legacy_install(tmp_path, monkeypatch):
    """A directory laid out the way 0.5.x left it."""
    (tmp_path / "src").mkdir()
    (tmp_path / "certs").mkdir()
    (tmp_path / "src" / "zettabrain_vectorstore").mkdir()
    (tmp_path / "src" / "zettabrain_vectorstore" / "chroma.sqlite3").touch()
    (tmp_path / "src" / "zettabrain.env").write_text(
        "# written by setup.sh\n"
        "OLLAMA_HOST=http://10.0.1.50:11434\n"
        "ZETTABRAIN_LLM_MODEL=llama3.1:8b\n"
        "ZETTABRAIN_EMBED_MODEL=nomic-embed-text\n"
        "RAG_DATA_PATH=/mnt/Rag-data\n"
        "ZETTABRAIN_TLS_PROVIDER=self-signed\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ZETTABRAIN_DIR", str(tmp_path))
    for var in ("ZETTABRAIN_CHROMA", "ZETTABRAIN_DOCS"):
        monkeypatch.delenv(var, raising=False)

    import zettabrain_rag.config as config

    importlib.reload(config)
    return config, tmp_path


class TestPathsMatchTheOldLayout:
    def test_existing_vector_store_is_used(self, legacy_install):
        """The whole point: an upgrade must find the library, not start empty."""
        config, tmp_path = legacy_install
        assert config.CHROMA_PATH == tmp_path / "src" / "zettabrain_vectorstore"
        assert config.CHROMA_PATH.exists()

    def test_certs_directory_unchanged(self, legacy_install):
        config, tmp_path = legacy_install
        assert config.CERT_DIR == tmp_path / "certs"

    def test_application_lives_under_src(self, legacy_install):
        config, tmp_path = legacy_install
        assert config.DEPLOY_DIR == tmp_path / "src"

    def test_chroma_env_override_still_wins(self, tmp_path, monkeypatch):
        """Installs that moved the store set ZETTABRAIN_CHROMA; that must keep working."""
        elsewhere = tmp_path / "elsewhere" / "store"
        monkeypatch.setenv("ZETTABRAIN_DIR", str(tmp_path))
        monkeypatch.setenv("ZETTABRAIN_CHROMA", str(elsewhere))
        import zettabrain_rag.config as config

        importlib.reload(config)
        assert config.CHROMA_PATH == elsewhere


class TestSettingsMigration:
    def test_settings_are_carried_forward(self, legacy_install):
        config, _ = legacy_install
        migrated = config.migrate_legacy_settings()
        assert migrated["ollama_host"] == "http://10.0.1.50:11434"
        assert migrated["llm_model"] == "llama3.1:8b"
        assert migrated["embed_model"] == "nomic-embed-text"

    def test_document_folder_is_preserved(self, legacy_install):
        """RAG_DATA_PATH pointed at a mount; losing it would empty the library."""
        config, _ = legacy_install
        config.migrate_legacy_settings()
        assert config.docs_folder() == "/mnt/Rag-data"

    def test_migration_is_recorded(self, legacy_install):
        config, _ = legacy_install
        config.migrate_legacy_settings()
        assert config.get_setting("migrated_from") == "0.5.x"

    def test_running_twice_changes_nothing(self, legacy_install):
        config, _ = legacy_install
        config.migrate_legacy_settings()
        config.set_setting("llm_model", "phi4-mini")
        assert config.migrate_legacy_settings() == {}
        assert config.get_setting("llm_model") == "phi4-mini"

    def test_old_file_is_not_deleted(self, legacy_install):
        """A bad upgrade must be reversible."""
        config, _ = legacy_install
        config.migrate_legacy_settings()
        assert config.LEGACY_ENV_FILE.exists()

    def test_fresh_install_migrates_nothing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ZETTABRAIN_DIR", str(tmp_path))
        import zettabrain_rag.config as config

        importlib.reload(config)
        assert config.migrate_legacy_settings() == {}

    def test_unreadable_legacy_file_is_survivable(self, tmp_path, monkeypatch):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "zettabrain.env").write_bytes(b"\xff\xfe not text at all")
        monkeypatch.setenv("ZETTABRAIN_DIR", str(tmp_path))
        import zettabrain_rag.config as config

        importlib.reload(config)
        config.migrate_legacy_settings()  # must not raise


class TestConsoleScripts:
    """Every command from 0.5.x must still be installed, especially zettabrain-server:
    the systemd unit written by setup.sh calls it by name."""

    EXPECTED = {
        "zettabrain", "zettabrain-chat", "zettabrain-ingest", "zettabrain-setup",
        "zettabrain-status", "zettabrain-storage", "zettabrain-server",
        "zettabrain-cert", "zettabrain-postinstall",
    }

    @pytest.fixture(scope="class")
    def scripts(self):
        data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
        return data["project"]["scripts"]

    def test_every_legacy_command_survives(self, scripts):
        assert self.EXPECTED <= set(scripts)

    def test_server_command_target_exists(self, scripts):
        assert scripts["zettabrain-server"] == "zettabrain_rag.cli:server_cmd"
        from zettabrain_rag import cli

        assert callable(cli.server_cmd)

    @pytest.mark.parametrize("command", sorted(EXPECTED))
    def test_each_target_is_importable(self, scripts, command):
        module, _, func = scripts[command].partition(":")
        assert callable(getattr(importlib.import_module(module), func))


class TestPackagingMetadata:
    @pytest.fixture(scope="class")
    def project(self):
        return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]

    def test_name_is_unchanged(self, project):
        assert project["name"] == "zettabrain-rag"

    def test_version_moves_forward(self, project):
        """0.5.31 -> 0.2.0 would not install; pip does not downgrade on upgrade."""
        major, minor, _ = project["version"].split(".")
        assert (int(major), int(minor)) > (0, 5)

    def test_version_matches_the_package(self, project):
        from zettabrain_rag import __version__

        assert __version__ == project["version"]


class TestAuthDefaultsOff:
    """0.5.x had no login. Growing one in an upgrade would lock people out."""

    def test_disabled_by_default(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ZETTABRAIN_DIR", str(tmp_path))
        import zettabrain_rag.config as config

        importlib.reload(config)
        import zettabrain_rag.auth as auth

        importlib.reload(auth)
        assert auth.auth_enabled() is False

    def test_require_auth_passes_when_disabled(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ZETTABRAIN_DIR", str(tmp_path))
        import zettabrain_rag.config as config

        importlib.reload(config)
        import zettabrain_rag.auth as auth

        importlib.reload(auth)
        assert auth.require_auth(None) == "local"

    def test_can_be_turned_on(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ZETTABRAIN_DIR", str(tmp_path))
        import zettabrain_rag.config as config

        importlib.reload(config)
        import zettabrain_rag.auth as auth

        importlib.reload(auth)
        config.set_setting("auth_enabled", True)
        assert auth.auth_enabled() is True
