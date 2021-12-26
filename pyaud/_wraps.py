"""
pyaud._wraps
============
"""
import functools as _functools
import sys as _sys
import typing as _t

from ._indexing import files as _files
from ._utils import colors as _colors


def check_command(func: _t.Callable[..., int]) -> _t.Callable[..., None]:
    """Run the routine common with all functions in this package.

    :param func: Function to decorate.
    :return: Wrapped function.
    """

    @_functools.wraps(func)
    def _wrapper(*args: str, **kwargs: bool) -> None:
        if not _files.reduce():
            print("No files found")
        else:
            returncode = func(*args, **kwargs)
            if returncode:
                _colors.red.bold.print(
                    f"Failed: returned non-zero exit status {returncode}",
                    file=_sys.stderr,
                )
            else:
                _colors.green.bold.print(
                    f"Success: no issues found in {len(_files)} source files"
                )

    return _wrapper
