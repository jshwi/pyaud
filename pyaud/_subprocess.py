"""
pyaud._subprocess
=================
"""
from __future__ import annotations

import functools as _functools
import logging as _logging
import os as _os
import shutil as _shutil
import sys as _sys
import typing as _t
from pathlib import Path as _Path
from subprocess import PIPE as _PIPE
from subprocess import CalledProcessError as _CalledProcessError
from subprocess import Popen as _Popen
from subprocess import check_output as _sp_out

from . import config as _config
from . import exceptions as _exceptions
from ._objects import MutableSequence as _MutableSequence


class _STDOut(_MutableSequence):
    """Only except str in the stdout object."""

    def insert(self, index: int, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(
                "stdout received as '{}': only str instances allowed".format(
                    type(value).__name__
                )
            )

        super().insert(index, value)


class Subprocess:
    """Object-oriented Subprocess.

    ``exe`` is a mandatory argument used to construct the subprocess
    executable. Default ``file``, ``capture``, and ``devnull`` values
    can be set when instantiating the object and overridden later when
    using ``call``.

    :param exe: Subprocess executable.
    :key loglevel: Loglevel for non-error logging.
    :param commands: List of positional arguments to set as attributes
        if not None.
    :key file: File path to write stream to if not None.
    :key capture: Collect output array.
    :key log: Pipe stdout to logging instead of console.
    :key devnull: Send output to /dev/null.
    :raise CommandNotFoundError: Raise if instantiated subprocess cannot
        exist.
    """

    def __init__(
        self,
        exe: str,
        loglevel: str = "error",
        commands: _t.Optional[_t.Iterable[str]] = None,
        **kwargs: _t.Union[bool, str],
    ) -> None:
        self.is_command = _shutil.which(exe)
        self._exe = exe
        self._loglevel = loglevel
        if commands is not None:
            for command in commands:
                setattr(
                    self,
                    command.replace("-", "_"),
                    _functools.partial(self.call, command),
                )

        self._kwargs = kwargs
        self._stdout: _t.MutableSequence[str] = _STDOut()
        self.args: _t.Tuple[str, ...] = ()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} ({self._exe})>"

    def _handle_stdout(
        self, pipeline: _Popen, **kwargs: _t.Union[bool, str]
    ) -> None:
        if pipeline.stdout is not None:
            for line in iter(pipeline.stdout.readline, b""):
                line = line.decode("utf-8", "ignore")
                file = kwargs.get("file", self._kwargs.get("file", None))
                if file is not None:
                    with open(file, "a+", encoding="utf-8") as fout:
                        fout.write(line)

                elif kwargs.get("capture", self._kwargs.get("capture", False)):
                    self._stdout.append(line.strip())

                elif kwargs.get("devnull", self._kwargs.get("devnull", False)):
                    with open(_os.devnull, "w", encoding="utf-8") as fout:
                        fout.write(line)

                else:
                    _sys.stdout.write(line)

    def _handle_stderr(self, pipeline: _Popen) -> None:
        for line in iter(pipeline.stderr.readline, b""):  # type: ignore
            getattr(_logging.getLogger(self._exe), self._loglevel)(
                line.decode("utf-8", "ignore").strip()
            )

    def _open_process(self, *args: str, **kwargs: _t.Union[bool, str]) -> int:
        # open process with ``subprocess.Popen``
        # pipe stream depending on the keyword arguments provided
        # Log errors to file regardless
        # wait for process to finish and return it's exit-code
        if not self.is_command:
            raise _exceptions.CommandNotFoundError(self._exe)

        pipeline = _Popen(  # pylint: disable=consider-using-with
            [self._exe, *args], stdout=_PIPE, stderr=_PIPE
        )
        self._handle_stdout(pipeline, **kwargs)
        self._handle_stderr(pipeline)
        return pipeline.wait()

    def call(self, *args: str, **kwargs: bool) -> int:
        """Call command. Open process with ``subprocess.Popen``.

        Pipe stream depending on the keyword arguments provided to
        instance constructor or overridden through this method. If a
        file path is provided it will take precedence over the other
        options, then capture and then finally devnull. Log errors to
        file regardless. Wait for process to finish and return it's
        exit-code.

        :param args: Positional str arguments.
        :key file: File path to write stream to if not None.
        :key devnull: Send output to /dev/null.
        :key capture: Collect output array.
        :key suppress: Suppress errors and continue running.
        :raises CalledProcessError: If error occurs in subprocess.
        :return: Exit status.
        """
        self.args = tuple(  # pylint: disable=consider-using-generator
            [str(i) for i in args]
        )
        _logging.getLogger(self._exe).debug("called with %s", self.args)
        returncode = self._open_process(*self.args, **kwargs)
        if returncode and not kwargs.get("suppress", False):
            _logging.getLogger(self._exe).error(
                "returned non-zero exit status %s", returncode
            )
            raise _CalledProcessError(
                returncode, f"{self._exe} {' '.join(self.args)}"
            )

        return returncode

    def stdout(self) -> _t.MutableSequence[str]:
        """Consume accrued stdout by returning the lines of output.

        Assign new container to ``_stdout``.

        :return: List of captured stdout.
        """
        captured, self._stdout = self._stdout, _STDOut()
        return captured


class _Git(Subprocess):
    """Git commands as class attributes.

    @DynamicAttrs
    """

    def __init__(self) -> None:
        self.commands = [
            i.lstrip().split()[0]
            for i in _sp_out(["git", "help", "--all"]).decode().splitlines()
            if i.startswith("   ")
        ]
        super().__init__("git", commands=self.commands, loglevel="debug")

    def call(self, *args: str, **kwargs: bool) -> int:
        """Call partial git command instantiated in superclass.

        :param args: Command's positional arguments.
        :key file: File path to write the stdout stream to.
        :key capture: Pipe stream to self.
        :key devnull: Suppress output.
        :key suppress: Suppress errors and continue running.
        :raises NotARepositoryError: If not run from within a
            repository.
        :raises CalledProcessError: If error occurs in subprocess.
        :return: Exit status.
        """
        git_dir = _Path.cwd() / ".git"
        with _config.TempEnvVar(
            _os.environ, GIT_WORK_TREE=str(_Path.cwd()), GIT_DIR=str(git_dir)
        ):
            if "--bare" in args:
                del _os.environ["GIT_WORK_TREE"]

            try:
                return super().call(*args, **kwargs)

            except _CalledProcessError as err:
                if not git_dir.is_dir():
                    raise _exceptions.NotARepositoryError from err

                raise err


git = _Git()
