"""
pyaud.utils
===========

Shared classes and functions.
"""
from __future__ import annotations

import functools
import logging
import logging.handlers as logging_handlers
import os
import shutil
import sys
from pathlib import Path
from subprocess import PIPE, CalledProcessError, Popen
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

import pyblake2
from object_colors import Color

from .environ import env

colors = Color()
colors.populate_colors()


class PythonItems:
    """Scan a directory fo Python files.

    :param exclude: Files to exclude.
    """

    def __init__(self, *exclude: str) -> None:
        self.exclude = exclude
        self.items: List[str] = []
        self.files: List[str] = []

    def exclude_virtualenv(self) -> None:
        """Remove virtualenv dir."""
        venv_contents = [
            "bin",
            "include",
            "lib",
            "lib64",
            "pyvenv.cfg",
            "share",
            "src",
        ]
        for count, item in enumerate(list(self.items)):
            if os.path.isdir(item):
                contents = os.listdir(item)
                if all(os.path.basename(e) in contents for e in venv_contents):
                    self.items.pop(count)

    def exclude_unversioned(self) -> None:
        """Remove unversioned files from list."""
        for count, item in enumerate(list(self.items)):
            with Git(os.environ["PROJECT_DIR"], loglevel="debug") as git:
                returncode = git.ls_files(  # type: ignore
                    "--error-unmatch", item, devnull=True, suppress=True
                )
                if returncode:
                    self.items.pop(count)

    def get_files(self) -> None:
        """Get all relevant python files starting from project root."""
        self.items.clear()
        for glob_path in Path(env["PROJECT_DIR"]).rglob("*.py"):
            if glob_path.name in self.exclude:
                continue

            path = Path(glob_path)
            while str(path.parent) != env["PROJECT_DIR"]:
                path = path.parent

            # ensure there are no duplicate entries
            # ensure that any subdirectories of a parent are not added
            if path not in self.items and not any(
                str(path) in str(p) or str(p) in str(path) for p in self.items
            ):
                self.items.append(str(path))

    def get_file_paths(self) -> None:
        """Get all relevant python file paths starting from project
        root.
        """
        self.files.clear()
        for glob_path in Path(env["PROJECT_DIR"]).rglob("*.py"):
            if glob_path.name not in self.exclude:
                self.files.append(str(glob_path))


pyitems = PythonItems("whitelist.py", "conf.py", "setup.py")


class Subprocess:
    """Object oriented

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
        """Open process with ``Popen``. Pipe stream depending
        on the keyword arguments provided. Log errors to file
        regardless. Wait for process to finish and return it's
        exit-code.

        :param exe:     str: Subprocess executable.
        :param args:    tuple: Series of commands.
        :key file:      str: File path to write stream to.
        :key devnull:   bool: Suppress output.
        :key capture:   bool: Pipe stream to self.
        :key suppress:  bool: Suppress errors and continue running.
        :return:        int: Exit status.
        """
        pipeline = Popen([exe, *args], stdout=PIPE, stderr=PIPE)
        self._handle_stdout(pipeline, **kwargs)
        self._handle_stderr(pipeline)
        return pipeline.wait()

    def run(self, exe: str, *args: str, **kwargs: str) -> int:
        """Call subprocess run and manipulate error resolve.

        :param exe:     str: Subprocess executable.
        :param args:    str: Positional arguments for process called.
        :param kwargs:  str: Keyword arguments for handling stdout.
        :raises:        Exception: PyaudError.
        :return:        int: Exit status.
        """
        suppress = kwargs.get("suppress", env["SUPPRESS"])
        returncode = self.open_process(exe, *args, **kwargs)
        if returncode and not suppress:
            self.logger.error("returned non-zero exit status %s", returncode)
            raise PyaudSubprocessError(
                returncode, f"{self.exe} {' '.join(args)}"
            )

        return returncode


class Git(Subprocess):
    """Git commands as class attributes.

    @DynamicAttrs

    :param repo: Repository to perform ``git`` actions in.
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

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.saved_path)
        if not self.already_existed and not self._keep_repo():
            shutil.rmtree(self.enter_path)

    def call(self, *args: Any, **kwargs: Any) -> int:
        if "--bare" in args:
            del os.environ["GIT_WORK_TREE"]

        return super().call(*args, **kwargs)


class HashCap:
    """Analyze hashes for before and after. ``self.snapshot``, the
    ``list`` object, only holds a maximum of two snapshots for before
    and after.

    :param file: The path of the file to hash.
    """

    def __init__(self, file: Union[bytes, str, os.PathLike]) -> None:
        self.file = file
        self.before: Optional[str] = None
        self.after: Optional[str] = None
        self.compare = False
        self.new = not os.path.isfile(self.file)

    def _hash_file(self) -> str:
        """Open the files and inspect it to get its hash. Return the
        hash as a string.
        """
        with open(self.file, "rb") as lines:
            _hash = pyblake2.blake2b(lines.read())

        return _hash.hexdigest()

    def _compare(self) -> bool:
        """Compare two hashes in the ``snapshot`` list.

        :return:    Boolean: True for both match, False if they don't.
        """
        return self.before == self.after

    def __enter__(self) -> HashCap:
        if not self.new:
            self.before = self._hash_file()

        return self

    def __exit__(self, exc_type: str, exc_val: str, exc_tb: str) -> None:
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


class PyaudSubprocessError(CalledProcessError):
    """Raise a ``PyaudSubprocessError`` for non-zero subprocess
    exits.
    """


def check_command(func: Callable[..., int]) -> Callable[..., None]:
    """Run the routine common with all functions checking files in this
    package.

    :param func: Function to decorate.
    """

    @functools.wraps(func)
    def _wrapper(**kwargs: bool) -> None:
        if not pyitems.items:
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
                        len(pyitems.files)
                    )
                )

    return _wrapper


def get_branch() -> Optional[str]:
    """Get the current checked out branch of the project.

    :return: Name of branch.
    """
    with Git(env["PROJECT_DIR"], loglevel="debug") as git:
        git.symbolic_ref(  # type: ignore
            "--short", "HEAD", capture=True, suppress=True
        )
        if git.stdout is not None:
            return git.stdout.strip()

        return None


def get_logger(logname: str) -> logging.Logger:
    """Set the name of ``~/.cache/pyaud/log/*/<logfile>.log``. Get the
    new or already existing ``Logging`` object by ``logname`` with
    ``logging.getLogger``. Prevent multiple handlers from pointing to
    the same logging object at once by setting ``propagate`` to False.
    Log to files using ``TimedRotatingFileHandler`` with a daily rotate.
    If any handlers already exist within a logging object remove the
    handler and update so multiple handlers do not log at once and cause
    unnecessary duplicates in logfiles.

    :param logname:     Name to be logged to file
    :return:            ``Logging`` callable e.g. call as
                        ``logger.<[debug, info, warning, etc.]>(msg)``
    """

    logfile = os.path.join(env["LOG_DIR"], env["PKG"] + ".log")
    logger = logging.getLogger(logname)
    logger.propagate = False
    filehandler = logging_handlers.TimedRotatingFileHandler(
        logfile, when="d", interval=1, backupCount=60
    )
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logger.setLevel(env["LOG_LEVEL"])
    if logger.hasHandlers():
        logger.handlers.clear()

    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    return logger


def write_command(
    file: Union[bytes, str, os.PathLike],
    required: Optional[Union[bytes, str, os.PathLike]] = None,
) -> Callable[..., Any]:
    """Run the routine common with all functions manipulating files in
    this package.

    :param file:        File which is to be written to.
    :param required:    Any required files.
    """

    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            if not required or os.path.exists(env[required]):
                _file = env[file]
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
    """Change to the selected directory entered as an argument and when
    actions are complete return to the previous directory

    :param new_path: Enter the directory to temporarily change to
    """

    def __init__(self, new_path):
        self.saved_path = os.getcwd()
        self.enter_path = os.path.expanduser(new_path)

    def __enter__(self):
        os.chdir(self.enter_path)

    def __exit__(self, _, value, __):
        os.chdir(self.saved_path)


def deploy_docs(url: Union[bool, str]) -> None:
    """Series of functions for deploying docs.

    :param url: URL to push documentation to.
    """
    with Git(env["PROJECT_DIR"]) as git:
        git.add(".")  # type: ignore
        git.diff_index("--cached", "HEAD", capture=True)  # type: ignore
        stashed = False
        if git.stdout is not None:
            git.stash(devnull=True)  # type: ignore
            stashed = True

        shutil.move(os.path.join(env["DOCS_BUILD"], "html"), ".")
        shutil.copy("README.rst", os.path.join("html", "README.rst"))

        git.rev_list("--max-parents=0", "HEAD", capture=True)  # type: ignore
        if git.stdout is not None:
            git.checkout(git.stdout.strip())  # type: ignore

        git.checkout("--orphan", "gh-pages")  # type: ignore
        git.config("--global", "user.name", env["GH_NAME"])  # type: ignore
        git.config("--global", "user.email", env["GH_EMAIL"])  # type: ignore
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
        git.remote("add", "origin", url)  # type: ignore
        git.fetch()  # type: ignore
        git.ls_remote("--heads", url, "gh-pages", capture=True)  # type: ignore
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
