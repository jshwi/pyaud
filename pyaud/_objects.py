"""
pyaud._objects
==============
"""
from object_colors import Color as _Color

NAME = __name__.split(".", maxsplit=1)[0]


colors = _Color()

colors.populate_colors()
