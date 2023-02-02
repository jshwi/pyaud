"""
tests.config_test
=================
"""
# pylint: disable=protected-access
import copy
import typing as t

import pytest

import pyaud

# noinspection PyProtectedMember
from pyaud import _config as pc

from . import (
    DEFAULT_KEY,
    EXCLUDE,
    INDEXING,
    KEY,
    PLUGIN_NAME,
    PROJECT,
    VALUE,
    AppFiles,
    MockActionPluginFactoryType,
    MockMainType,
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
    app_files.home_config_file.write_text(pc.toml.dumps(home_rcfile))

    # reset the dict to the test default
    # ==================================
    # test the the changes made to clean are inherited through the
    # config hierarchy but not configured in this dict
    project_rcfile = dict(test_default)
    app_files.pyproject_toml.write_text(pc.toml.dumps(project_rcfile))

    # load "$HOME/.pyaudrc" and then "$PROJECT_DIR/.pyaudrc"
    # ======================================================
    # override "$HOME/.pyaudrc"
    pc.load_config(app_files)
    subtotal: t.Dict[str, t.Any] = dict(home_rcfile)
    assert dict(pc.toml) == subtotal

    # load pyproject.toml
    # ===================
    # pyproject.toml tools start with [tool.<PACKAGE_REPO>]
    pyproject_dict = {"tool": {pyaud.__name__: test_default}}
    app_files.pyproject_toml.write_text(pc.toml.dumps(pyproject_dict))

    # load "$HOME/.pyaudrc" and then "$PROJECT_DIR/.pyaudrc"
    # ======================================================
    # override "$HOME/.pyaudrc"
    pc.load_config(app_files)
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
    assert dict(pc.toml) == pc.DEFAULT_CONFIG


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

    app_files.global_config_file.write_text(pc.toml.dumps())

    # check config file to confirm essential key was removed
    pc.toml.loads(app_files.global_config_file.read_text())

    app_files.global_config_file.write_text(pc.toml.dumps())
    pc.configure_global(app_files)
    main(PLUGIN_NAME[1])

    # confirm after running main that no crash occurred and that the
    # essential key was replaced with a default
    pc.toml.loads(app_files.global_config_file.read_text())
