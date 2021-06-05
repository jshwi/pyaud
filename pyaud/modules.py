"""
pyaud.modules
=============
"""
import os
import shutil
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Callable, List, Union

from .config import ConfigParser
from .environ import NAME, TempEnvVar, env
from .utils import (
    EnterDir,
    Git,
    HashCap,
    LineSwitch,
    PyAuditError,
    Subprocess,
    check_command,
    colors,
    deploy_docs,
    pyitems,
    write_command,
)


def make_audit(**kwargs: Union[bool, str]) -> int:
    """Run all modules for complete package audit.

    :param kwargs:  Pass keyword arguments to audit submodule.
    :key clean:     Insert clean module to the beginning of module list
                    to remove all unversioned files before executing
                    rest of audit.
    :key deploy:    Append deploy modules (docs and coverage) to end of
                    modules list to deploy package data after executing
                    audit.
    :return:        Exit status.
    """
    audit_modules: List[Callable[..., Any]] = [
        make_format,
        make_format_str,
        make_imports,
        make_typecheck,
        make_unused,
        make_lint,
        make_coverage,
        make_readme,
        make_docs,
    ]
    if env.get("CLEAN"):
        audit_modules.insert(0, make_clean)

    if env.get("DEPLOY"):
        audit_modules.append(make_deploy)

    for audit_module in audit_modules:
        colors.cyan.bold.print(
            "\n{}".format(
                audit_module.__name__.replace("make_", f"{NAME} ").replace(
                    "_", "-"
                )
            )
        )
        audit_module(**kwargs)

    return 0


def make_clean(**kwargs: Union[bool, str]) -> int:
    """Remove all unversioned package files recursively.

    :param kwargs:  Additional keyword arguments for ``git clean``.
    :return:        Exit status.
    """
    _config = ConfigParser()
    exclude = _config.getlist("CLEAN", "exclude")
    with Git(os.environ["PROJECT_DIR"]) as git:
        return git.clean(  # type: ignore
            "-fdx", *[f"--exclude={e}" for e in exclude], **kwargs
        )


def make_coverage(**kwargs: Union[bool, str]) -> int:
    """Run package unit-tests with ``pytest`` and ``coverage``.

    :param kwargs:  Pass keyword arguments to ``pytest`` and ``call``.
    :return:        Exit status.
    """
    with EnterDir(env["PROJECT_DIR"]):
        coverage = Subprocess("coverage")
        args = [f"--cov={e}" for e in pyitems.items if os.path.isdir(e)]
        returncode = make_tests(*args, **kwargs)
        if not returncode:
            with TempEnvVar(kwargs, suppress=True):
                return coverage.call("xml", **kwargs)

        print("No coverage to report")
        return 0


def make_deploy(**kwargs: Union[bool, str]) -> int:
    """Deploy package documentation and test coverage.

    :param kwargs:  Keyword arguments for ``deploy_module``.
    :return:        Exit status.
    """

    deploy_modules = [make_deploy_cov, make_deploy_docs]
    for deploy_module in deploy_modules:
        colors.cyan.bold.print(
            "\n{}".format(
                deploy_module.__name__.replace("make_", f"{NAME} ").replace(
                    "_", "-"
                )
            )
        )
        returncode = deploy_module(**kwargs)
        if returncode:
            return returncode

    return 0


def make_deploy_cov(**kwargs: Union[bool, str]) -> int:
    """Upload coverage data to ``Codecov``.

    If no file exists otherwise announce that no file has been created
    yet. If no ``CODECOV_TOKEN`` environment variable has been exported
    or defined in ``.env`` announce that no authorization token has been
    created yet.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    codecov = Subprocess("codecov")
    if os.path.isfile(env["COVERAGE_XML"]):
        if env["CODECOV_TOKEN"]:
            return codecov.call(
                "--file",
                env["COVERAGE_XML"],
                "--token",
                env["CODECOV_TOKEN"],
                "--slug",
                env["CODECOV_SLUG"],
                **kwargs,
            )

        print("CODECOV_TOKEN not set")
    else:
        print("No coverage report found")

    return 0


def make_deploy_docs(**kwargs: Union[bool, str]) -> int:
    """Deploy package documentation to ``gh-pages``.

    Check that the branch is being pushed as master (or other branch
    for tests). If the correct branch is the one in use deploy.
    ``gh-pages`` to the orphaned branch - otherwise do nothing and
    announce.

    :key url:   Remote origin URL.
    :return:    Exit status.
    """
    if env["BRANCH"] == "master":
        git_credentials = ["GH_NAME", "GH_EMAIL", "GH_TOKEN"]
        null_vals = [k for k in git_credentials if env[k] is None]
        if not null_vals:
            url = kwargs.get(
                "url",
                (
                    "https://"
                    + env["GH_NAME"]
                    + ":"
                    + env["GH_TOKEN"]
                    + "@github.com/"
                    + env["GH_NAME"]
                    + "/"
                    + env["PKG"]
                    + ".git"
                ),
            )
            if not os.path.isdir(env["DOCS_BUILD_HTML"]):
                make_docs(**kwargs)

            deploy_docs(url)
        else:
            print("The following is not set:")
            for null_val in null_vals:
                print(f"- {null_val}")

            print()
            print("Pushing skipped")
    else:
        colors.green.print("Documentation not for master")
        print("Pushing skipped")

    return 0


def make_docs(**kwargs: Union[bool, str]) -> None:
    """Compile package documentation with ``Sphinx``.

    This is so the hyperlink isn't exactly the same as the package
    documentation. Build the ``Sphinx`` html documentation. Return the
    README's title to what it originally was.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    make_toc(**kwargs)

    readme_rst = "README"
    underline = len(readme_rst) * "="
    if os.path.isdir(env["DOCS_BUILD"]):
        shutil.rmtree(env["DOCS_BUILD"])

    sphinx_build = Subprocess("sphinx-build")
    if os.path.isdir(env["DOCS"]):
        with LineSwitch(env["README_RST"], {0: readme_rst, 1: underline}):
            command = ["-M", "html", env["DOCS"], env["DOCS_BUILD"], "-W"]
            sphinx_build.call(*command, **kwargs)
            colors.green.bold.print("Build successful")
    else:
        print("No docs found")


def make_files(**kwargs: Union[bool, str]) -> int:
    """Audit project data files.

    Make ``docs/<APPNAME>.rst``, ``whitelist.py``, and
    ``requirements.txt`` if none already exist, update them if they do
    and changes are needed or pass if nothing needs to be done.

    :param kwargs:  Pass keyword arguments to ``func``.
    :return:        Exit status.
    """
    for func in (make_requirements, make_toc, make_whitelist):
        returncode = func(**kwargs)
        if returncode:
            return returncode

    return 0


@check_command
def make_format(**kwargs: Union[bool, str]) -> int:
    """Audit code against ``Black``.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    black = Subprocess("black", loglevel="debug")
    args = pyitems.items
    try:
        return black.call("--check", *args, **kwargs)

    except CalledProcessError as err:
        black.call(*args, **kwargs)
        raise PyAuditError(f"{black.exe} {args}") from err


@check_command
def make_lint(**kwargs: Union[bool, str]) -> int:
    """Lint code with ``pylint``.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    with TempEnvVar(os.environ, PYCHARM_HOSTED="True"):
        args = list(pyitems.items)
        pylint = Subprocess("pylint")
        if os.path.isfile(env["PYLINTRC"]):
            args.append(f"--rcfile={env['PYLINTRC']}")

        return pylint.call("--output-format=colorized", *args, **kwargs)


@write_command("REQUIREMENTS", required="PIPFILE_LOCK")
def make_requirements(**kwargs: Union[bool, str]) -> int:
    """Audit requirements.txt with Pipfile.lock.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    newlines = []
    contents = []

    # get the stdout for both production and development packages
    p2req = Subprocess("pipfile2req")
    p2req.call(env["PIPFILE_LOCK"], capture=True, **kwargs)

    prod_stdout = p2req.stdout
    p2req.call(env["PIPFILE_LOCK"], "--dev", capture=True, **kwargs)

    dev_stdout = p2req.stdout
    for stdout in prod_stdout, dev_stdout:
        if stdout:
            contents.extend(stdout.splitlines())

    # write to file and then use sed to remove the additional
    # information following the semi-colon
    contents.sort()
    with open(env["REQUIREMENTS"], "w") as fout:
        for content in contents:
            if content not in newlines:
                newlines.append(content)
                fout.write(f"{content.split(';')[0]}\n")

    return 0


def make_tests(*args: str, **kwargs: Union[bool, str]) -> int:
    """Run the package unit-tests with ``pytest``.

    :param args:    Additional positional arguments for ``pytest``.
    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    with EnterDir(env["PROJECT_DIR"]):
        tests = env["TESTS"]
        project_dir = env["PROJECT_DIR"]
        patterns = ("test_*.py", "*_test.py")
        rglob = [p for a in patterns for p in Path(project_dir).rglob(a)]
        pytest = Subprocess("pytest")
        if os.path.isdir(tests) and rglob:
            return pytest.call(*args, **kwargs)

        print("No tests found")
        return 1


@write_command("TOC", required="DOCS")
def make_toc(**kwargs: Union[bool, str]) -> int:
    """Audit docs/<NAME>.rst toc-file.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    kwargs["devnull"] = True
    toc_attrs = [
        ".. automodule::",
        "   :members:",
        "   :undoc-members:",
        "   :show-inheritance:",
    ]
    if os.path.isfile(env["DOCS_CONF"]):
        apidoc = Subprocess("sphinx-apidoc")
        apidoc.call("-o", env["DOCS"], env["PKG_PATH"], "-f", **kwargs)
        with open(env["TOC"]) as fin:
            contents = fin.read().splitlines()

        with open(env["TOC"], "w") as fout:
            fout.write(f"{env['PKG']}\n{len(env['PKG']) * '='}\n\n")
            for content in contents:
                if any(a in content for a in toc_attrs):
                    fout.write(f"{content}\n")

        modules = (
            os.path.join(env["DOCS"], f"{env['PKG']}.src.rst"),
            os.path.join(env["DOCS"], "modules.rst"),
        )
        for module in modules:
            if os.path.isfile(module):
                os.remove(module)

    return 0


@check_command
def make_typecheck(**kwargs: Union[bool, str]) -> int:
    """Typecheck code with ``mypy``.

    Check that there are no errors between the files and their
    stub-files.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    cache_dir = os.path.join(env["PROJECT_DIR"], ".mypy_cache")
    os.environ["MYPY_CACHE_DIR"] = cache_dir
    mypy = Subprocess("mypy")
    return mypy.call("--ignore-missing-imports", *pyitems.items, **kwargs)


@check_command
def make_unused(**kwargs: Union[bool, str]) -> int:
    """Audit unused code with ``vulture``.

    Create whitelist first with --fix.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    args = list(pyitems.items)
    if os.path.isfile(env["WHITELIST"]):
        args.append(env["WHITELIST"])

    vulture = Subprocess("vulture")
    return vulture.call(*args, **kwargs)


@write_command("WHITELIST")
def make_whitelist(**kwargs: Union[bool, str]) -> int:
    """Check whitelist.py file with ``vulture``.

    This will consider all unused code an exception so resolve code that
    is not to be excluded from the ``vulture`` search first.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    lines = []
    vulture = Subprocess("vulture")

    # append whitelist exceptions for each individual module
    for item in pyitems.items:
        if os.path.exists(item):  # type: ignore
            with TempEnvVar(kwargs, suppress=True):
                vulture.call(item, "--make-whitelist", capture=True, **kwargs)

            if vulture.stdout:
                lines.extend(vulture.stdout.splitlines())

    # clear contents of instantiated ``TextIO' object to write a new
    # file and not append
    stdout = [i for i in "\n".join(lines).splitlines() if i != ""]
    stdout.sort()
    with open(env["WHITELIST"], "w") as fout:
        for line in stdout:
            fout.write(f"{line.replace(env['PROJECT_DIR'] + os.sep, '')}\n")

    return 0


@check_command
def make_imports(**kwargs: Union[bool, str]) -> int:
    """Audit imports with ``isort``.

    ``Black`` and ``isort`` clash in some areas when it comes to
    ``Black`` and sorting imports. To avoid running into false positives
    when running both in conjunction run ``Black`` straight after. Use
    ``HashCap`` to determine if any files have changed for presenting
    data to user.
    """
    changed = []
    isort = Subprocess("isort")
    black = Subprocess("black")
    for item in pyitems.files:
        if os.path.isfile(item):
            with HashCap(item) as cap:
                isort.call(item, capture=True, **kwargs)
                black.call(item, devnull=True, **kwargs)

            if not cap.compare:
                changed.append(os.path.relpath(item, env["PROJECT_DIR"]))
                if isort.stdout is not None:
                    print(isort.stdout.strip())

    if changed:
        raise PyAuditError(f"{isort.exe} {tuple(changed)}")

    return 0


def make_readme() -> None:
    """Parse, test, and assert RST code-blocks."""
    with TempEnvVar(os.environ, PYCHARM_HOSTED="True"):
        readmtester = Subprocess("readmetester")
        if os.path.isfile(env["README_RST"]):
            readmtester.call(env["README_RST"])
        else:
            print("No README.rst found in project root")


@check_command
def make_format_str(**kwargs: bool) -> int:
    """Format f-strings with ``flynt``.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    :return:        Exit status.
    """
    flynt = Subprocess("flynt")
    args = ("--line-length", "72", "--transform-concats", *pyitems.items)
    try:
        return flynt.call(
            "--dry-run", "--fail-on-change", *args, devnull=True, **kwargs
        )

    except CalledProcessError as err:
        flynt.call(*args, **kwargs)
        raise PyAuditError(
            f"{flynt.exe} {tuple([str(i) for i in args])}"
        ) from err
