"""
pyaud.modules
==============
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
    PyaudSubprocessError,
    Subprocess,
    check_command,
    colors,
    deploy_docs,
    pyitems,
    write_command,
)


def make_audit(**kwargs: Union[bool, str]) -> int:
    """Combine (almost) all make functions into a single build
    function.

    :param kwargs: Pass keyword arguments to audit submodule.
    """
    audit_modules: List[Callable[..., Any]] = [
        make_format,
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
    """Remove all unversioned directories and files within a git
    repository.

    :param kwargs: Additional keyword arguments for ``git clean``.
    """
    _config = ConfigParser()
    exclude = _config.getlist("CLEAN", "exclude")
    with Git(os.environ["PROJECT_DIR"]) as git:
        return git.clean(  # type: ignore
            "-fdx", *["--exclude=" + e for e in exclude], **kwargs
        )


def make_coverage(**kwargs: Union[bool, str]) -> int:
    """Ensure ``pytest`` and ``coverage`` are installed. If it is
    not then install development dependencies with ``pipenv``. Run
    the package unittests with ``pytest`` and ``coverage``.
    """
    with EnterDir(env["PROJECT_DIR"]):
        coverage = Subprocess("coverage")
        args = ["--cov=" + e for e in pyitems.items if os.path.isdir(e)]
        returncode = make_tests(*args, **kwargs)
        if not returncode:
            return coverage.call("xml", suppress=True, **kwargs)

        print("No coverage to report")
        return 0


def make_deploy(**kwargs: Union[bool, str]) -> int:
    """Combine both the ``deploy-cov`` and ``deploy-docs`` modules into
    a single process.

    :param kwargs: Keyword arguments for ``deploy_module``.
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
    """Upload coverage data from a ``coverage.xml`` to ``codecov.io``.
    If no file exists otherwise announce that no file has been created
    yet. If no ``CODECOV_TOKEN`` environment variable has been exported
    or defined in ``.env`` announce that no authorization token has been
    created yet.

    :param kwargs: Additional keyword arguments for ``codecov``.
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
    """Check that the branch is being pushed as master (or other branch
    for tests). If the correct branch is the one in use deploy
    ``gh-pages`` to the orphaned branch - otherwise do nothing and
    announce.

    :key url: Remote origin URL.
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
                print("- " + null_val)

            print()
            print("Pushing skipped")
    else:
        colors.green.print("Documentation not for master")
        print("Pushing skipped")

    return 0


@check_command
def make_docs(**kwargs: Union[bool, str]) -> int:
    """Replace the title of ``README.rst`` with ``README`` so the
    hyperlink isn't exactly the same as the package documentation. Build
    the ``Sphinx`` html documentation. Return the README's title to what
    it originally was.

    :param kwargs:  Additional keyword arguments for ``make_toc`` and
                    ``sphinx-build``.
    """
    make_toc(**kwargs)

    readme_rst = "README"
    underline = len(readme_rst) * "="
    if os.path.isdir(env["DOCS_BUILD"]):
        shutil.rmtree(env["DOCS_BUILD"])

    sphinx_build = Subprocess("sphinx-build")
    with LineSwitch(env["README_RST"], {0: readme_rst, 1: underline}):
        command = ["-M", "html", env["DOCS"], env["DOCS_BUILD"], "-W"]
        return sphinx_build.call(*command, **kwargs)


def make_files(**kwargs: Union[bool, str]) -> int:
    """Make ``docs/<APPNAME>.rst``, ``whitelist.py``, and
    ``requirements.txt`` if none already exist, update them if they do
    and changes are needed or pass if nothing needs to be done.

    :param kwargs:  Keyword arguments for ``make_requirements``,
                    ``make_toc``, and ``make_whitelist``
    """
    for func in (make_requirements, make_toc, make_whitelist):
        returncode = func(**kwargs)
        if returncode:
            return returncode

    return 0


@check_command
def make_format(**kwargs: Union[bool, str]) -> int:
    """Subprocess ``Black`` to format python files and directories within a
    Python project.

    :param kwargs: Additional keyword arguments for ``Black``.
    """
    black = Subprocess("black", loglevel="debug")
    args = pyitems.items
    try:
        return black.call("--check", *args, **kwargs)

    except CalledProcessError as err:
        black.call(*args, **kwargs)
        raise PyaudSubprocessError(
            1, f"{black} {' '.join([str(s) for s in args])}"
        ) from err


@check_command
def make_lint(**kwargs: Union[bool, str]) -> int:
    """Lint all Python files with ``pylint``. If a ``.pylintrc`` file
    exists include this.

    :param kwargs: Additional keyword arguments for ``pylint``.
    """
    with TempEnvVar("PYCHARM_HOSTED", "True"):
        args = list(pyitems.items)
        pylint = Subprocess("pylint")
        if os.path.isfile(env["PYLINTRC"]):
            args.append(f"--rcfile={env['PYLINTRC']}")

        return pylint.call("--output-format=colorized", *args, **kwargs)


@write_command("REQUIREMENTS", required="PIPFILE_LOCK")
def make_requirements(**kwargs: Union[bool, str]) -> int:
    """Create or update and then format ``requirements.txt`` from
    ``Pipfile.lock``.

    :param kwargs: Additional keyword arguments for ``pipfile2req``.
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
                fout.write(content.split(";")[0] + "\n")

    return 0


def make_tests(*args: str, **kwargs: Union[bool, str]) -> int:
    """Ensure ``pytest`` is installed. If it is not then install
    development dependencies with ``pipenv``. Run the package
    unit-tests with ``pytest``.

    :param args:    Additional positional arguments for ``pytest``.
    :param kwargs:  Additional keyword arguments for ``pytest``.
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
    """Make the docs/<APPNAME>.rst file from the package source for
    ``Sphinx`` to parse into documentation.

    :param kwargs: Additional keyword arguments for ``sphinx-apidoc``.
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
                    fout.write(content + "\n")

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
    """Run ``mypy`` on all python files to check that there are no
    errors between the files and their stub-files.

    :param kwargs: Additional keyword arguments for ``mypy``.
    """
    cache_dir = os.path.join(env["PROJECT_DIR"], ".mypy_cache")
    os.environ["MYPY_CACHE_DIR"] = cache_dir
    mypy = Subprocess("mypy")
    return mypy.call("--ignore-missing-imports", *pyitems.items, **kwargs)


@check_command
def make_unused(**kwargs: Union[bool, str]) -> int:
    """Run ``vulture`` on all python files to inspect them for unused
    code.

    :param kwargs: Additional keyword arguments for ``vulture``.
    """
    args = list(pyitems.items)
    if os.path.isfile(env["WHITELIST"]):
        args.append(env["WHITELIST"])

    vulture = Subprocess("vulture")
    return vulture.call(*args, **kwargs)


@write_command("WHITELIST")
def make_whitelist(**kwargs: Union[bool, str]) -> int:
    """Generate a ``whitelist.py`` file for ``vulture``. This will
    consider all unused code an exception so resolve code that is not
    to be excluded from the ``vulture`` search first.

    :param kwargs: Additional keyword arguments for ``vulture``.
    """
    lines = []
    vulture = Subprocess("vulture")

    # append whitelist exceptions for each individual module
    for item in pyitems.items:
        if os.path.exists(item):  # type: ignore
            vulture.call(
                item, "--make-whitelist", capture=True, suppress=True, **kwargs
            )
            if vulture.stdout:
                lines.extend(vulture.stdout.splitlines())

    # clear contents of instantiated ``TextIO' object to write a new
    # file and not append
    stdout = [i for i in "\n".join(lines).splitlines() if i != ""]
    stdout.sort()
    with open(env["WHITELIST"], "w") as fout:
        for line in stdout:
            fout.write(line.replace(env["PROJECT_DIR"] + os.sep, "") + "\n")

    return 0


@check_command
def make_imports(**kwargs: Union[bool, str]) -> int:
    """Sort imports with ``isort``. ``Black`` and ``isort`` clash in
    some areas when it comes to ``Black`` and sorting imports. To
    avoid running into false positives when running both in conjunction
    run ``Black`` straight after. Use ``HashCap`` to determine if any
    files have changed for presenting data to user.
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
        command = "isort {}".format(" ".join(changed))
        raise PyaudSubprocessError(returncode=1, cmd=command)

    return 0


def make_readme() -> None:
    """Parse, test, and assert RST code-blocks."""
    with TempEnvVar("PYCHARM_HOSTED", "True"):
        readmtester = Subprocess("readmetester")
        if os.path.isfile(env["README_RST"]):
            readmtester.call(env["README_RST"])
        else:
            print("No README.rst found in project root")
