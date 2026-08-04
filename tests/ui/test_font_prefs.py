from PySide6.QtGui import QFontDatabase

from app.ui import font_prefs


def _use_tmp_settings(monkeypatch, tmp_path):
    settings_path = tmp_path / "settings.ini"
    monkeypatch.setattr(font_prefs, "get_settings_path", lambda: settings_path)
    return settings_path


def test_resolve_default_font_family_prefers_aptos_when_installed(monkeypatch):
    monkeypatch.setattr(QFontDatabase, "families", staticmethod(lambda: ["Aptos", "Arial"]))

    assert font_prefs.resolve_default_font_family() == "Aptos"


def test_resolve_default_font_family_falls_back_when_aptos_missing(monkeypatch):
    monkeypatch.setattr(QFontDatabase, "families", staticmethod(lambda: ["Arial", "DejaVu Sans"]))

    # Not installed here -- must not hard-fail or claim Aptos anyway.
    assert font_prefs.resolve_default_font_family() != "Aptos"


def test_load_font_family_returns_resolved_default_when_nothing_saved(monkeypatch, tmp_path):
    _use_tmp_settings(monkeypatch, tmp_path)
    monkeypatch.setattr(QFontDatabase, "families", staticmethod(lambda: ["Arial"]))

    assert font_prefs.load_font_family() == font_prefs.resolve_default_font_family()


def test_save_then_load_round_trips_the_chosen_font(monkeypatch, tmp_path):
    _use_tmp_settings(monkeypatch, tmp_path)
    monkeypatch.setattr(QFontDatabase, "families", staticmethod(lambda: ["Arial", "Consolas"]))

    font_prefs.save_font_family("Consolas")

    assert font_prefs.load_font_family() == "Consolas"


def test_load_font_family_ignores_a_saved_font_no_longer_installed(monkeypatch, tmp_path):
    _use_tmp_settings(monkeypatch, tmp_path)
    monkeypatch.setattr(QFontDatabase, "families", staticmethod(lambda: ["Consolas"]))
    font_prefs.save_font_family("Consolas")

    # Simulate reopening the app on a machine/profile where that font is gone.
    monkeypatch.setattr(QFontDatabase, "families", staticmethod(lambda: ["Arial"]))

    assert font_prefs.load_font_family() == font_prefs.resolve_default_font_family()
    assert font_prefs.load_font_family() != "Consolas"
