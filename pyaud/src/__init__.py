"""
pyaud.src
==========

Shared classes and functions.
"""
from __future__ import annotations

import functools
import logging
import logging.handlers
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Optional, Iterable, Union, List, Dict, Callable, Any

import object_colors
import pyblake2

from . import environ

colors = object_colors.Color()


class PythonItems:
    """Scan a directory fo Python files.

    :param exclude: Files to exclude.
    """

    def __init__(self, *exclude: str) -> None:
        self.exclude = exclude
        self.items: List[str] = []

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
        for glob_path in pathlib.Path(environ.env["PROJECT_DIR"]).rglob(
            "*.py"
        ):
            if glob_path.name in self.exclude:
                continue

            path = pathlib.Path(glob_path)
            while str(path.parent) != environ.env["PROJECT_DIR"]:
                path = path.parent

            # ensure there are no duplicate entries
            # ensure that any subdirectories of a parent are not added
            if path not in self.items and not any(
                str(path) in str(p) or str(p) in str(path) for p in self.items
            ):
                self.items.append(str(path))


pyitems = PythonItems("whitelist.py", "conf.py")


class Subprocess:
    """Object oriented subprocess.

    :param exe:         Subprocess executable.
    :param loglevel:    Level to log the application under.
    :param commands:    Any additional commands to set as attributes.
    """

    def __init__(
        self,
        exe: str,
        loglevel: str = "error",
        commands: Optional[Iterable] = None,
        stdout: Optional[str] = None,
    ) -> None:
        self.exe = exe
        self.loglevel = loglevel
        self.commands = commands
        self._call = functools.partial(self.run, self.exe)
        self.stdout = stdout
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

    def _handle_stdout(
        self, pipeline: subprocess.Popen, **kwargs: str
    ) -> None:
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

    def _handle_stderr(self, pipeline: subprocess.Popen) -> None:
        for line in iter(pipeline.stderr.readline, b""):  # type: ignore
            getattr(self.logger, self.loglevel)(
                line.decode("utf-8", "ignore").strip()
            )

    def open_process(self, exe: str, *args: str, **kwargs: str) -> int:
        """Open process with ``subprocess.Popen``. Pipe stream depending
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
        pipe = subprocess.PIPE
        pipeline = subprocess.Popen([exe, *args], stdout=pipe, stderr=pipe)
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
        suppress = kwargs.get("suppress", environ.env["SUPPRESS"])
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

    def __init__(self, repo: Union[str, os.PathLike], loglevel="info") -> None:
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
        return self.call("clone", source, *args, **kwargs)

    def __enter__(self) -> Git:
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


# noinspection PyClassHasNoInit
class Tally:
    """Count elements of package."""

    @staticmethod
    def tests(*args: str) -> int:
        """Count the number of tests in a testing suite.

        :param args:    Pattern to search for when running glob on
                            directory.
        :return:            int: Number of tests in suite.
        """
        total = 0
        for arg in args:
            for file in pathlib.Path(environ.env["PROJECT_DIR"]).rglob(arg):
                with open(file) as fin:
                    for line in fin.read().splitlines():
                        if "def test_" in line:
                            total += 1

        return total

    @classmethod
    def pyfiles(cls, *args: str) -> int:
        """Return the quantity of files traversing the given paths
        recursively.

        :param args: Paths to count.
        """

        total = 0
        for arg in args:
            if os.path.isfile(arg) and arg.endswith(".py"):
                total += 1

            elif os.path.isdir(arg) and os.path.basename(arg) != "__pycache__":
                for item in os.listdir(arg):
                    total += cls.pyfiles(os.path.join(arg, item))

        return total


class LineSwitch:
    """Take the ``path`` and ``replace`` argument from the commandline
    and reformat the README whilst returning the original title to
    the parent process.

    :param file:    File to manipulate.
    :param lines:   Dictionary of line number's as key and replacement
                    strings as values.
    """

    def __init__(
        self, file: Union[bytes, str, os.PathLike], lines: Dict[int, str]
    ) -> None:
        self.file = file
        self.lines = lines
        with open(self.file) as fin:
            self.readlines = fin.read().splitlines()

        self.store = self.readlines.copy()

    def _write_file(self, fin: List[str]) -> None:
        with open(self.file, "w") as file:
            for line in fin:
                file.write(line + "\n")

    def __enter__(self) -> None:
        for key, value in self.lines.items():
            self.readlines[key] = value

        self._write_file(self.readlines)

    def __exit__(self, exc_type: str, exc_val: str, exc_tb: str) -> None:
        self._write_file(self.store)


class PyaudSubprocessError(subprocess.CalledProcessError):
    """Raise a ``PyaudSubprocessError`` for non-zero subprocess
    exits.
    """


def check_command(func: Callable[..., int]) -> Callable[..., int]:
    """Run the routine common with all functions checking files in this
    package.

    :param func: Function to decorate.
    """

    @functools.wraps(func)
    def _wrapper(**kwargs):
        _pyitems = pyitems.items
        if func.__name__ == "make_docs":
            _requires = os.path.isfile(environ.env["DOCS_CONF"])
            success = "Build successful"
            _type = "docs"
        else:
            _requires = [str(f) for f in pyitems.items if os.path.exists(f)]
            success = "Success: no issues found in "
            _type = "files"
            if func.__name__ in ("make_tests", "make_coverage"):
                total = Tally.tests("test_*.py", "*_test.py")
                success += f"{total} tests"
            else:
                quantity = Tally.pyfiles(*_pyitems)
                success += f"{quantity} source files"

        if _requires:
            returncode = func(**kwargs)
            if returncode:
                print(
                    colors.red.bold.get(
                        f"Failed: returned non-zero exit status {returncode}"
                    ),
                    file=sys.stderr,
                )
            else:

                colors.green.bold.print(success)
        else:
            print(f"No {_type} found")

        return 0

    return _wrapper


def get_branch() -> Optional[str]:
    """Get the current checked out branch of the project.

    :return: Name of branch.
    """
    with Git(environ.env["PROJECT_DIR"], loglevel="debug") as git:
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

    logfile = os.path.join(environ.env["LOG_DIR"], environ.env["PKG"] + ".log")
    logger = logging.getLogger(logname)
    logger.propagate = False
    filehandler = logging.handlers.TimedRotatingFileHandler(
        logfile, when="d", interval=1, backupCount=60
    )
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logger.setLevel(environ.env["LOG_LEVEL"])
    if logger.hasHandlers():
        logger.handlers.clear()

    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    return logger


def print_command(func) -> None:
    """Display the command being run.

    :param func: Function for ``__name__``.
    """
    print()
    colors.cyan.bold.print(
        func.__name__.replace("make_", "pyaud ").replace("_", "-")
    )


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
            if not required or os.path.exists(environ.env[required]):
                _file = environ.env[file]
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


class DeployDocs(Git):
    """Deploy documentation to ``gh-pages`` with git."""

    def __init__(self, repo: Union[str, os.PathLike], url: str) -> None:
        super().__init__(repo)
        self.url = url
        self.stashed = False

    def _dirty_tree(self) -> Optional[str]:
        self.add(".")  # type: ignore
        self.diff_index("--cached", "HEAD", capture=True)  # type: ignore
        return self.stdout

    @staticmethod
    def _remove_prefix() -> None:
        shutil.move(os.path.join("docs", "_build", "html"), ".")
        shutil.copy("README.rst", os.path.join("html", "README.rst"))

    def _checkout_root(self) -> None:
        self.rev_list("--max-parents=0", "HEAD", capture=True)  # type: ignore
        self.checkout(self.stdout.strip())  # type: ignore

    def _stash(self, *args) -> None:
        if not args:
            self.stashed = True

        self.stash(*args, devnull=True)  # type: ignore

    def _config(self) -> None:
        self.config(  # type: ignore
            "--global", "user.name", environ.env["GH_NAME"]
        )
        self.config(  # type: ignore
            "--global", "user.email", environ.env["GH_EMAIL"]
        )

    def _commit(self) -> None:
        self.add(".")  # type: ignore
        self.commit(  # type: ignore
            "-m",
            '"[ci skip] Publishes updated documentation"',
            devnull=True,
        )

    def _config_remote(self) -> None:
        self.remote("rm", "origin")  # type: ignore
        self.remote("add", "origin", self.url)  # type: ignore

    def _remote_exists(self) -> Optional[str]:
        self.fetch()  # type: ignore
        self.ls_remote(  # type: ignore
            "--heads", self.url, "gh-pages", capture=True
        )
        return self.stdout

    def _remote_diff(self) -> Optional[str]:
        self.diff("gh-pages", "origin/gh-pages", capture=True)  # type: ignore
        return self.stdout

    def deploy_docs(self) -> None:
        """Series of functions for deploying docs."""
        if self._dirty_tree():
            self._stash()

        self._remove_prefix()
        self._checkout_root()
        self.checkout("--orphan", "gh-pages")  # type: ignore
        self._config()
        shutil.rmtree("docs")
        self.rm("-rf", ".", devnull=True)  # type: ignore
        self.clean("-fdx", "--exclude=html", devnull=True)  # type: ignore
        for file in os.listdir("html"):
            shutil.move(os.path.join("html", file), ".")

        shutil.rmtree("html")
        self._commit()
        self._config_remote()

        if self._remote_exists() and not self._remote_diff():
            colors.green.print("No difference between local branch and remote")
            print("Pushing skipped")
        else:
            colors.green.print("Pushing updated documentation")
            self.push("origin", "gh-pages", "-f")  # type: ignore
            print("Documentation Successfully deployed")

        self.checkout("master", devnull=True)  # type: ignore
        if self.stashed:
            self.stash("pop", devnull=True)  # type: ignore

        self.branch("-D", "gh-pages", devnull=True)  # type: ignore


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
