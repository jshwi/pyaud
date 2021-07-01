"""
plugins.modules
===============
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pyaud

from .utils import DOCS, README, LineSwitch, deploy_docs


@pyaud.plugins.register(name="clean")
class Clean(pyaud.plugins.Action):  # pylint: disable=too-few-public-methods
    """Remove all unversioned package files recursively."""

    def action(self, *args: Any, **kwargs: bool) -> int:
        exclude = pyaud.config.toml["clean"]["exclude"]
        return pyaud.utils.git.clean(  # type: ignore
            "-fdx", *[f"--exclude={e}" for e in exclude], **kwargs
        )


@pyaud.plugins.register(name="coverage")
class Coverage(pyaud.plugins.Action):  # pylint: disable=too-few-public-methods
    """Run package unit-tests with ``pytest`` and ``coverage``."""

    coverage = "coverage"

    @property
    def exe(self) -> List[str]:
        return [self.coverage]

    def action(self, *args: Any, **kwargs: bool) -> Any:
        returncode = pyaud.plugins.plugins["tests"](
            *[f"--cov={e}" for e in pyaud.utils.files.reduce()],
            *args,
            **kwargs,
        )
        if not returncode:
            with pyaud.utils.TempEnvVar(kwargs, suppress=True):
                self.subprocess[self.coverage].call("xml", *args, **kwargs)
        else:
            print("No coverage to report")


@pyaud.plugins.register(name="deploy")
class Deploy(  # pylint: disable=too-few-public-methods
    pyaud.plugins.Parametrize
):
    """Deploy package documentation and test coverage."""

    def plugins(self) -> List[str]:
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
    def exe(self) -> List[str]:
        return [self.codecov]

    def action(self, *args: Any, **kwargs: bool) -> Any:
        coverage_xml = Path.cwd() / os.environ["PYAUD_COVERAGE_XML"]
        if coverage_xml.is_file():
            if os.environ["CODECOV_TOKEN"] != "":
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

    def action(self, *args: Any, **kwargs: bool) -> Any:
        if pyaud.utils.get_branch() == "master":
            git_credentials = [
                "PYAUD_GH_NAME",
                "PYAUD_GH_EMAIL",
                "PYAUD_GH_TOKEN",
            ]
            null_vals = [k for k in git_credentials if os.environ[k] == ""]
            if not null_vals:
                if not Path(
                    Path.cwd() / os.environ["BUILDDIR"] / "html"
                ).is_dir():
                    pyaud.plugins.plugins["docs"](**kwargs)

                deploy_docs()
            else:
                print("The following is not set:")
                for null_val in null_vals:
                    print(f"- {null_val}")

                print()
                print("Pushing skipped")
        else:
            pyaud.utils.colors.green.print("Documentation not for master")
            print("Pushing skipped")


@pyaud.plugins.register(name="docs")
class Docs(pyaud.plugins.Action):  # pylint: disable=too-few-public-methods
    """Compile package documentation with ``Sphinx``.

    This is so the hyperlink isn't exactly the same as the package
    documentation. Build the ``Sphinx`` html documentation. Return the
    README's title to what it originally was.
    """

    sphinx_build = "sphinx-build"

    @property
    def exe(self) -> List[str]:
        return [self.sphinx_build]

    def action(self, *args: Any, **kwargs: bool) -> Any:
        make_toc(**kwargs)
        readme_rst = "README"
        underline = len(readme_rst) * "="
        build_dir = Path.cwd() / os.environ["BUILDDIR"]
        if build_dir.is_dir():
            shutil.rmtree(build_dir)

        if (
            Path(Path.cwd() / DOCS).is_dir()
            and Path(Path.cwd(), README).is_file()
        ):
            with LineSwitch(
                Path.cwd() / README, {0: readme_rst, 1: underline}
            ):
                command = ["-M", "html", Path.cwd() / DOCS, build_dir, "-W"]
                self.subprocess[self.sphinx_build].call(*command, **kwargs)
                pyaud.utils.colors.green.bold.print("Build successful")
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

    def plugins(self) -> List[str]:
        return ["requirements", "toc", "whitelist"]


@pyaud.plugins.register(name="format")
class Format(pyaud.plugins.Fix):
    """Audit code with `Black`."""

    black = "black"

    @property
    def exe(self) -> List[str]:
        return [self.black]

    def audit(self, *args: Any, **kwargs: bool) -> Any:
        return self.subprocess[self.black].call(
            "--check", *pyaud.utils.files.args(reduce=True), *args, **kwargs
        )

    def fix(self, *args: Any, **kwargs: bool) -> Any:
        return self.subprocess[self.black].call(
            *args, *pyaud.utils.files.args(reduce=True), **kwargs
        )


@pyaud.plugins.register(name="lint")
class Lint(pyaud.plugins.Audit):
    """Lint code with ``pylint``."""

    pylint = "pylint"

    @property
    def exe(self) -> List[str]:
        return [self.pylint]

    @property
    def env(self) -> Dict[str, str]:
        return {"PYCHARM_HOSTED": "True"}

    def audit(self, *args: Any, **kwargs: bool) -> Any:
        return self.subprocess[self.pylint].call(
            "--output-format=colorized",
            *args,
            *pyaud.utils.files.args(reduce=True),
            **kwargs,
        )


@pyaud.plugins.register(name="requirements")
@pyaud.plugins.write_command(
    "PYAUD_REQUIREMENTS", required="PYAUD_PIPFILE_LOCK"
)
def make_requirements(**kwargs: bool) -> None:
    """Audit requirements.txt with Pipfile.lock.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    """
    # get the stdout for both production and development packages
    pipfile_lock_path = Path.cwd() / "Pipfile.lock"
    requirements_path = Path.cwd() / os.environ["PYAUD_REQUIREMENTS"]

    # get the stdout for both production and development packages
    p2req = pyaud.utils.Subprocess("pipfile2req", capture=True)
    p2req.call(pipfile_lock_path, **kwargs)
    p2req.call(pipfile_lock_path, "--dev", **kwargs)

    # write to file and then use sed to remove the additional
    # information following the semi-colon
    stdout = list(set("\n".join(p2req.stdout()).splitlines()))
    stdout.sort()
    with open(requirements_path, "w") as fout:
        for content in stdout:
            fout.write(f"{content.split(';')[0]}\n")


@pyaud.plugins.register(name="tests")
class Tests(pyaud.plugins.Action):  # pylint: disable=too-few-public-methods
    """Run the package unit-tests with ``pytest``."""

    pytest = "pytest"

    @property
    def exe(self) -> List[str]:
        return [self.pytest]

    def action(self, *args: Any, **kwargs: bool) -> Any:
        tests = Path.cwd() / "tests"
        patterns = ("test_*.py", "*_test.py")
        rglob = [
            f
            for f in pyaud.utils.files
            for p in patterns
            if f.match(p) and str(tests) in str(f)
        ]
        if rglob:
            return self.subprocess[self.pytest].call(*args, **kwargs)

        print("No tests found")
        return 1


@pyaud.plugins.register(name="toc")
@pyaud.plugins.write_command("PYAUD_TOC", required="PYAUD_DOCS")
def make_toc(**kwargs: bool) -> None:
    """Audit docs/<NAME>.rst toc-file.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    :return:        Exit status.
    """
    toc_attrs = [
        ".. automodule::",
        "   :members:",
        "   :undoc-members:",
        "   :show-inheritance:",
    ]
    package = pyaud.environ.find_package()
    docspath = Path.cwd() / DOCS
    tocpath = docspath / f"{package}.rst"
    if Path(Path.cwd() / DOCS / "conf.py").is_file():
        apidoc = pyaud.utils.Subprocess("sphinx-apidoc")
        apidoc.call(
            "-o", docspath, Path.cwd() / package, "-f", devnull=True, **kwargs
        )

        contents = []
        if tocpath.is_file():
            with open(tocpath) as fin:
                contents.extend(fin.read().splitlines())

        with open(tocpath, "w") as fout:
            fout.write(f"{package}\n{len(package) * '='}\n\n")
            for content in contents:
                if any(a in content for a in toc_attrs):
                    fout.write(f"{content}\n")

        modules = (docspath / f"{package}.src.rst", docspath / "modules.rst")
        for module in modules:
            if module.is_file():
                os.remove(module)


@pyaud.plugins.register(name="typecheck")
class TypeCheck(pyaud.plugins.Audit):
    """Typecheck code with ``mypy``.

    Check that there are no errors between the files and their stub-
    files.
    """

    mypy = "mypy"

    @property
    def exe(self) -> List[str]:
        return [self.mypy]

    def audit(self, *args: Any, **kwargs: bool) -> Any:
        return self.subprocess[self.mypy].call(
            "--ignore-missing-imports",
            *pyaud.utils.files.args(reduce=True),
            *args,
            **kwargs,
        )


@pyaud.plugins.register(name="unused")
class Unused(pyaud.plugins.Fix):
    """Audit unused code with ``vulture``.

    Create whitelist first with --fix.
    """

    vulture = "vulture"

    @property
    def exe(self) -> List[str]:
        return [self.vulture]

    def audit(self, *args: Any, **kwargs: bool) -> Any:
        whitelist = Path.cwd() / os.environ["PYAUD_WHITELIST"]
        args = *pyaud.utils.files.args(reduce=True), *args
        if whitelist.is_file():
            args = str(whitelist), *args

        return self.subprocess[self.vulture].call(*args, **kwargs)

    def fix(self, *args: Any, **kwargs: bool) -> Any:
        make_whitelist(**kwargs)
        return self.audit(*args, **kwargs)


@pyaud.plugins.register(name="whitelist")
@pyaud.plugins.write_command("PYAUD_WHITELIST")
def make_whitelist(**kwargs: bool) -> None:
    """Check whitelist.py file with ``vulture``.

    This will consider all unused code an exception so resolve code that
    is not to be excluded from the ``vulture`` search first.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    :return:        Exit status.
    """
    vulture = pyaud.utils.Subprocess("vulture", capture=True)

    # append whitelist exceptions for each individual module
    for item in pyaud.utils.files.reduce():
        if item.exists():
            with pyaud.utils.TempEnvVar(kwargs, suppress=True):
                vulture.call(item, "--make-whitelist", **kwargs)

    # clear contents of instantiated ``TextIO' object to write a new
    # file and not append
    stdout = [i for i in "\n".join(vulture.stdout()).splitlines() if i != ""]
    stdout.sort()
    with open(Path.cwd() / os.environ["PYAUD_WHITELIST"], "w") as fout:
        for line in stdout:
            fout.write(f"{line.replace(str(Path.cwd()) + os.sep, '')}\n")


@pyaud.plugins.register(name="imports")
@pyaud.plugins.check_command
def make_imports(**kwargs: bool) -> int:
    """Audit imports with ``isort``.

    ``Black`` and ``isort`` clash in some areas when it comes to
    ``Black`` sorting imports. To avoid  running into false positives
    when running both in conjunction (as ``Black`` is uncompromising)
    run ``Black`` straight after. To effectively test this, for lack of
    stdin functionality, use ``tempfile.NamedTemporaryFunction`` to
    first evaluate contents from original file, then after ``isort``,
    then after ``Black``. If nothing has changed, even if ``isort``
    has changed a file, then the imports are sorted enough for
    ``Black``'s standard. If there is a change raise ``PyAuditError`` if
    ``-f/--fix`` or ``-s/--suppress`` was not passed to the commandline.
    If ``-f/--fix`` was passed then replace the original file with the
    temp file's contents.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    :return:        Exit status.
    """
    isort = pyaud.utils.Subprocess("isort", devnull=True)
    black = pyaud.utils.Subprocess("black", loglevel="debug", devnull=True)
    for item in pyaud.utils.files:
        if item.is_file():

            # collect original file's contents
            with open(item) as fin:
                content = fin.read()

            # write original file's contents to temporary file
            tmp = tempfile.NamedTemporaryFile(delete=False)
            with open(tmp.name, "w") as fout:
                fout.write(content)

            # run both ``isort`` and ``black`` on the temporary file,
            # leaving the original file untouched
            isort.call(tmp.name, **kwargs)
            black.call(tmp.name, "--line-length", "79", **kwargs)

            # collect the results from the temporary file
            with open(tmp.name) as fin:
                result = fin.read()

            os.remove(tmp.name)
            if result != content:
                if kwargs.get("fix"):
                    print(f"Fixed {item.relative_to(Path.cwd())}")

                    # replace original file's contents with the temp
                    # file post ``isort`` and ``Black``
                    with open(item, "w") as fout:
                        fout.write(result)

                else:
                    raise pyaud.exceptions.PyAuditError(
                        "{} {}".format(
                            make_imports, pyaud.utils.files.args(reduce=True)
                        )
                    )

    return 0


@pyaud.plugins.register(name="readme")
class Readme(pyaud.plugins.Action):  # pylint: disable=too-few-public-methods
    """Parse, test, and assert RST code-blocks."""

    readmetester = "readmetester"

    @property
    def env(self) -> Dict[str, str]:
        return {"PYCHARM_HOSTED": "True"}

    @property
    def exe(self) -> List[str]:
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
    args = "--line-length", "72", "--transform-concats"

    @property
    def exe(self) -> List[str]:
        return [self.flynt]

    def audit(self, *args: Any, **kwargs: bool) -> Any:
        return self.subprocess[self.flynt].call(
            "--check",
            *self.args,
            *pyaud.utils.files.args(reduce=True),
            *args,
            **kwargs,
        )

    def fix(self, *args: Any, **kwargs: bool) -> Any:
        return self.subprocess[self.flynt].call(
            *self.args, *pyaud.utils.files.args(reduce=True), *args, **kwargs
        )


@pyaud.plugins.register(name="format-docs")
class FormatDocs(pyaud.plugins.Fix):
    """Format docstrings with ``docformatter``."""

    docformatter = "docformatter"
    args = "--recursive", "--wrap-summaries", "72"

    @property
    def exe(self) -> List[str]:
        return [self.docformatter]

    def audit(self, *args: Any, **kwargs: bool) -> Any:
        return self.subprocess[self.docformatter].call(
            "--check",
            *self.args,
            *pyaud.utils.files.args(reduce=True),
            *args,
            **kwargs,
        )

    def fix(self, *args: Any, **kwargs: bool) -> Any:
        return self.subprocess[self.docformatter].call(
            "--in-place",
            *self.args,
            *pyaud.utils.files.args(reduce=True),
            *args,
            **kwargs,
        )


@pyaud.plugins.register(name="generate-rcfile")
class GenerateRCFile(
    pyaud.plugins.Action
):  # pylint: disable=too-few-public-methods
    """Print rcfile to stdout.

    Print rcfile to stdout so it may be piped to chosen filepath.
    """

    def action(self, *args: Any, **kwargs: bool) -> Any:
        pyaud.config.generate_rcfile()


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
            if func in pyaud.plugins.plugins:
                pyaud.utils.colors.cyan.bold.print(
                    f"\n{pyaud.__name__} {func}"
                )
                pyaud.plugins.plugins[func](**kwargs)
