"""
Unit tests for the per-user data directory helper.
"""

import os

import pytest

from domain import user_paths


def test_user_data_dir_ends_in_app_name(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    path = user_paths.user_data_dir()
    assert os.path.basename(path) == user_paths.APP_DIR_NAME


def test_user_data_dir_creates_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    path = user_paths.user_data_dir()
    assert os.path.isdir(path)


def test_user_data_dir_falls_back_when_appdata_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path))
    path = user_paths.user_data_dir()
    assert os.path.isdir(path)
    assert os.path.basename(path) == user_paths.APP_DIR_NAME


def test_user_data_file_joins_filename(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    path = user_paths.user_data_file("settings.json")
    assert os.path.basename(path) == "settings.json"
    assert os.path.basename(os.path.dirname(path)) == user_paths.APP_DIR_NAME
