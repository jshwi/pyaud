"""
tests.config_test
=================
"""
# pylint: disable=protected-access
import copy
import logging
import logging.config as logging_config
import logging.handlers as logging_handlers
import typing as t
from pathlib import Path

import pytest

import pyaud

# noinspection PyProtectedMember
from pyaud import _config as pc

from . import (
    CRITICAL,
    DEBUG,
    DEFAULT,
    DEFAULT_KEY,
    ERROR,
    EXCLUDE,
    FILENAME,
    HANDLERS,
    INDEXING,
    INFO,
    KEY,
    LEVEL,
    LOGGING,
    MODULE,
    PLUGIN_NAME,
    PROJECT,
    PYAUD_PLUGINS_PLUGINS,
    ROOT,
    VALUE,
    VERSION,
    WARNING,
    AppFiles,
    MockActionPluginFactoryType,
    MockMainType,
)


@pytest.mark.parametrize(DEFAULT, [CRITICAL, ERROR, WARNING, INFO, DEBUG])
@pytest.mark.parametrize("flag", ["", "-v", "-vv", "-vvv", "-vvvv"])
def test_loglevel(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    app_files: AppFiles,
    default: str,
    flag: str,
) -> None:
    """Test the right loglevel is set when parsing the commandline.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param app_files: App file locations object.
    :param default: Default loglevel configuration.
    :param flag: Verbosity level commandline flag.
    """
    levels = {
        "": [CRITICAL, ERROR, WARNING, INFO, DEBUG],
        "-v": [ERROR, WARNING, INFO, DEBUG, DEBUG],
        "-vv": [WARNING, INFO, DEBUG, DEBUG, DEBUG],
        "-vvv": [INFO, DEBUG, DEBUG, DEBUG, DEBUG],
        "-vvvv": [DEBUG, DEBUG, DEBUG, DEBUG, DEBUG],
    }
    pc.toml[LOGGING][ROOT][LEVEL] = default
    app_files.global_config_file.write_text(pc.toml.dumps())

    # dummy call to non-existing plugin to evaluate multiple -v
    # arguments
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, {MODULE: lambda *_, **__: None})
    main(MODULE, flag)
    assert (
        logging.getLevelName(logging.root.level)
        == levels[flag][levels[""].index(default)]
    )


def test_del_key_in_context() -> None:
    """Confirm there is no error raised when deleting temp key-value."""
    obj: t.Dict[str, str] = {}
    with pc.TempEnvVar(obj, key=VALUE):
        assert obj[KEY] == VALUE
        del obj[KEY]


def test_toml(app_files: AppFiles) -> None:
    """Assert "$HOME/.config/pyaud.toml" is created and loaded.

    Create "$HOME/.pyaudrc" and "$PROJECT_DIR/.pyaudrc" load them,
    ensuring that each level up overrides changes from lower level
    configs whilst, keeping the remaining changes. Create
    "$PROJECT_DIR/pyproject.toml" and test the same, which will override
    all previous configs.

    :param app_files: App file locations object.
    """
    # base config is created and loaded
    # =================================
    test_default: t.Dict[t.Any, t.Any] = copy.deepcopy(pc.DEFAULT_CONFIG)
    assert dict(pc.toml) == test_default

    # instantiate a new dict object
    # =============================
    # preserve the test default config
    home_rcfile = dict(test_default)
    home_rcfile[LOGGING][HANDLERS][DEFAULT].update(
        {"class": "logging.handlers.StreamHandler"}
    )
    home_rcfile[LOGGING][VERSION] = 2
    app_files.home_config_file.write_text(pc.toml.dumps(home_rcfile))

    # reset the dict to the test default
    # ==================================
    # test the the changes made to clean are inherited through the
    # config hierarchy but not configured in this dict
    project_rcfile = dict(test_default)
    project_rcfile[LOGGING][VERSION] = 3
    app_files.pyproject_toml.write_text(pc.toml.dumps(project_rcfile))

    # load "$HOME/.pyaudrc" and then "$PROJECT_DIR/.pyaudrc"
    # ======================================================
    # override "$HOME/.pyaudrc"
    pc.load_config(app_files)
    subtotal: t.Dict[str, t.Any] = dict(home_rcfile)
    subtotal[LOGGING][VERSION] = 3
    subtotal[LOGGING][HANDLERS][DEFAULT][FILENAME] = str(
        Path(subtotal[LOGGING][HANDLERS][DEFAULT][FILENAME]).expanduser()
    )
    assert dict(pc.toml) == subtotal

    # load pyproject.toml
    # ===================
    # pyproject.toml tools start with [tool.<PACKAGE_REPO>]
    pyproject_dict = {"tool": {pyaud.__name__: test_default}}
    changes = {LOGGING: {VERSION: 4}}
    pyproject_dict["tool"][pyaud.__name__].update(changes)
    app_files.pyproject_toml.write_text(pc.toml.dumps(pyproject_dict))

    # load "$HOME/.pyaudrc" and then "$PROJECT_DIR/.pyaudrc"
    # ======================================================
    # override "$HOME/.pyaudrc"
    pc.load_config(app_files)
    subtotal[LOGGING][VERSION] = 4
    assert dict(pc.toml) == subtotal


def test_toml_no_override_all(
    monkeypatch: pytest.MonkeyPatch, app_files: AppFiles
) -> None:
    """Confirm error not raised for entire key being overridden.

     Test for when implementing hierarchical config loading.

        def configure(self):
            '''Do the configuration.'''

            config = self.config
            if 'version' not in config:
    >           raise ValueError("dictionary doesn't specify a version")
    E           ValueError: dictionary doesn't specify a version

    :param monkeypatch: Mock patch environment and attributes.
    :param app_files: App file locations object.
    """
    monkeypatch.setattr(
        "pyaud._config.DEFAULT_CONFIG", copy.deepcopy(pc.DEFAULT_CONFIG)
    )
    pc.toml.clear()
    pc.load_config(app_files)  # base key-values
    pc.toml.loads(app_files.global_config_file.read_text())
    assert dict(pc.toml) == pc.DEFAULT_CONFIG
    app_files.home_config_file.write_text(
        pc.toml.dumps({LOGGING: {ROOT: {LEVEL: "INFO"}}})
    )

    # should override:
    # {
    #      VERSION: 1,
    #      "disable_existing_loggers": True,
    #      "formatters": {...},
    #      HANDLERS: {...},
    #      ROOT: {
    #          LEVEL: "DEBUG", HANDLERS: [...], "propagate": False,
    #      },
    # },
    # with:
    # {
    #      VERSION: 1,
    #      "disable_existing_loggers": True,
    #      "formatters": {...},
    #      HANDLERS: {...},
    #      ROOT: {
    #          LEVEL: "INFO", HANDLERS: [...], "propagate": False,
    #      },
    # },
    # and not reduce it to:
    # {ROOT: {LEVEL: "INFO"}}
    pc.load_config(app_files)

    # this here would raise a ``ValueError`` if not working as expected,
    # so on its own is an assertion
    logging_config.dictConfig(pc.toml[LOGGING])
    pc.DEFAULT_CONFIG[LOGGING][ROOT][LEVEL] = "INFO"
    assert dict(pc.toml) == pc.DEFAULT_CONFIG


def test_backup_toml(app_files: AppFiles) -> None:
    """Test backing up of toml config in case file is corrupted.

    :param app_files: App file locations object.
    """

    def _corrupt_file(_configfile_contents: str) -> None:
        # make a non-parsable change to the configfile (corrupt it)
        _lines = _configfile_contents.splitlines()
        _string = 'format = "%(asctime)s %(levelname)s %(name)s %(message)s"'
        for _count, _line in enumerate(list(_lines)):
            if _line == _string:
                _lines.insert(_count, _string[-6:])

        app_files.global_config_file.write_text("\n".join(_lines))

    # initialisation
    # ==============
    # originally there is no backup file (not until configure_global is
    # run)
    default_config = dict(pc.toml)
    assert not app_files.global_config_file_backup.is_file()

    # assert corrupt configfile with no backup will simply reset
    configfile_contents = app_files.global_config_file.read_text()
    _corrupt_file(configfile_contents)
    pc.configure_global(app_files)
    pc.toml.loads(app_files.global_config_file.read_text())

    # assert corrupt configfile is no same as default
    assert dict(pc.toml) == default_config

    # create backupfile
    pc.configure_global(app_files)
    assert app_files.global_config_file_backup.is_file()

    # ensure backupfile is a copy of the original config file
    # (overridden at every initialisation in the case of a change)
    configfile_contents = app_files.global_config_file.read_text()
    backupfile_contents = app_files.global_config_file_backup.read_text()
    assert configfile_contents == backupfile_contents

    # change to config
    # ================
    # this setting, by default, is True
    pc.toml[LOGGING]["disable_existing_loggers"] = False
    app_files.global_config_file.write_text(pc.toml.dumps())

    # now that there is a change the backup should be different to the
    # original until configure_global is run again
    # read configfile as only that file has been changed
    configfile_contents = app_files.global_config_file.read_text()

    assert configfile_contents != backupfile_contents
    pc.configure_global(app_files)

    # read both, as both have been changed
    configfile_contents = app_files.global_config_file.read_text()
    backupfile_contents = app_files.global_config_file_backup.read_text()
    assert configfile_contents == backupfile_contents

    # resolve corrupt file
    # ====================
    _corrupt_file(configfile_contents)

    # read configfile as only that file has been changed
    configfile_contents = app_files.global_config_file.read_text()

    # only configfile is corrupt, so check backup is not the same
    assert configfile_contents != backupfile_contents

    # resolve corruption
    # ==================
    pc.configure_global(app_files)
    configfile_contents = app_files.global_config_file.read_text()
    backupfile_contents = app_files.global_config_file_backup.read_text()
    assert configfile_contents == backupfile_contents

    # configfile should equal the backup file and all changes should be
    # retained
    assert configfile_contents == backupfile_contents
    pc.toml.loads(app_files.global_config_file.read_text())
    assert pc.toml[LOGGING]["disable_existing_loggers"] is False


def test_exclude_loads_at_main(
    main: MockMainType,
    app_files: AppFiles,
    mock_action_plugin_factory: MockActionPluginFactoryType,
) -> None:
    """Confirm project config is loaded with ``main``.

    :param main: Patch package entry point.
    :param app_files: App file locations object.
    :param mock_action_plugin_factory: Factory for creating mock action
        plugin objects.
    """
    plugins = mock_action_plugin_factory({"name": "Plugin"})
    pyaud.plugins.register(name=PLUGIN_NAME[1])(plugins[0])
    default_config = copy.deepcopy(pc.DEFAULT_CONFIG)
    project_config = copy.deepcopy(default_config)
    project_config[INDEXING][EXCLUDE].append(PROJECT)
    test_project_toml_object = pc._Toml()
    test_project_toml_object.update(project_config)
    app_files.project_config_file.write_text(test_project_toml_object.dumps())
    assert PROJECT not in pc.toml[INDEXING][EXCLUDE]

    main(PLUGIN_NAME[1])

    assert PROJECT in pc.toml[INDEXING][EXCLUDE]


def test_filter_logging_config_kwargs(app_files: AppFiles) -> None:
    """Test that no errors are raised for additional config kwargs.

    :param app_files: App file locations object.
    """
    test_default: t.Dict[t.Any, t.Any] = copy.deepcopy(pc.DEFAULT_CONFIG)

    # patch `DEFAULT_CONFIG` for `TimedRotatingFileHandler`
    logfile = str(Path.cwd() / ".cache" / "pyaud" / "log" / "pyaud.log")
    test_default[LOGGING][HANDLERS][DEFAULT][FILENAME] = logfile
    rcfile = dict(test_default)
    app_files.project_config_file.write_text(pc.toml.dumps(rcfile))
    pc.load_config(app_files)
    pc.configure_logging()
    logger = logging.getLogger(DEFAULT).root
    handler = logger.handlers[0]
    assert isinstance(handler, logging_handlers.TimedRotatingFileHandler)
    assert handler.when.casefold() == "d"  # type: ignore
    assert handler.backupCount == 60  # type: ignore
    assert handler.stream.buffer.name == logfile  # type: ignore

    # patch `DEFAULT_CONFIG` for `StreamHandler`
    rcfile[LOGGING][HANDLERS][DEFAULT]["class"] = "logging.StreamHandler"
    app_files.project_config_file.write_text(pc.toml.dumps(rcfile))
    pc.load_config(app_files)
    pc.configure_logging()
    logger = logging.getLogger(DEFAULT).root
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert getattr(handler, "when", None) is None
    assert getattr(handler, "backupCount", None) is None


def test_default_key() -> None:
    """Test setting and restoring of existing dict keys."""
    obj = {DEFAULT_KEY: "default_value"}
    with pc.TempEnvVar(obj, default_key="temp_value"):
        assert obj[DEFAULT_KEY] == "temp_value"

    assert obj[DEFAULT_KEY] == "default_value"


def test_del_key_config_runtime(
    main: MockMainType, app_files: AppFiles
) -> None:
    """Test a key can be removed and will be replaced if essential.

    :param main: Patch package entry point.
    :param app_files: App file locations object.
    """

    class Plugin(pyaud.plugins.Action):
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    pyaud.plugins.register(name=PLUGIN_NAME[1])(Plugin)

    # check config file for essential key
    pc.toml.loads(app_files.global_config_file.read_text())
    assert FILENAME in pc.toml[LOGGING][HANDLERS][DEFAULT]

    del pc.toml[LOGGING][HANDLERS][DEFAULT][FILENAME]

    app_files.global_config_file.write_text(pc.toml.dumps())

    # check config file to confirm essential key was removed
    pc.toml.loads(app_files.global_config_file.read_text())
    assert FILENAME not in pc.toml[LOGGING][HANDLERS][DEFAULT]

    app_files.global_config_file.write_text(pc.toml.dumps())
    pc.configure_global(app_files)
    main(PLUGIN_NAME[1])

    # confirm after running main that no crash occurred and that the
    # essential key was replaced with a default
    pc.toml.loads(app_files.global_config_file.read_text())
    assert FILENAME in pc.toml[LOGGING][HANDLERS][DEFAULT]
