pyaud
=====
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: License
.. image:: https://img.shields.io/pypi/v/pyaud
    :target: https://pypi.org/project/pyaud/
    :alt: PyPI
.. image:: https://github.com/jshwi/pyaud/actions/workflows/build.yaml/badge.svg
    :target: https://github.com/jshwi/pyaud/actions/workflows/build.yaml
    :alt: Build
.. image:: https://github.com/jshwi/pyaud/actions/workflows/codeql-analysis.yml/badge.svg
    :target: https://github.com/jshwi/pyaud/actions/workflows/codeql-analysis.yml
    :alt: CodeQL
.. image:: https://results.pre-commit.ci/badge/github/jshwi/pyaud/master.svg
   :target: https://results.pre-commit.ci/latest/github/jshwi/pyaud/master
   :alt: pre-commit.ci status
.. image:: https://codecov.io/gh/jshwi/pyaud/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jshwi/pyaud
    :alt: codecov.io
.. image:: https://readthedocs.org/projects/pyaud/badge/?version=latest
    :target: https://pyaud.readthedocs.io/en/latest/?badge=latest
    :alt: readthedocs.org
.. image:: https://img.shields.io/badge/python-3.8-blue.svg
    :target: https://www.python.org/downloads/release/python-380
    :alt: python3.8
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Black
.. image:: https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
    :target: https://pycqa.github.io/isort/
    :alt: isort
.. image:: https://img.shields.io/badge/%20formatter-docformatter-fedcba.svg
    :target: https://github.com/PyCQA/docformatter
    :alt: docformatter
.. image:: https://img.shields.io/badge/linting-pylint-yellowgreen
    :target: https://github.com/PyCQA/pylint
    :alt: pylint
.. image:: https://img.shields.io/badge/security-bandit-yellow.svg
    :target: https://github.com/PyCQA/bandit
    :alt: Security Status
.. image:: https://snyk.io/test/github/jshwi/pyaud/badge.svg
    :target: https://snyk.io/test/github/jshwi/pyaud/badge.svg
    :alt: Known Vulnerabilities
.. image:: https://snyk.io/advisor/python/pyaud/badge.svg
    :target: https://snyk.io/advisor/python/pyaud
    :alt: pyaud

Framework for writing Python package audits
-------------------------------------------

The ``pyaud`` framework is designed for writing modular audits for Python packages

Audits can be run to fail, such as when using CI, or include a fix

Fixes can be written for whole directories or individual files

Plugins can be written for manipulating files

Supports single script plugins

Installation
------------

.. code-block:: console

    $ pip install pyaud

Usage
-----

Commandline
***********

.. code-block:: console

    usage: pyaud [-h] [-v] [-f] [-n] [-s] [--audit LIST] [--exclude EXCLUDE] MODULE

    positional arguments:
      MODULE             choice of module: [modules] to list all

    optional arguments:
      -h, --help         show this help message and exit
      -v, --version      show program's version number and exit
      -f, --fix          suppress and fix all fixable issues
      -n, --no-cache     disable file caching
      -s, --suppress     continue without stopping for errors
      --audit LIST       comma separated list of plugins for audit
      --exclude EXCLUDE  regex of paths to ignore

Plugins
*******

``pyaud`` will search for a plugins package in the project root

To register a plugin package ensure it is importable and prefix the package with ``pyaud_``

The name ``pyaud_plugins`` is reserved and will be automatically imported

To view available plugins see ``pyaud-plugins`` `README <https://github.com/jshwi/pyaud-plugins/blob/master/README.rst>`_ or run ``pyaud modules all``

For writing plugins see `docs <https://jshwi.github.io/pyaud/pyaud.html#pyaud-plugins>`_

Configure
*********

Configuration values are declared in the pyproject.toml file

.. code-block:: toml

    [tool.pyaud]
    audit = [
      "commit-policy",
      "const",
      "docs",
      "files",
      "format",
      "format-docs",
      "format-str",
      "imports",
      "lint",
      "params",
      "test",
      "typecheck",
      "unused"
    ]
    exclude = '''
      (?x)^(
        | docs\/conf\.py
        | whitelist\.py
      )$
    '''
