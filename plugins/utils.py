"""
plugins.utils
=============
"""
import os
import shutil
from pathlib import Path
from typing import Any, Dict

from object_colors import Color

import pyaud

DOCS = Path("docs")
README = Path("README.rst")

colors = Color()
colors.populate_colors()


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


def deploy_docs() -> None:
    """Series of functions for deploying docs."""
    gh_remote = os.environ["PYAUD_GH_REMOTE"]
    root_html = Path.cwd() / "html"
    pyaud.git.add(".")  # type: ignore
    pyaud.git.diff_index("--cached", "HEAD", capture=True)  # type: ignore
    stashed = False
    if pyaud.git.stdout():
        pyaud.git.stash(devnull=True)  # type: ignore
        stashed = True

    shutil.move(str(Path.cwd() / os.environ["BUILDDIR"] / "html"), root_html)
    shutil.copy(Path.cwd() / README, root_html / README)
    pyaud.git.rev_list("--max-parents=0", "HEAD", capture=True)  # type: ignore
    stdout = pyaud.git.stdout()
    if stdout:
        pyaud.git.checkout(stdout[-1])  # type: ignore

    pyaud.git.checkout("--orphan", "gh-pages")  # type: ignore
    pyaud.git.config(  # type: ignore
        "--global", "user.name", os.environ["PYAUD_GH_NAME"]
    )
    pyaud.git.config(  # type: ignore
        "--global", "user.email", os.environ["PYAUD_GH_EMAIL"]
    )
    shutil.rmtree(Path.cwd() / DOCS)
    pyaud.git.rm("-rf", Path.cwd(), devnull=True)  # type: ignore
    pyaud.git.clean("-fdx", "--exclude=html", devnull=True)  # type: ignore
    for file in root_html.rglob("*"):
        shutil.move(str(file), Path.cwd() / file.name)

    shutil.rmtree(root_html)
    pyaud.git.add(".")  # type: ignore
    pyaud.git.commit(  # type: ignore
        "-m", '"[ci skip] Publishes updated documentation"', devnull=True
    )
    pyaud.git.remote("rm", "origin")  # type: ignore
    pyaud.git.remote("add", "origin", gh_remote)  # type: ignore
    pyaud.git.fetch()  # type: ignore
    pyaud.git.stdout()
    pyaud.git.ls_remote(  # type: ignore
        "--heads", gh_remote, "gh-pages", capture=True
    )
    result = pyaud.git.stdout()
    remote_exists = None if not result else result[-1]
    pyaud.git.diff(  # type: ignore
        "gh-pages", "origin/gh-pages", suppress=True, capture=True
    )
    result = pyaud.git.stdout()
    remote_diff = None if not result else result[-1]
    if remote_exists is not None and remote_diff is None:
        colors.green.print("No difference between local branch and remote")
        print("Pushing skipped")
    else:
        colors.green.print("Pushing updated documentation")
        pyaud.git.push("origin", "gh-pages", "-f")  # type: ignore
        print("Documentation Successfully deployed")

    pyaud.git.checkout("master", devnull=True)  # type: ignore
    if stashed:
        pyaud.git.stash("pop", devnull=True)  # type: ignore

    pyaud.git.branch("-D", "gh-pages", devnull=True)  # type: ignore
