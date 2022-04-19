pyaud
=====
.. image:: https://github.com/jshwi/pyaud/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/jshwi/pyaud/actions/workflows/ci.yml
    :alt: ci
.. image:: https://github.com/jshwi/pyaud/actions/workflows/codeql-analysis.yml/badge.svg
    :target: https://github.com/jshwi/pyaud/actions/workflows/codeql-analysis.yml
    :alt: CodeQL
.. image:: https://readthedocs.org/projects/pyaud/badge/?version=latest
    :target: https://pyaud.readthedocs.io/en/latest/?badge=latest
    :alt: readthedocs.org
.. image:: https://img.shields.io/badge/python-3.8-blue.svg
    :target: https://www.python.org/downloads/release/python-380
    :alt: python3.8
.. image:: https://img.shields.io/pypi/v/pyaud
    :target: https://img.shields.io/pypi/v/pyaud
    :alt: pypi
.. image:: https://codecov.io/gh/jshwi/pyaud/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jshwi/pyaud
    :alt: codecov.io
.. image:: https://img.shields.io/badge/License-MIT-blue.svg
    :target: https://lbesson.mit-license.org/
    :alt: mit
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: black

The ``pyaud`` framework is designed for writing modular audits for Python packages

    | Audits can be run to fail, such as when using CI, or include a fix
    | Fixes can be written for whole directories or individual files
    | Plugins can be written for manipulating files
    | Supports single script plugins

Install
-------
Dependencies

    | python3.8 (see `pyenv <https://github.com/pyenv/pyenv>`_)
    | pip

PyPi

``pip install pyaud``

Development

``poetry install``

Usage
-----

.. code-block:: console

    usage: pyaud [-h] [-c] [-d] [-f] [-s] [-v] [--rcfile RCFILE] MODULE

    positional arguments:
      MODULE           choice of module: [modules] to list all

    optional arguments:
      -h, --help       show this help message and exit
      -c, --clean      clean unversioned files prior to any process
      -d, --deploy     include test and docs deployment after audit
      -s, --suppress   continue without stopping for errors
      -v, --verbose    incrementally increase logging verbosity
      --rcfile RCFILE  select file to override config hierarchy

Plugins
-------

``pyaud`` will search for a ``plugins`` package in the project root

    | This package can contain any number of Python modules
    | For writing plugins see `docs <https://jshwi.github.io/pyaud/pyaud.html#pyaud-plugins>`_

The following plugins are usable out of the box:

.. code-block:: console

    audit           -- Read from [audit] key in config
    clean           -- Remove all unversioned package files recursively
    coverage        -- Run package unit-tests with `pytest` and `coverage`
    deploy          -- Deploy package documentation and test coverage
    deploy-cov      -- Upload coverage data to `Codecov`
    deploy-docs     -- Deploy package documentation to `gh-pages`
    docs            -- Compile package documentation with `Sphinx`
    files           -- Audit project data files
    format          -- Audit code against `Black`
    format-docs     -- Format docstrings with `docformatter`
    format-str      -- Format f-strings with `flynt`
    generate-rcfile -- Print rcfile to stdout
    imports         -- Audit imports with `isort`
    lint            -- Lint code with `pylint`
    readme          -- Parse, test, and assert RST code-blocks
    requirements    -- Audit requirements.txt with Pipfile.lock
    tests           -- Run the package unit-tests with `pytest`
    toc             -- Audit docs/<NAME>.rst toc-file
    typecheck       -- Typecheck code with `mypy`
    unused          -- Audit unused code with `vulture`
    whitelist       -- Check whitelist.py file with `vulture`

Environment
-----------

Default environment variables:

.. code-block:: shell

    PYAUD_WHITELIST     = "whitelist.py"
    PYAUD_COVERAGE_XML  = "coverage.xml"
    PYAUD_REQUIREMENTS  = "requirements.txt"
    PYAUD_GH_NAME       = ""
    PYAUD_GH_EMAIL      = ""
    PYAUD_GH_TOKEN      = ""
    PYAUD_GH_REMOTE     = ""

Environment variables should be placed in an .env file in the project root and override all config files

Configure
---------

Configuration of settings can be made with the following toml syntax files (overriding in this order):

    | ~/.config/pyaud/pyaud.toml
    | ~/.pyaudrc
    | .pyaudrc
    | pyproject.toml

Example config:

.. code-block:: toml

    [clean]
    exclude = ["*.egg*", ".mypy_cache", ".env", "instance"]

    [logging]
    version = 1
    disable_existing_loggers = true

    [indexing]
    exclude = ["whitelist.py", "conf.py", "setup.py"]

    [packages]
    exclude = ["tests"]
    name = "pyaud"

    [audit]
    modules = [
        "format",
        "format-docs",
        "format-str",
        "imports",
        "typecheck",
        "unused",
        "lint",
        "coverage",
        "readme",
        "docs",
    ]

    [logging.root]
    level = "INFO"
    handlers = ["default"]
    propagate = false

    [logging.formatters.standard]
    format = "%(asctime)s %(levelname)s %(name)s %(message)s"

    [logging.handlers.default]
    class = "logging.handlers.TimedRotatingFileHandler"
    formatter = "standard"
    when = "d"
    backupCount = 60
    filename = "~/.cache/pyaud/log/pyaud.log"

Prefix each key with ``tool.pyaud`` when using pyproject.toml

.. code-block:: toml

    [tool.pyaud.clean]
    exclude = ["*.egg*", ".mypy_cache", ".env", "instance"]
