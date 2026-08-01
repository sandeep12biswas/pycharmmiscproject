"""NFR-3: the DB/settings must live under the OS-standard per-user app-data
directory under a fixed, predictable app name -- not derived from argv[0]
(sys.argv[0] varies with how the app is launched: 'python main.py', a
pytest/python -c invocation, or a frozen PyInstaller executable's own path),
and not vulnerable to other Qt-using code in the same process resetting
QCoreApplication.applicationName() after app/config.py is first imported
(observed in this test suite: pytest-qt's own fixtures do exactly that)."""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QStandardPaths

from app import config


def test_get_app_data_dir_forces_the_fixed_application_name():
    # Simulate exactly what broke this in practice: something else in the
    # process (pytest-qt, or argv[0]-derived Qt defaults) left applicationName
    # pointing at the wrong thing. get_app_data_dir() must still resolve
    # correctly, since it re-asserts the name itself rather than trusting a
    # prior import-time side effect.
    QCoreApplication.setApplicationName("something-else-entirely")

    config.get_app_data_dir()

    assert QCoreApplication.applicationName() == config.APP_NAME


def test_app_data_dir_matches_qstandardpaths():
    expected = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    assert config.get_app_data_dir() == expected


def test_db_and_settings_live_under_the_fixed_app_name_directory():
    db_path = config.get_db_path()
    settings_path = config.get_settings_path()

    assert db_path.parent.name == config.APP_NAME
    assert settings_path.parent.name == config.APP_NAME
    assert db_path.name == "notes.db"
    assert settings_path.name == "settings.ini"
