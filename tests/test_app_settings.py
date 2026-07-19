"""
Unit tests for AppSettings persistence, including migration from the
legacy next-to-executable settings.json location.
"""

import json
import os

import pytest

from domain import app_settings as app_settings_module
from domain import user_paths
from domain.app_settings import AppSettings


@pytest.fixture
def fresh_settings(tmp_path, monkeypatch):
    """A clean AppSettings singleton backed by a tmp AppData-style dir.

    Monkeypatches APPDATA (rather than _settings_file_path directly) so the
    real user_data_dir()/mkdir behavior is exercised, same as production.
    """
    AppSettings._instance = None

    appdata_root = tmp_path / "appdata"
    monkeypatch.setenv("APPDATA", str(appdata_root))
    new_path = str(appdata_root / user_paths.APP_DIR_NAME / "settings.json")

    legacy_path = str(tmp_path / "legacy" / "settings.json")
    os.makedirs(os.path.dirname(legacy_path), exist_ok=True)

    monkeypatch.setattr(app_settings_module, "_legacy_settings_paths", lambda: [legacy_path])

    yield app_settings_module.AppSettings(), new_path, legacy_path

    AppSettings._instance = None


def test_save_then_load_round_trips(fresh_settings):
    settings, new_path, _ = fresh_settings
    settings.line_width = 3.5
    settings.save()

    AppSettings._instance = None
    reloaded = AppSettings()
    reloaded.load()

    assert os.path.isfile(new_path)
    assert reloaded.line_width == 3.5


def test_save_creates_missing_directory(fresh_settings):
    settings, new_path, _ = fresh_settings
    assert not os.path.isdir(os.path.dirname(new_path))
    settings.save()
    assert os.path.isfile(new_path)


def test_corrupt_settings_falls_back_to_defaults(fresh_settings):
    settings, new_path, _ = fresh_settings
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    with open(new_path, "w", encoding="utf-8") as f:
        f.write("{not valid json")

    settings.load()

    assert settings.line_width == app_settings_module._DEFAULTS["line_width"]


def test_migration_copies_legacy_when_new_absent(fresh_settings):
    settings, new_path, legacy_path = fresh_settings
    with open(legacy_path, "w", encoding="utf-8") as f:
        json.dump({"line_width": 7.0}, f)

    settings.load()

    assert os.path.isfile(new_path)
    assert os.path.isfile(legacy_path)  # original left untouched
    assert settings.line_width == 7.0


def test_migration_skipped_when_new_file_present(fresh_settings):
    settings, new_path, legacy_path = fresh_settings
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump({"line_width": 1.5}, f)
    with open(legacy_path, "w", encoding="utf-8") as f:
        json.dump({"line_width": 7.0}, f)

    settings.load()

    assert settings.line_width == 1.5


def test_no_files_present_uses_defaults(fresh_settings):
    settings, _, _ = fresh_settings
    settings.load()
    assert settings.line_width == app_settings_module._DEFAULTS["line_width"]
