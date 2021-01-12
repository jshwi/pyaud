"""
tests.files
===========

Content to write to mock files.
"""
# pylint: disable=too-many-lines

README_RST = """repo\n====\n"""
INDEX_RST = """
Repo
====

|

The source code is available `here <https://github.com/johndoe/repo>`_

|

.. toctree::
   :maxdepth: 1
   :name: mastertoc

   repo
   readme

* :ref:`genindex`

This documentation was last updated on |today|
"""
DEFAULT_TOC = """
repo package
============

Module contents
---------------

.. automodule:: repo
   :members:
   :undoc-members:
   :show-inheritance:
"""
