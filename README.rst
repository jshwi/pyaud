pyaud
=====
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: License
.. image:: https://img.shields.io/pypi/v/pyaud
    :target: https://img.shields.io/pypi/v/pyaud
    :alt: pypi
.. image:: https://github.com/jshwi/pyaud/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/jshwi/pyaud/actions/workflows/ci.yml
    :alt: CI
.. image:: https://github.com/jshwi/pyaud/actions/workflows/codeql-analysis.yml/badge.svg
    :target: https://github.com/jshwi/pyaud/actions/workflows/codeql-analysis.yml
    :alt: CodeQL
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
    :alt: black

Framework for writing Python package audits
-------------------------------------------

The ``pyaud`` framework is designed for writing modular audits for Python packages

Audits can be run to fail, such as when using CI, or include a fix

Fixes can be written for whole directories or individual files

Plugins can be written for manipulating files

Supports single script plugins

Installation
------------

PyPi
****

``pip install pyaud``

Development
***********

``poetry install``

Usage
-----

.. code-block:: console

    usage: pyaud [-h] [-c] [-f] [-n] [-s] [-t] [-v] [--rcfile RCFILE] [--version] MODULE

    positional arguments:
      MODULE           choice of module: [modules] to list all

    optional arguments:
      -h, --help       show this help message and exit
      -c, --clean      clean unversioned files prior to any process
      -f, --fix        suppress and fix all fixable issues
      -n, --no-cache   disable file caching
      -s, --suppress   continue without stopping for errors
      -t, --timed      track the length of time for each plugin
      -v, --verbose    incrementally increase logging verbosity
      --rcfile RCFILE  select file to override config hierarchy
      --version        show version and exit

Plugins
-------

``pyaud`` will search for a plugins package in the project root

To register a plugin package ensure it is importable and prefix the package with ``pyaud_``

The name ``pyaud_plugins`` is reserved and will be automatically imported

To view available plugins see ``pyaud-plugins`` `README <https://github.com/jshwi/pyaud-plugins/blob/master/README.rst>`_ or run ``pyaud modules all``

For writing plugins see `docs <https://jshwi.github.io/pyaud/pyaud.html#pyaud-plugins>`_

Configure
---------

Configuration of settings can be made with the following toml syntax files (overriding in this order):

    | ~/.config/pyaud/pyaud.toml
    | ~/.pyaudrc
    | .pyaudrc
    | pyproject.toml

A config can be generated with `pyaud generate-rcfile`

Prefix each key with ``tool.pyaud`` when using pyproject.toml
