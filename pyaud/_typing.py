"""
pyaud._typing
=============
"""
import typing as _t
from types import TracebackType as _TracebackType

Exc = _t.Optional[_t.Type[BaseException]]
ExcVal = _t.Optional[BaseException]
ExcTB = _t.Optional[_TracebackType]
