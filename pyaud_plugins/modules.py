"""
plugins.modules
===============
"""
import os
import shutil
import sys
import tempfile
import typing as t
from pathlib import Path

from object_colors import Color

import pyaud

DOCS = Path("docs")
README = Path("README.rst")

colors = Color()
colors.populate_colors()


@pyaud.plugins.register(name="clean")
class Clean(pyaud.plugins.Action):  # pylint: disable=too-few-public-methods
    """Remove all unversioned package files recursively."""

    def action(self, *args: t.Any, **kwargs: bool) -> int:
        exclude = pyaud.config.toml["clean"]["exclude"]
        return pyaud.git.clean(  # type: ignore
            "-fdx", *[f"--exclude={e}" for e in exclude], **kwargs
        )


@pyaud.plugins.register(name="tests")
class Tests(pyaud.plugins.Action):  # pylint: disable=too-few-public-methods
    """Run the package unit-tests with ``pytest``."""

    pytest = "pytest"
    cache = True
    cache_all = True

    @property
    def exe(self) -> t.List[str]:
        return [self.pytest]

    @property
    def is_tests(self) -> bool:
        """Confirm that a test suite exists.

        :return: Does a test suite exist? True or False.
        """
        tests = Path.cwd() / "tests"
        patterns = ("test_*.py", "*_test.py")
        rglob = [
            f
            for f in pyaud.files
            for p in patterns
            if f.match(p) and str(tests) in str(f)
        ]
        return rglob != []

    def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
        if self.is_tests:
            return self.subprocess[self.pytest].call(*args, **kwargs)

        print("No tests found")
        return 0


@pyaud.plugins.register(name="coverage")
class Coverage(Tests):  # pylint: disable=too-few-public-methods
    """Run package unit-tests with ``pytest`` and ``coverage``."""

    coverage = "coverage"

    @property
    def exe(self) -> t.List[str]:
        return super().exe + [self.coverage]

    def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
        returncode = super().action(
            *[f"--cov={e}" for e in pyaud.files.reduce()], **kwargs
        )
        if self.is_tests and not returncode:
            kwargs["suppress"] = True
            self.subprocess[self.coverage].call("xml", *args, **kwargs)
        else:
            print("No coverage to report")

        return returncode


@pyaud.plugins.register(name="deploy")
class Deploy(  # pylint: disable=too-few-public-methods
    pyaud.plugins.Parametrize
):
    """Deploy package documentation and test coverage."""

    def plugins(self) -> t.List[str]:
        return ["deploy-docs", "deploy-cov"]


@pyaud.plugins.register(name="deploy-cov")
class DeployCov(  # pylint: disable=too-few-public-methods
    pyaud.plugins.Action
):
    """Upload coverage data to ``Codecov``.

    If no file exists otherwise announce that no file has been created
    yet. If no ``CODECOV_TOKEN`` environment variable has been exported
    or defined in ``.env`` announce that no authorization token has been
    created yet.
    """

    codecov = "codecov"

    @property
    def exe(self) -> t.List[str]:
        return [self.codecov]

    def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
        coverage_xml = Path.cwd() / pyaud.environ.COVERAGE_XML
        if coverage_xml.is_file():
            if pyaud.environ.CODECOV_TOKEN is not None:
                self.subprocess[self.codecov].call(
                    "--file", Path.cwd() / coverage_xml, **kwargs
                )
            else:
                print("CODECOV_TOKEN not set")
        else:
            print("No coverage report found")


@pyaud.plugins.register(name="deploy-docs")
class DeployDocs(
    pyaud.plugins.Action
):  # pylint: disable=too-few-public-methods
    """Deploy package documentation to ``gh-pages``.

    Check that the branch is being pushed as master (or other branch
    for tests). If the correct branch is the one in use deploy.
    ``gh-pages`` to the orphaned branch - otherwise do nothing and
    announce.
    """

    _pushing_skipped = "Pushing skipped"

    def deploy_docs(self) -> None:
        """Series of functions for deploying docs."""
        gh_remote = pyaud.environ.GH_REMOTE
        root_html = Path.cwd() / "html"
        pyaud.git.add(".")  # type: ignore
        pyaud.git.diff_index("--cached", "HEAD", capture=True)  # type: ignore
        stashed = False
        if pyaud.git.stdout():
            pyaud.git.stash(devnull=True)  # type: ignore
            stashed = True

        shutil.move(
            str(Path.cwd() / pyaud.environ.BUILDDIR / "html"), root_html
        )
        shutil.copy(Path.cwd() / README, root_html / README)
        pyaud.git.rev_list(  # type: ignore
            "--max-parents=0", "HEAD", capture=True
        )
        stdout = pyaud.git.stdout()
        if stdout:
            pyaud.git.checkout(stdout[-1])  # type: ignore

        pyaud.git.checkout("--orphan", "gh-pages")  # type: ignore
        pyaud.git.config(  # type: ignore
            "--global", "user.name", pyaud.environ.GH_NAME
        )
        pyaud.git.config(  # type: ignore
            "--global", "user.email", pyaud.environ.GH_EMAIL
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
            print(self._pushing_skipped)
        else:
            colors.green.print("Pushing updated documentation")
            pyaud.git.push("origin", "gh-pages", "-f")  # type: ignore
            print("Documentation Successfully deployed")

        pyaud.git.checkout("master", devnull=True)  # type: ignore
        if stashed:
            pyaud.git.stash("pop", devnull=True)  # type: ignore

        pyaud.git.branch("-D", "gh-pages", devnull=True)  # type: ignore

    def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
        if pyaud.branch() == "master":
            git_credentials = ["GH_NAME", "GH_EMAIL", "GH_TOKEN"]
            null_vals = [
                k for k in git_credentials if getattr(pyaud.environ, k) is None
            ]
            if not null_vals:
                if not Path(
                    Path.cwd() / pyaud.environ.BUILDDIR / "html"
                ).is_dir():
                    pyaud.plugins.get("docs")(**kwargs)

                self.deploy_docs()
            else:
                print("The following is not set:")
                for null_val in null_vals:
                    print(f"- {pyaud.environ.PREFIX}{null_val}")

                print()
                print(self._pushing_skipped)
        else:
            colors.green.print("Documentation not for master")
            print(self._pushing_skipped)


@pyaud.plugins.register(name="docs")
class Docs(pyaud.plugins.Action):  # pylint: disable=too-few-public-methods
    """Compile package documentation with ``Sphinx``.

    This is so the hyperlink isn't exactly the same as the package
    documentation. Build the ``Sphinx`` html documentation. Return the
    README's title to what it originally was.
    """

    sphinx_build = "sphinx-build"
    m2r = "m2r"

    @property
    def exe(self) -> t.List[str]:
        return [self.sphinx_build]

    def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
        pyaud.plugins.get("toc")(*args, **kwargs)
        readme_rst = "README"
        underline = len(readme_rst) * "="
        build_dir = Path.cwd() / pyaud.environ.BUILDDIR
        if build_dir.is_dir():
            shutil.rmtree(build_dir)

        with pyaud.parsers.Md2Rst(Path.cwd() / "README.md", temp=True):
            if (
                Path(Path.cwd() / DOCS / "conf.py").is_file()
                and Path(Path.cwd(), README).is_file()
            ):
                with pyaud.parsers.LineSwitch(
                    Path.cwd() / README, {0: readme_rst, 1: underline}
                ):
                    command = [
                        "-M",
                        "html",
                        Path.cwd() / DOCS,
                        build_dir,
                        "-W",
                    ]
                    self.subprocess[self.sphinx_build].call(*command, **kwargs)
                    colors.green.bold.print("Build successful")
            else:
                print("No docs found")


@pyaud.plugins.register(name="files")
class Files(
    pyaud.plugins.Parametrize
):  # pylint: disable=too-few-public-methods
    """Audit project data files.

    Make ``docs/<APPNAME>.rst``, ``whitelist.py``, and
    ``requirements.txt`` if none already exist, update them if they do
    and changes are needed or pass if nothing needs to be done.
    """

    def plugins(self) -> t.List[str]:
        return ["requirements", "toc", "whitelist"]


@pyaud.plugins.register(name="format")
class Format(pyaud.plugins.Fix):
    """Audit code with `Black`."""

    black = "black"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.black]

    def audit(self, *args: t.Any, **kwargs: bool) -> t.Any:
        return self.subprocess[self.black].call(
            "--check", *pyaud.files.args(), *args, **kwargs
        )

    def fix(self, *args: t.Any, **kwargs: bool) -> t.Any:
        return self.subprocess[self.black].call(
            *args, *pyaud.files.args(), **kwargs
        )


@pyaud.plugins.register(name="lint")
class Lint(pyaud.plugins.Audit):
    """Lint code with ``pylint``."""

    pylint = "pylint"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.pylint]

    @property
    def env(self) -> t.Dict[str, str]:
        return {"PYCHARM_HOSTED": "True"}

    def audit(self, *args: t.Any, **kwargs: bool) -> t.Any:
        return self.subprocess[self.pylint].call(
            "--output-format=colorized", *args, *pyaud.files.args(), **kwargs
        )


@pyaud.plugins.register(name="requirements")
class Requirements(pyaud.plugins.Write):
    """Audit requirements.txt with Pipfile.lock."""

    p2req = "pipfile2req"

    @property
    def exe(self) -> t.List[str]:
        return [self.p2req]

    @property
    def path(self) -> Path:
        return Path.cwd() / pyaud.environ.REQUIREMENTS

    def required(self) -> Path:
        return Path.cwd() / "Pipfile.lock"

    def write(self, *args: t.Any, **kwargs: bool) -> t.Any:
        # get the stdout for both production and development packages

        # get the stdout for both production and development packages
        self.subprocess[self.p2req].call(
            self.required(), *args, capture=True, **kwargs
        )
        self.subprocess[self.p2req].call(
            self.required(), "--dev", *args, capture=True, **kwargs
        )

        # write to file and then use sed to remove the additional
        # information following the semicolon
        stdout = list(
            set("\n".join(self.subprocess[self.p2req].stdout()).splitlines())
        )
        stdout.sort()
        with open(self.path, "w", encoding="utf-8") as fout:
            for content in stdout:
                fout.write(f"{content.split(';')[0]}\n")


@pyaud.plugins.register(name="toc")
class Toc(pyaud.plugins.Write):
    """Audit docs/<NAME>.rst toc-file."""

    sphinx_apidoc = "sphinx-apidoc"

    @property
    def exe(self) -> t.List[str]:
        return [self.sphinx_apidoc]

    @property
    def path(self) -> Path:
        return Path.cwd() / DOCS / f"{pyaud.package()}.rst"

    def required(self) -> t.Optional[Path]:
        return Path.cwd() / DOCS / "conf.py"

    @staticmethod
    def _populate(path: Path, contents: t.List[str]) -> None:
        if path.is_file():
            with open(path, encoding="utf-8") as fin:
                contents.extend(fin.read().splitlines())

    def write(self, *args: t.Any, **kwargs: bool) -> t.Any:
        toc_attrs = "   :members:\n   :undoc-members:\n   :show-inheritance:"
        package = pyaud.package()
        docspath = Path.cwd() / DOCS
        self.subprocess[self.sphinx_apidoc].call(
            "-o",
            docspath,
            Path.cwd() / package,
            "-f",
            *args,
            devnull=True,
            **kwargs,
        )

        # dynamically populate a list of unwanted, overly nested files
        # nesting the file in the docs/<NAME>.rst file is preferred
        nested = [
            docspath / f
            for f in docspath.iterdir()
            if len(f.name.split(".")) > 2
        ]

        contents: t.List[str] = []
        self._populate(self.path, contents)
        for file in nested:

            # extract the data from the nested toc
            self._populate(file, contents)

        contents = sorted(
            [i for i in contents if i.startswith(".. automodule::")]
        )
        with open(self.path, "w", encoding="utf-8") as fout:
            fout.write(f"{package}\n{len(package) * '='}\n\n")
            for content in contents:
                fout.write(f"{content}\n{toc_attrs}\n")

        # files that we do not want included in docs
        # modules creates an extra layer that is not desired for this
        # module
        blacklist = [docspath / "modules.rst", *nested]

        # remove unwanted files
        for module in blacklist:
            if module.is_file():
                os.remove(module)


@pyaud.plugins.register(name="typecheck")
class TypeCheck(pyaud.plugins.Audit):
    """Typecheck code with ``mypy``.

    Check that there are no errors between the files and their stub-
    files.
    """

    mypy = "mypy"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.mypy]

    def audit(self, *args: t.Any, **kwargs: bool) -> t.Any:
        # save the value of ``suppress`` if it exists: default to False
        suppress = kwargs.get("suppress", False)

        # ignore the first error that might occur
        # capture output to analyse for missing stub libraries
        kwargs["suppress"] = True
        returncode = self.subprocess[self.mypy].call(
            "--ignore-missing-imports",
            *pyaud.files.args(),
            *args,
            capture=True,
            **kwargs,
        )

        # restore value of ``suppress``
        kwargs["suppress"] = suppress
        stdout = self.subprocess[self.mypy].stdout()

        # if no error occurred, continue on to print message and return
        # value
        if returncode:
            # if error occurred it might be because the stub library is
            # not installed: automatically download and install stub
            # library if the below message occurred
            if any(
                "error: Library stubs not installed for" in i for i in stdout
            ):
                self.subprocess[self.mypy].call(
                    "--non-interactive", "--install-types"
                )

                # continue on to run the first command again, which will
                # not, by default, ignore any consecutive errors
                # do not capture output again
                return self.subprocess[self.mypy].call(
                    "--ignore-missing-imports",
                    *pyaud.files.args(),
                    *args,
                    **kwargs,
                )

            # if any error occurred that wasn't because of a missing
            # stub library
            print("\n".join(stdout))
            if not suppress:
                raise pyaud.exceptions.AuditError(" ".join(sys.argv))

        else:
            print("\n".join(stdout))

        return returncode


@pyaud.plugins.register(name="unused")
class Unused(pyaud.plugins.Fix):
    """Audit unused code with ``vulture``.

    Create whitelist first with --fix.
    """

    vulture = "vulture"

    @property
    def exe(self) -> t.List[str]:
        return [self.vulture]

    def audit(self, *args: t.Any, **kwargs: bool) -> t.Any:
        whitelist = Path.cwd() / pyaud.environ.WHITELIST
        args = tuple([*pyaud.files.args(reduce=True), *args])
        if whitelist.is_file():
            args = str(whitelist), *args

        return self.subprocess[self.vulture].call(*args, **kwargs)

    def fix(self, *args: t.Any, **kwargs: bool) -> t.Any:
        pyaud.plugins.get("whitelist")(*args, **kwargs)
        return self.audit(*args, **kwargs)


@pyaud.plugins.register(name="whitelist")
class Whitelist(pyaud.plugins.Write):
    """Check whitelist.py file with ``vulture``.

    This will consider all unused code an exception so resolve code that
    is not to be excluded from the ``vulture`` search first.
    """

    vulture = "vulture"

    @property
    def exe(self) -> t.List[str]:
        return [self.vulture]

    @property
    def path(self) -> Path:
        return Path.cwd() / pyaud.environ.WHITELIST

    def write(self, *args: t.Any, **kwargs: bool) -> t.Any:
        # append whitelist exceptions for each individual module
        kwargs["suppress"] = True
        self.subprocess[self.vulture].call(
            *pyaud.files.args(reduce=True),
            "--make-whitelist",
            *args,
            capture=True,
            **kwargs,
        )
        stdout = self.subprocess[self.vulture].stdout()
        stdout = [i.replace(str(Path.cwd()) + os.sep, "") for i in stdout]
        stdout.sort()
        with open(self.path, "w", encoding="utf-8") as fout:
            fout.write("\n".join(stdout) + "\n")


@pyaud.plugins.register(name="imports")
class Imports(pyaud.plugins.FixFile):
    """Audit imports with ``isort``.

    ``Black`` and ``isort`` clash in some areas when it comes to
    ``Black`` sorting imports. To avoid  running into false
    positives when running both in conjunction (as ``Black`` is
    uncompromising) run ``Black`` straight after.

    To effectively test this, for lack of stdin functionality, use
    ``tempfile.NamedTemporaryFunction`` to first evaluate contents
    from original file, then after ``isort``, then after ``Black``.

    If nothing has changed, even if ``isort`` has changed a file,
    then the imports are sorted enough for ``Black``'s standard.

    If there is a change raise ``PyAuditError`` if ``-f/--fix`` or
    ``-s/--suppress`` was not passed to the commandline.

    If ``-f/--fix`` was passed then replace the original file with
    the temp file's contents.
    """

    result = ""
    content = ""
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return ["isort", "black"]

    def audit(self, file: Path, **kwargs: bool) -> t.Any:
        # collect original file's contents
        with open(file, encoding="utf-8") as fin:
            self.content = fin.read()

        # write original file's contents to temporary file
        tmp = (
            tempfile.NamedTemporaryFile(  # pylint: disable=consider-using-with
                delete=False
            )
        )
        with open(tmp.name, "w", encoding="utf-8") as fout:
            fout.write(self.content)

        # run both ``isort`` and ``black`` on the temporary file,
        # leaving the original file untouched
        self.subprocess["isort"].call(tmp.name, devnull=True, **kwargs)
        self.subprocess["black"].call(
            tmp.name,
            "--line-length",
            "79",
            loglevel="debug",
            devnull=True,
            **kwargs,
        )

        # collect the results from the temporary file
        with open(tmp.name, encoding="utf-8") as fin:
            self.result = fin.read()

        os.remove(tmp.name)

    def fail_condition(self) -> t.Optional[bool]:
        return self.result != self.content

    def fix(self, file: t.Any, **kwargs: bool) -> None:
        print(f"Fixed {file.relative_to(Path.cwd())}")

        # replace original file's contents with the temp
        # file post ``isort`` and ``Black``
        with open(file, "w", encoding="utf-8") as fout:
            fout.write(self.result)


@pyaud.plugins.register(name="readme")
class Readme(pyaud.plugins.Action):  # pylint: disable=too-few-public-methods
    """Parse, test, and assert RST code-blocks."""

    readmetester = "readmetester"

    @property
    def env(self) -> t.Dict[str, str]:
        return {"PYCHARM_HOSTED": "True"}

    @property
    def exe(self) -> t.List[str]:
        return [self.readmetester]

    def action(self, *args, **kwargs):
        if Path(Path.cwd() / README).is_file():
            self.subprocess[self.readmetester].call(
                Path.cwd() / README, *args, **kwargs
            )
        else:
            print("No README.rst found in project root")


@pyaud.plugins.register(name="format-str")
class FormatFString(pyaud.plugins.Fix):
    """Format f-strings with ``flynt``."""

    flynt = "flynt"
    args = "--line-length", "79", "--transform-concats"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.flynt]

    def audit(self, *args: t.Any, **kwargs: bool) -> t.Any:
        return self.subprocess[self.flynt].call(
            "--dry-run",
            "--fail-on-change",
            *self.args,
            *pyaud.files.args(),
            *args,
            **kwargs,
        )

    def fix(self, *args: t.Any, **kwargs: bool) -> t.Any:
        return self.subprocess[self.flynt].call(
            *self.args, *pyaud.files.args(), *args, **kwargs
        )


@pyaud.plugins.register(name="format-docs")
class FormatDocs(pyaud.plugins.Fix):
    """Format docstrings with ``docformatter``."""

    docformatter = "docformatter"
    args = "--recursive", "--wrap-summaries", "72"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.docformatter]

    def audit(self, *args: t.Any, **kwargs: bool) -> t.Any:
        return self.subprocess[self.docformatter].call(
            "--check", *self.args, *pyaud.files.args(), *args, **kwargs
        )

    def fix(self, *args: t.Any, **kwargs: bool) -> t.Any:
        return self.subprocess[self.docformatter].call(
            "--in-place", *self.args, *pyaud.files.args(), *args, **kwargs
        )


@pyaud.plugins.register(name="generate-rcfile")
class GenerateRCFile(
    pyaud.plugins.Action
):  # pylint: disable=too-few-public-methods
    """Print rcfile to stdout.

    Print rcfile to stdout, so it may be piped to chosen filepath.
    """

    def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
        print(pyaud.config.toml.dumps(pyaud.config.DEFAULT_CONFIG), end="")


@pyaud.plugins.register("audit")
class Audit(pyaud.plugins.Action):  # pylint: disable=too-few-public-methods

    """Read from [audit] key in config."""

    def action(self, *args, **kwargs):
        funcs = pyaud.config.toml["audit"]["modules"]
        if kwargs.get("clean", False):
            funcs.insert(0, "clean")

        if kwargs.get("deploy", False):
            funcs.append("deploy")

        for func in funcs:
            if func in pyaud.plugins.registered():
                colors.cyan.bold.print(f"\n{pyaud.__name__} {func}")
                pyaud.plugins.get(func)(**kwargs)
