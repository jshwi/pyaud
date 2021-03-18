PyAud
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

.. code-block:: console

    usage: pyaud [-h] [-c] [-d] [-s] [-v] [--path PATH] MODULE

    positional arguments:
      MODULE          choice of module: ``modules`` to list all options

    optional arguments:
      -h, --help      show this help message and exit
      -c, --clean     clean unversioned files prior to any process
      -d, --deploy    include test and docs deployment after audit
      -s, --suppress  continue without stopping for errors
      -v, --verbose   incrementally increase logging verbosity
      --path PATH     set alternative path to present working dir
    ---------------------------------------------------------------------------

    audit                   Run all checks
    clean                   Remove all unversioned files unless excluded
    coverage                Run ``pytest`` with ``coverage``
    deploy                  Deploy code coverage and documentation
    deploy-cov              Deploy code coverage to ``codecov.io``
    deploy-docs             Deploy ``Sphinx`` docs to ``gh-pages``
    docs                    Compile documentation with ``Sphinx``
    files                   Run ``requirements``, ``toc``, and ``whitelist``
    format                  Format all Python project files with ``Black``
    imports                 Sort imports with ``isort``
    lint                    Show possible corrections with ``pylint``
    readme                  tests code-blocks in README.rst
    requirements            Create requirements.txt from Pipfile.lock
    tests                   Run unittests with ``pytest``
    toc                     Update docs/<PACKAGENAME>.rst
    typecheck               Inspect files for type errors with ``mypy``
    unused                  Inspect files for unused code with ``vulture``
    whitelist               Update ``vulture`` whitelist.py
..
