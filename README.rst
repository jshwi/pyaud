pyaud
=====
.. image:: https://github.com/jshwi/pyaud/workflows/build/badge.svg
    :target: https://github.com/jshwi/pyaud/workflows/build/badge.svg
    :alt: audit
.. image:: https://img.shields.io/badge/python-3.8-blue.svg
    :target: https://www.python.org/downloads/release/python-380
    :alt: python3.8
.. image:: https://img.shields.io/pypi/v/pyaud
    :target: https://img.shields.io/pypi/v/pyaud
    :alt: pypi
.. image:: https://codecov.io/gh/jshwi/pyaud/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jshwi/pyaud
    :alt: codecov.io
.. image:: https://readthedocs.org/projects/pyaud/badge/?version=latest
    :target: https://pyaud.readthedocs.io/en/latest/?badge=latest
    :alt: readthedocs.org
.. image:: https://img.shields.io/badge/License-MIT-blue.svg
    :target: https://lbesson.mit-license.org/
    :alt: mit
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: black

Automate quality-check of Python package with bundled utils

Configuration of settings can be made with the following ini syntax file:
    | ~/.config/pyaud/pyaud.ini

Default environment variables:

or environment variables (overriding in this order)

.. code-block:: shell

    PYAUD_WHITELIST     = "whitelist.py"
    PYAUD_COVERAGE_XML  = "coverage.xml"
    PYAUD_REQUIREMENTS  = "requirements.txt"
    BUILDDIR            = "docs/_build"
    PYAUD_GH_NAME       = ""
    PYAUD_GH_EMAIL      = ""
    PYAUD_GH_TOKEN      = ""
    PYAUD_GH_REMOTE     = ""
    CODECOV_TOKEN       = ""

Environment variables should be placed in an .env file in project root:

Example config:

.. code-block:: ini

    [CLEAN]
    exclude = *.egg*,
              .env,
              instance,
              .coverage

Commandline arguments:

.. code-block:: console

    usage: pyaud [-h] [-c] [-d] [-s] [-v] [--path PATH] MODULE

    positional arguments:
      MODULE          choice of module: [modules] to list all

    optional arguments:
      -h, --help      show this help message and exit
      -c, --clean     clean unversioned files prior to any process
      -d, --deploy    include test and docs deployment after audit
      -s, --suppress  continue without stopping for errors
      -v, --verbose   incrementally increase logging verbosity
      --path PATH     set alternative path to present working dir
    ------------------------------------------------------------------------
    audit        -- Run all modules for complete package audit
    clean        -- Remove all unversioned package files recursively
    coverage     -- Run package unit-tests with `pytest` and `coverage`
    deploy       -- Deploy package documentation and test coverage
    deploy-cov   -- Upload coverage data to `Codecov`
    deploy-docs  -- Deploy package documentation to `gh-pages`
    docs         -- Compile package documentation with `Sphinx`
    files        -- Audit project data files
    format       -- Audit code against `Black`
    format-docs  -- Format docstrings with `docformatter`
    format-str   -- Format f-strings with `flynt`
    imports      -- Audit imports with `isort`
    lint         -- Lint code with `pylint`
    readme       -- Parse, test, and assert RST code-blocks
    requirements -- Audit requirements.txt with Pipfile.lock
    tests        -- Run the package unit-tests with `pytest`
    toc          -- Audit docs/<NAME>.rst toc-file
    typecheck    -- Typecheck code with `mypy`
    unused       -- Audit unused code with `vulture`
    whitelist    -- Check whitelist.py file with `vulture`

*The word `function` and `module` are used interchangeably in this package*
