"""
pyaud.utils
===========

Utility classes and functions.
"""
from __future__ import annotations

import functools
import logging
import logging.handlers as logging_handlers
import os
import shutil
import sys
from collections.abc import MutableSequence
from pathlib import Path
from subprocess import PIPE, CalledProcessError, Popen
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

import pyblake2
from object_colors import Color

colors = Color()
colors.populate_colors()


class Subprocess:
    """Object oriented Subprocess.

    :param exe:         Subprocess executable.
    :param loglevel:    Level to log the application under.
    :param commands:    Any additional commands to set as attributes.
    """

    def __init__(
        self,
        exe: str,
        loglevel: str = "error",
        commands: Optional[Iterable] = None,
    ) -> None:
        self.exe = exe
        self.loglevel = loglevel
        self.commands = commands
        self._call = functools.partial(self.run, self.exe)
        self.stdout: Optional[str] = None
        self.logger = get_logger(self.exe)
        self._set_attrs()

    def call(
        self, *args: Union[bytes, str, os.PathLike], **kwargs: Union[bool, str]
    ) -> int:
        """Call command.

        :param args:    Command's positional arguments.
        :param kwargs:  Command's keyword arguments.
        :return:        Exit status.
        """
        self.logger.debug("called with %s", args)
        return self._call(*args, **kwargs)

    def _capture(self, line: str) -> None:
        if self.stdout is not None:
            self.stdout += line
        else:
            self.stdout = line

    def _set_attrs(self) -> None:
        if self.commands:
            for command in self.commands:
                func = functools.partial(self.call, command)
                _name = command.replace("-", "_")
                setattr(self, _name, func)

    def _handle_stdout(self, pipeline: Popen, **kwargs: str) -> None:
        self.stdout = None
        file = kwargs.get("file", None)
        capture = kwargs.get("capture", False)
        devnull = kwargs.get("devnull", False)
        for line in iter(lambda: pipeline.stdout.read(1), b""):  # type: ignore
            line = line.decode("utf-8", "ignore")
            if capture:
                self._capture(line)

            elif file:
                with open(file, "a+") as fout:
                    fout.write(line)

            elif not devnull:
                sys.stdout.write(line)

    def _handle_stderr(self, pipeline: Popen) -> None:
        for line in iter(pipeline.stderr.readline, b""):  # type: ignore
            getattr(self.logger, self.loglevel)(
                line.decode("utf-8", "ignore").strip()
            )

    def open_process(self, exe: str, *args: str, **kwargs: str) -> int:
        """Open process with ``subprocess.Popen``.

        Pipe stream depending on the keyword arguments provided. Log
        errors to file regardless. Wait for process to finish and return
        it's exit-code.

        :param exe:     Subprocess executable.
        :param args:    Series of commands.
        :key file:      File path to write stream to.
        :key devnull:   Suppress output.
        :key capture:   Pipe stream to self.
        :key suppress:  Suppress errors and continue running.
        :return:        Exit status.
        """
        pipeline = Popen([exe, *args], stdout=PIPE, stderr=PIPE)
        self._handle_stdout(pipeline, **kwargs)
        self._handle_stderr(pipeline)
        return pipeline.wait()

    def run(self, exe: str, *args: str, **kwargs: str) -> int:
        """Call subprocess run and manipulate error resolve.

        :param exe:                 Subprocess executable.
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
        returncode = self.open_process(exe, *args, **kwargs)
        if returncode and not kwargs.get("suppress", False):
            self.logger.error("returned non-zero exit status %s", returncode)
            raise CalledProcessError(
                returncode, f"{self.exe} {' '.join(args)}"
            )

        return returncode


class Git(Subprocess):
    """Git commands as class attributes.

    @DynamicAttrs

    :param repo:        Repository to perform ``git`` actions in.
    :param loglevel:    Loglevel to log git actions under.
    """

    commands = (
        "add",
        "apply",
        "branch",
        "checkout",
        "clean",
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

    def __init__(
        self, repo: Union[str, os.PathLike], loglevel="debug"
    ) -> None:
        super().__init__("git", commands=self.commands, loglevel=loglevel)
        self.enter_path = repo
        self.saved_path = os.getcwd()
        self.already_existed = os.path.isdir(repo)

    def clone(self, source: str, *args: str, **kwargs: str) -> int:
        """Clone repository to entered path.

        :param source:  Source repository to clone.
        :param args:    Arguments to be combined with ``git clone``.
        :param kwargs:  Keyword arguments passed to ``git clone``
        :return:        Exit status.
        """
        args = list(args)  # type: ignore
        args.append(self.enter_path)  # type: ignore
        del os.environ["GIT_WORK_TREE"]
        return self.call("clone", source, *args, **kwargs)

    def __enter__(self) -> Git:
        os.environ.update(
            GIT_DIR=str(os.path.join(self.enter_path, ".git")),
            GIT_WORK_TREE=str(self.enter_path),
        )
        if not self.already_existed:
            os.makedirs(self.enter_path)

        os.chdir(self.enter_path)
        return self

    def _keep_repo(self) -> bool:
        git_internals = [
            "branches",
            "config",
            "description",
            "HEAD",
            "hooks",
            "info",
            "objects",
            "refs",
        ]
        baredir = all(
            os.path.exists(os.path.join(self.enter_path, i))
            for i in git_internals
        )
        return os.path.isdir(os.path.join(self.enter_path, ".git")) or baredir

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        os.chdir(self.saved_path)
        if not self.already_existed and not self._keep_repo():
            shutil.rmtree(self.enter_path)

    def call(self, *args: Any, **kwargs: Any) -> int:
        if "--bare" in args:
            del os.environ["GIT_WORK_TREE"]

        return super().call(*args, **kwargs)


class HashCap:
    """Analyze hashes for before and after.

    :param file: The path of the file to hash.
    """

    def __init__(self, file: Union[bytes, str, os.PathLike]) -> None:
        self.file = file
        self.before: Optional[str] = None
        self.after: Optional[str] = None
        self.compare = False
        self.new = not os.path.isfile(self.file)

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

    def __init__(
        self, path: Union[bytes, str, os.PathLike], obj: Dict[int, str]
    ) -> None:
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
    with Git(os.environ["PROJECT_DIR"], loglevel="debug") as git:
        git.symbolic_ref(  # type: ignore
            "--short", "HEAD", capture=True, suppress=True
        )
        if git.stdout is not None:
            return git.stdout.strip()

        return None


def get_logger(logname: str) -> logging.Logger:
    """Get package logger.

    Set the name of ``~/.cache/pyaud/log/*/<logfile>.log``. Get the new
    or already existing ``Logging`` object by ``logname`` with
    ``logging.getLogger``. Prevent multiple handlers from pointing to
    the same logging object at once by setting ``propagate`` to False.
    Log to files using ``TimedRotatingFileHandler`` with a daily rotate.
    If any handlers already exist within a logging object remove the
    handler and update so multiple handlers do not log at once and cause
    unnecessary duplicates in logfiles.

    :param logname: Name to be logged to file
    :return:        Logging object.
    """

    logfile = os.path.join(os.environ["PYAUD_LOGFILE"])
    logger = logging.getLogger(logname)
    logger.propagate = False
    filehandler = logging_handlers.TimedRotatingFileHandler(
        logfile, when="d", interval=1, backupCount=60
    )
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logger.setLevel(os.environ["PYAUD_LOG_LEVEL"])
    if logger.hasHandlers():
        logger.handlers.clear()

    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    return logger


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
            if not required or os.path.exists(os.environ[str(required)]):
                _file = os.environ[str(file)]
                print(f"Updating ``{_file}``")
                with HashCap(_file) as cap:
                    func(*args, **kwargs)

                _file_name = os.path.basename(_file)
                if cap.new:
                    print(f"created ``{_file_name}``")

                elif cap.compare:
                    print(f"``{_file_name}`` is already up to date")
                else:
                    print(f"updated ``{_file_name}``")

        return _wrapper

    return _decorator


class EnterDir:
    """Change to the selected directory.

    Once actions are complete return to the previous directory.

    :param new_path: Enter the directory to temporarily change to
    """

    def __init__(self, new_path: Union[bytes, str, os.PathLike]) -> None:
        self.saved_path = os.getcwd()
        self.enter_path = os.path.expanduser(new_path)

    def __enter__(self) -> None:
        os.chdir(self.enter_path)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        os.chdir(self.saved_path)


def deploy_docs() -> None:
    """Series of functions for deploying docs."""
    gh_remote = os.environ["PYAUD_GH_REMOTE"]
    with Git(os.environ["PROJECT_DIR"]) as git:
        git.add(".")  # type: ignore
        git.diff_index("--cached", "HEAD", capture=True)  # type: ignore
        stashed = False
        if git.stdout is not None:
            git.stash(devnull=True)  # type: ignore
            stashed = True

        shutil.move(os.path.join(os.environ["BUILDDIR"], "html"), ".")
        shutil.copy("README.rst", os.path.join("html", "README.rst"))

        git.rev_list("--max-parents=0", "HEAD", capture=True)  # type: ignore
        if git.stdout is not None:
            git.checkout(git.stdout.strip())  # type: ignore

        git.checkout("--orphan", "gh-pages")  # type: ignore
        git.config(  # type: ignore
            "--global", "user.name", os.environ["PYAUD_GH_NAME"]
        )
        git.config(  # type: ignore
            "--global", "user.email", os.environ["PYAUD_GH_EMAIL"]
        )
        shutil.rmtree("docs")
        git.rm("-rf", ".", devnull=True)  # type: ignore
        git.clean("-fdx", "--exclude=html", devnull=True)  # type: ignore
        for file in os.listdir("html"):
            shutil.move(os.path.join("html", file), ".")

        shutil.rmtree("html")
        git.add(".")  # type: ignore
        git.commit(  # type: ignore
            "-m", '"[ci skip] Publishes updated documentation"', devnull=True
        )
        git.remote("rm", "origin")  # type: ignore
        git.remote("add", "origin", gh_remote)  # type: ignore
        git.fetch()  # type: ignore
        git.ls_remote(  # type: ignore
            "--heads", gh_remote, "gh-pages", capture=True
        )
        remote_exists = git.stdout
        git.diff(  # type: ignore
            "gh-pages", "origin/gh-pages", suppress=True, capture=True
        )
        remote_diff = git.stdout
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
        project_dir = Path(os.environ["PROJECT_DIR"])
        for path in [str(p) for p in project_dir.rglob("*.py")]:
            if os.path.basename(path) not in self._exclude:
                with Git(os.environ["PROJECT_DIR"], loglevel="debug") as git:
                    if not git.ls_files(  # type: ignore
                        "--error-unmatch", path, devnull=True, suppress=True
                    ):
                        self.append(path)

    def reduce(self) -> List[str]:
        """Get all relevant python files starting from project root.

        :return:    List of project's Python file index, reduced to
                    their root, relative to $PROJECT_DIR. Contains no
                    duplicate items so $PROJECT_DIR/dir/file1.py and
                    $PROJECT_DIR/dir/file2.py become
                    $PROJECT_DIR/dir but PROJECT_DIR/file1.py
                    and $PROJECT_DIR/file2.py remain as they are.
        """
        project_dir = os.environ["PROJECT_DIR"]
        return list(
            set(
                os.path.join(
                    project_dir,
                    os.path.relpath(p, project_dir).split(os.sep)[0],
                )
                for p in self
            )
        )


tree = _Tree("whitelist.py", "conf.py", "setup.py")
