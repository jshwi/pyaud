"""
pyaud.utils
===========

Utility classes and functions.
"""
from __future__ import annotations

import functools
import logging
import os
import shutil
import sys
from collections.abc import MutableSequence
from pathlib import Path
from subprocess import PIPE, CalledProcessError, Popen
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import pyblake2
from object_colors import Color

from .config import toml
from .environ import DOCS, README, TempEnvVar

colors = Color()
colors.populate_colors()


class Subprocess:
    """Object oriented Subprocess.

    ``exe`` is a mandatory argument used to construct the subprocess
    executable. Default ``file``, ``capture``, and ``devnull`` values
    can be set when instantiating the object and overridden later when
    using ``call``.


    :param exe:         Subprocess executable.
    :key loglevel:      Loglevel for non-error logging.
    :param commands:    List of positional arguments to set as
                        attributes if not None.
    :key file:          File path to write stream to if not None.
    :key capture:       Collect output array.
    :key log:           Pipe stdout to logging instead of console.
    :key devnull:       Send output to /dev/null.
    """

    def __init__(
        self,
        exe: str,
        loglevel: str = "error",
        commands: Optional[Iterable[str]] = None,
        **kwargs: Union[bool, str],
    ) -> None:
        self._exe = exe
        self._loglevel = loglevel
        if commands is not None:
            for command in commands:
                setattr(
                    self,
                    command.replace("-", "_"),
                    functools.partial(self.call, command),
                )

        self._kwargs = kwargs
        self._stdout: List[str] = []
        self.args: Tuple[str, ...] = ()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} ({self._exe})>"

    def _handle_stdout(
        self, pipeline: Popen, **kwargs: Union[bool, str]
    ) -> None:
        if pipeline.stdout is not None:
            for line in iter(pipeline.stdout.readline, b""):
                line = line.decode("utf-8", "ignore")
                file = kwargs.get("file", self._kwargs.get("file", None))
                if file is not None:
                    with open(file, "a+") as fout:
                        fout.write(line)

                elif kwargs.get("capture", self._kwargs.get("capture", False)):
                    self._stdout.append(line.strip())

                elif kwargs.get("devnull", self._kwargs.get("devnull", False)):
                    with open(os.devnull, "w") as fout:
                        fout.write(line)

                else:
                    sys.stdout.write(line)

    def _handle_stderr(self, pipeline: Popen) -> None:
        for line in iter(pipeline.stderr.readline, b""):  # type: ignore
            getattr(logging.getLogger(self._exe), self._loglevel)(
                line.decode("utf-8", "ignore").strip()
            )

    def _open_process(self, *args: str, **kwargs: Union[bool, str]) -> int:
        # open process with ``subprocess.Popen``
        # pipe stream depending on the keyword arguments provided
        # Log errors to file regardless
        # wait for process to finish and return it's exit-code
        pipeline = Popen([self._exe, *args], stdout=PIPE, stderr=PIPE)
        self._handle_stdout(pipeline, **kwargs)
        self._handle_stderr(pipeline)
        return pipeline.wait()

    def call(self, *args: Any, **kwargs: Any) -> int:
        """Call command. Open process with ``subprocess.Popen``.

        Pipe stream depending on the keyword arguments provided to
        instance constructor or overridden through this method. If a
        file path is provided it will take precedence over the other
        options, then capture and then finally devnull. Log errors to
        file regardless. Wait for process to finish and return it's
        exit-code.

        :param args:                Positional str arguments.
        :key file:                  File path to write stream to if not
                                    None.
        :key devnull:               Send output to /dev/null.
        :key capture:               Collect output array.
        :key suppress:              Suppress errors and continue
                                    running.
        :raises CalledProcessError: If error occurs in subprocess.
        :return:                    Exit status.
        """
        self.args = tuple([str(i) for i in args])
        logging.getLogger(self._exe).debug("called with %s", self.args)
        returncode = self._open_process(*self.args, **kwargs)
        if returncode and not kwargs.get("suppress", False):
            logging.getLogger(self._exe).error(
                "returned non-zero exit status %s", returncode
            )
            raise CalledProcessError(
                returncode, f"{self._exe} {' '.join(self.args)}"
            )

        return returncode

    def stdout(self) -> List[str]:
        """Consume accrued stdout by returning the lines of output.

        Assign new container to ``_stdout``.

        :return: List of captured stdout.
        """
        captured, self._stdout = self._stdout, []
        return captured


class _Git(Subprocess):
    """Git commands as class attributes.

    @DynamicAttrs
    """

    commands = (
        "add",
        "apply",
        "branch",
        "checkout",
        "clean",
        "clone",
        "commit",
        "config",
        "diff",
        "diff-index",
        "fetch",
        "init",
        "ls-files",
        "ls-remote",
        "push",
        "remote",
        "rev-list",
        "rev-parse",
        "rm",
        "stash",
        "symbolic-ref",
    )

    def __init__(self) -> None:
        super().__init__("git", commands=self.commands, loglevel="debug")

    def call(self, *args: Any, **kwargs: Any) -> int:
        """Call partial git command instantiated in superclass.

        :param args:                Command's positional arguments.
        :key file:                  File path to write the stdout stream
                                    to.
        :key capture:               Pipe stream to self.
        :key devnull:               Suppress output.
        :key suppress:              Suppress errors and continue
                                    running.
        :raises CalledProcessError: If error occurs in subprocess.
        :return:                    Exit status.
        """
        with TempEnvVar(
            os.environ,
            GIT_WORK_TREE=str(Path.cwd()),
            GIT_DIR=str(Path.cwd() / ".git"),
        ):
            if "--bare" in args:
                del os.environ["GIT_WORK_TREE"]

            return super().call(*args, **kwargs)


class HashCap:
    """Analyze hashes for before and after.

    :param file: The path of the file to hash.
    """

    def __init__(self, file: Path) -> None:
        self.file = file
        self.before: Optional[str] = None
        self.after: Optional[str] = None
        self.compare = False
        self.new = not self.file.is_file()

    def _hash_file(self) -> str:
        """Open the files and inspect it to get its hash.

        :return: Hash as a string.
        """
        with open(self.file, "rb") as lines:
            _hash = pyblake2.blake2b(lines.read())

        return _hash.hexdigest()

    def _compare(self) -> bool:
        """Compare two hashes in the ``snapshot`` list.

        :return: Boolean: True for both match, False if they don't.
        """
        return self.before == self.after

    def __enter__(self) -> HashCap:
        if not self.new:
            self.before = self._hash_file()

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            self.after = self._hash_file()
        except FileNotFoundError:
            pass

        self.compare = self._compare()


class LineSwitch:
    """Take the ``path`` and ``replace`` argument from the commandline.

    Reformat the README whilst returning the original title to the
    parent process.

    :param path:    File to manipulate.
    :param obj:     Dictionary of line number's as key and replacement
                    strings as values.
    """

    def __init__(self, path: Path, obj: Dict[int, str]) -> None:
        self._path = path
        self._obj = obj
        with open(path) as fin:
            self.read = fin.read()

    def __enter__(self) -> None:
        with open(self._path, "w") as file:
            for count, line in enumerate(self.read.splitlines()):
                if count in self._obj:
                    line = self._obj[count]

                file.write(f"{line}\n")

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        with open(self._path, "w") as file:
            file.write(self.read)


def check_command(func: Callable[..., int]) -> Callable[..., None]:
    """Run the routine common with all functions in this package.

    :param func:    Function to decorate.
    :return:        Wrapped function.
    """

    @functools.wraps(func)
    def _wrapper(**kwargs: bool) -> None:
        if not tree.reduce():
            print("No files found")
        else:
            returncode = func(**kwargs)
            if returncode:
                colors.red.bold.print(
                    f"Failed: returned non-zero exit status {returncode}",
                    file=sys.stderr,
                )
            else:
                colors.green.bold.print(
                    "Success: no issues found in {} source files".format(
                        len(tree)
                    )
                )

    return _wrapper


def get_branch() -> Optional[str]:
    """Get the current checked out branch of the project.

    :return: Name of branch or None if on a branch with no parent.
    """
    git.symbolic_ref(  # type: ignore
        "--short", "HEAD", suppress=True, capture=True
    )
    stdout = git.stdout()
    if stdout:
        return stdout[-1]

    return None


def write_command(
    file: Union[bytes, str, os.PathLike],
    required: Optional[Union[bytes, str, os.PathLike]] = None,
) -> Callable[..., Any]:
    """Run the routine common with all functions manipulating files.

    :param file:        File which is to be written to.
    :param required:    Any required files.
    :return:            Wrapped function.
    """

    def _decorator(func: Callable[..., int]) -> Callable[..., None]:
        @functools.wraps(func)
        def _wrapper(*args: str, **kwargs: Union[bool, str]) -> None:
            if (
                not required
                or Path(Path.cwd() / os.environ[str(required)]).exists()
            ):
                _file = Path.cwd() / os.environ[str(file)]
                print(f"Updating ``{_file}``")
                with HashCap(_file) as cap:
                    func(*args, **kwargs)

                if cap.new:
                    print(f"created ``{_file.name}``")

                elif cap.compare:
                    print(f"``{_file.name}`` is already up to date")
                else:
                    print(f"updated ``{_file.name}``")

        return _wrapper

    return _decorator


def deploy_docs() -> None:
    """Series of functions for deploying docs."""
    gh_remote = os.environ["PYAUD_GH_REMOTE"]
    root_html = Path.cwd() / "html"
    git.add(".")  # type: ignore
    git.diff_index("--cached", "HEAD", capture=True)  # type: ignore
    stashed = False
    if git.stdout():
        git.stash(devnull=True)  # type: ignore
        stashed = True

    shutil.move(str(Path.cwd() / os.environ["BUILDDIR"] / "html"), root_html)
    shutil.copy(Path.cwd() / README, root_html / README)
    git.rev_list("--max-parents=0", "HEAD", capture=True)  # type: ignore
    stdout = git.stdout()
    if stdout:
        git.checkout(stdout[-1])  # type: ignore

    git.checkout("--orphan", "gh-pages")  # type: ignore
    git.config(  # type: ignore
        "--global", "user.name", os.environ["PYAUD_GH_NAME"]
    )
    git.config(  # type: ignore
        "--global", "user.email", os.environ["PYAUD_GH_EMAIL"]
    )
    shutil.rmtree(Path.cwd() / DOCS)
    git.rm("-rf", Path.cwd(), devnull=True)  # type: ignore
    git.clean("-fdx", "--exclude=html", devnull=True)  # type: ignore
    for file in root_html.rglob("*"):
        shutil.move(str(file), Path.cwd() / file.name)

    shutil.rmtree(root_html)
    git.add(".")  # type: ignore
    git.commit(  # type: ignore
        "-m", '"[ci skip] Publishes updated documentation"', devnull=True
    )
    git.remote("rm", "origin")  # type: ignore
    git.remote("add", "origin", gh_remote)  # type: ignore
    git.fetch()  # type: ignore
    git.stdout()
    git.ls_remote(  # type: ignore
        "--heads", gh_remote, "gh-pages", capture=True
    )
    result = git.stdout()
    remote_exists = None if not result else result[-1]
    git.diff(  # type: ignore
        "gh-pages", "origin/gh-pages", suppress=True, capture=True
    )
    result = git.stdout()
    remote_diff = None if not result else result[-1]
    if remote_exists is not None and remote_diff is None:
        colors.green.print("No difference between local branch and remote")
        print("Pushing skipped")
    else:
        colors.green.print("Pushing updated documentation")
        git.push("origin", "gh-pages", "-f")  # type: ignore
        print("Documentation Successfully deployed")

    git.checkout("master", devnull=True)  # type: ignore
    if stashed:
        git.stash("pop", devnull=True)  # type: ignore

    git.branch("-D", "gh-pages", devnull=True)  # type: ignore


class PyAuditError(Exception):
    """Raise for audit failures that aren't failed subprocesses.

    :param cmd: Optional str. If no argument provided the value will be
                None.
    """

    def __init__(self, cmd: Optional[str]) -> None:
        super().__init__(f"{cmd} did not pass all checks")


class _MutableSequence(MutableSequence):  # pylint: disable=too-many-ancestors
    """Inherit to replicate subclassing of ``list`` objects."""

    def __init__(self) -> None:
        self._list: List[Any] = list()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._list}>"

    def __len__(self) -> int:
        return self._list.__len__()

    def __delitem__(self, key: Any) -> None:
        self._list.__delitem__(key)

    def __setitem__(self, index: Any, value: Any) -> None:
        self._list.__setitem__(index, value)

    def __getitem__(self, index: Any) -> Any:
        return self._list.__getitem__(index)

    def insert(self, index: int, value: str) -> None:
        """Insert values into ``_list`` object.

        :param index:   ``list`` index to insert ``value``.
        :param value:   Value to insert into list.
        """
        self._list.insert(index, value)


class _Tree(_MutableSequence):  # pylint: disable=too-many-ancestors
    """Index all Python files in project.

    :param exclude: Files to exclude.
    """

    def __init__(self, *exclude: str) -> None:
        super().__init__()
        self._exclude = exclude

    def populate(self) -> None:
        """Populate object with repository index.

        Exclude items not in version-control.
        """
        for path in Path.cwd().rglob("*.py"):
            if (
                path.name not in self._exclude
                and not git.ls_files(  # type: ignore
                    "--error-unmatch", path, devnull=True, suppress=True
                )
            ):
                self.append(path)

    def reduce(self) -> List[Path]:
        """Get all relevant python files starting from project root.

        :return:    List of project's Python file index, reduced to
                    their root, relative to $PROJECT_DIR. Contains no
                    duplicate items so $PROJECT_DIR/dir/file1.py and
                    $PROJECT_DIR/dir/file2.py become
                    $PROJECT_DIR/dir but PROJECT_DIR/file1.py
                    and $PROJECT_DIR/file2.py remain as they are.
        """
        project_dir = Path.cwd()
        return list(
            set(
                project_dir / p.relative_to(project_dir).parts[0] for p in self
            )
        )


tree = _Tree(*toml["indexing"]["exclude"])
git = _Git()
