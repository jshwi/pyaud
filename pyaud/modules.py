"""
pyaud.modules
=============
"""
import os
import shutil
import tempfile
from pathlib import Path
from subprocess import CalledProcessError

from .config import generate_rcfile, toml
from .environ import (
    DOCS,
    DOCS_CONF,
    NAME,
    PIPFILE_LOCK,
    README,
    TESTS,
    TempEnvVar,
    find_package,
)
from .exceptions import PyAuditError
from .plugins import register
from .utils import (
    LineSwitch,
    Subprocess,
    check_command,
    colors,
    deploy_docs,
    get_branch,
    git,
    tree,
    write_command,
)


@register(name="clean")
def make_clean(**kwargs: bool) -> None:
    """Remove all unversioned package files recursively.

    :param kwargs:  Additional keyword arguments for ``git clean``.
    """
    exclude = toml["clean"]["exclude"]
    return git.clean(  # type: ignore
        "-fdx", *[f"--exclude={e}" for e in exclude], **kwargs
    )


@register(name="coverage")
def make_coverage(**kwargs: bool) -> None:
    """Run package unit-tests with ``pytest`` and ``coverage``.

    :param kwargs:  Pass keyword arguments to ``pytest`` and ``call``.
    """
    coverage = Subprocess("coverage")
    returncode = make_tests(*[f"--cov={e}" for e in tree.reduce()], **kwargs)
    if not returncode:
        with TempEnvVar(kwargs, suppress=True):
            coverage.call("xml", **kwargs)
    else:
        print("No coverage to report")


@register(name="deploy")
def make_deploy(**kwargs: bool) -> None:
    """Deploy package documentation and test coverage.

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
        deploy_module(**kwargs)


@register(name="deploy-cov")
def make_deploy_cov(**kwargs: bool) -> None:
    """Upload coverage data to ``Codecov``.

    If no file exists otherwise announce that no file has been created
    yet. If no ``CODECOV_TOKEN`` environment variable has been exported
    or defined in ``.env`` announce that no authorization token has been
    created yet.

    :param kwargs: Pass keyword arguments to ``call``.
    """
    codecov = Subprocess("codecov")
    coverage_xml = Path.cwd() / os.environ["PYAUD_COVERAGE_XML"]
    if coverage_xml.is_file():
        if os.environ["CODECOV_TOKEN"] != "":
            codecov.call("--file", Path.cwd() / coverage_xml, **kwargs)
        else:
            print("CODECOV_TOKEN not set")
    else:
        print("No coverage report found")


@register(name="deploy-docs")
def make_deploy_docs(**kwargs: bool) -> None:
    """Deploy package documentation to ``gh-pages``.

    Check that the branch is being pushed as master (or other branch
    for tests). If the correct branch is the one in use deploy.
    ``gh-pages`` to the orphaned branch - otherwise do nothing and
    announce.

    :param kwargs: Pass keyword arguments to ``make_docs``.
    """
    if get_branch() == "master":
        git_credentials = ["PYAUD_GH_NAME", "PYAUD_GH_EMAIL", "PYAUD_GH_TOKEN"]
        null_vals = [k for k in git_credentials if os.environ[k] == ""]
        if not null_vals:
            if not Path(Path.cwd() / os.environ["BUILDDIR"] / "html").is_dir():
                make_docs(**kwargs)

            deploy_docs()
        else:
            print("The following is not set:")
            for null_val in null_vals:
                print(f"- {null_val}")

            print()
            print("Pushing skipped")
    else:
        colors.green.print("Documentation not for master")
        print("Pushing skipped")


@register(name="docs")
def make_docs(**kwargs: bool) -> None:
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
    build_dir = Path.cwd() / os.environ["BUILDDIR"]
    if build_dir.is_dir():
        shutil.rmtree(build_dir)

    sphinx_build = Subprocess("sphinx-build")
    if Path(Path.cwd() / DOCS).is_dir() and Path(Path.cwd(), README).is_file():
        with LineSwitch(Path.cwd() / README, {0: readme_rst, 1: underline}):
            command = ["-M", "html", Path.cwd() / DOCS, build_dir, "-W"]
            sphinx_build.call(*command, **kwargs)
            colors.green.bold.print("Build successful")
    else:
        print("No docs found")


@register(name="files")
def make_files(**kwargs: bool) -> None:
    """Audit project data files.

    Make ``docs/<APPNAME>.rst``, ``whitelist.py``, and
    ``requirements.txt`` if none already exist, update them if they do
    and changes are needed or pass if nothing needs to be done.

    :param kwargs:  Pass keyword arguments to ``func``.
    :return:        Exit status.
    """
    for func in (make_requirements, make_toc, make_whitelist):
        func(**kwargs)


@register(name="format")
@check_command
def make_format(**kwargs: bool) -> int:
    """Audit code against ``Black``.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    :return:        Exit status.
    """
    black = Subprocess("black", loglevel="debug")
    args = tree.reduce()
    try:
        return black.call("--check", *args, **kwargs)

    except CalledProcessError as err:
        black.call(*args, **kwargs)
        if kwargs.get("fix", False):
            return black.call(*args, **kwargs)

        raise PyAuditError(f"{black} {tuple([str(p) for p in args])}") from err


@register(name="lint")
@check_command
def make_lint(**kwargs: bool) -> int:
    """Lint code with ``pylint``.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    with TempEnvVar(os.environ, PYCHARM_HOSTED="True"):
        args = tree.reduce()
        pylint = Subprocess("pylint")
        return pylint.call("--output-format=colorized", *args, **kwargs)


@register(name="requirements")
@write_command("PYAUD_REQUIREMENTS", required="PYAUD_PIPFILE_LOCK")
def make_requirements(**kwargs: bool) -> None:
    """Audit requirements.txt with Pipfile.lock.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    """
    # get the stdout for both production and development packages
    pipfile_lock_path = Path.cwd() / PIPFILE_LOCK
    requirements_path = Path.cwd() / os.environ["PYAUD_REQUIREMENTS"]

    # get the stdout for both production and development packages
    p2req = Subprocess("pipfile2req", capture=True)
    p2req.call(pipfile_lock_path, **kwargs)
    p2req.call(pipfile_lock_path, "--dev", **kwargs)

    # write to file and then use sed to remove the additional
    # information following the semi-colon
    stdout = list(set("\n".join(p2req.stdout()).splitlines()))
    stdout.sort()
    with open(requirements_path, "w") as fout:
        for content in stdout:
            fout.write(f"{content.split(';')[0]}\n")


@register(name="tests")
def make_tests(*args: str, **kwargs: bool) -> int:
    """Run the package unit-tests with ``pytest``.

    :param args:    Additional positional arguments for ``pytest``.
    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    tests = Path.cwd() / TESTS
    patterns = ("test_*.py", "*_test.py")
    pytest = Subprocess("pytest")
    rglob = [
        f
        for f in tree
        for p in patterns
        if f.match(p) and str(tests) in str(f)
    ]
    if rglob:
        return pytest.call(*args, **kwargs)

    print("No tests found")
    return 1


@register(name="toc")
@write_command("PYAUD_TOC", required="PYAUD_DOCS")
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
    package = find_package()
    docspath = Path.cwd() / DOCS
    tocpath = docspath / f"{package}.rst"
    if Path(Path.cwd() / DOCS_CONF).is_file():
        apidoc = Subprocess("sphinx-apidoc")
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


@register(name="typecheck")
@check_command
def make_typecheck(**kwargs: bool) -> int:
    """Typecheck code with ``mypy``.

    Check that there are no errors between the files and their
    stub-files.

    :param kwargs:  Pass keyword arguments to ``call``.
    :return:        Exit status.
    """
    mypy = Subprocess("mypy")
    return mypy.call("--ignore-missing-imports", *tree.reduce(), **kwargs)


@register(name="unused")
@check_command
def make_unused(**kwargs: bool) -> int:
    """Audit unused code with ``vulture``.

    Create whitelist first with --fix.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    :return:        Exit status.
    """
    whitelist = Path.cwd() / os.environ["PYAUD_WHITELIST"]
    args = tree.reduce()
    vulture = Subprocess("vulture")
    while True:
        try:
            if whitelist.is_file():
                args.append(whitelist)

            return vulture.call(*args, **kwargs)

        except CalledProcessError as err:
            if kwargs.get("fix", False):
                make_whitelist(**kwargs)
                return 0

            raise PyAuditError(
                f"{vulture} {tuple([str(i) for i in args])}"
            ) from err


@register(name="whitelist")
@write_command("PYAUD_WHITELIST")
def make_whitelist(**kwargs: bool) -> None:
    """Check whitelist.py file with ``vulture``.

    This will consider all unused code an exception so resolve code that
    is not to be excluded from the ``vulture`` search first.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    :return:        Exit status.
    """
    vulture = Subprocess("vulture", capture=True)

    # append whitelist exceptions for each individual module
    for item in tree.reduce():
        if item.exists():
            with TempEnvVar(kwargs, suppress=True):
                vulture.call(item, "--make-whitelist", **kwargs)

    # clear contents of instantiated ``TextIO' object to write a new
    # file and not append
    stdout = [i for i in "\n".join(vulture.stdout()).splitlines() if i != ""]
    stdout.sort()
    with open(Path.cwd() / os.environ["PYAUD_WHITELIST"], "w") as fout:
        for line in stdout:
            fout.write(f"{line.replace(str(Path.cwd()) + os.sep, '')}\n")


@register(name="imports")
@check_command
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
    isort = Subprocess("isort", devnull=True)
    black = Subprocess("black", loglevel="debug", devnull=True)
    for item in tree:
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
                    raise PyAuditError(
                        "{} {}".format(
                            make_imports.__name__,
                            tuple([str(p) for p in tree.reduce()]),
                        )
                    )

    return 0


@register(name="readme")
def make_readme(**kwargs: bool) -> None:
    """Parse, test, and assert RST code-blocks.

    :key suppress:  Suppress error and continue running even with a
                    non-zero exit status.
    :return:        Subprocess exit status.
    """
    with TempEnvVar(os.environ, PYCHARM_HOSTED="True"):
        readmtester = Subprocess("readmetester")
        if Path(Path.cwd() / README).is_file():
            readmtester.call(Path.cwd() / README, **kwargs)
        else:
            print("No README.rst found in project root")


@register(name="format-str")
@check_command
def make_format_str(**kwargs: bool) -> int:
    """Format f-strings with ``flynt``.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    :return:        Exit status.
    """
    flynt = Subprocess("flynt")
    args = ("--line-length", "72", "--transform-concats", *tree.reduce())
    try:
        return flynt.call(
            "--dry-run", "--fail-on-change", *args, devnull=True, **kwargs
        )

    except CalledProcessError as err:
        if kwargs.get("fix", False):
            return flynt.call(*args, **kwargs)

        raise PyAuditError(f"{flynt} {tuple([str(p) for p in args])}") from err


@register(name="format-docs")
@check_command
def make_format_docs(**kwargs: bool) -> int:
    """Format docstrings with ``docformatter``.

    :param kwargs:  Pass keyword arguments to ``call``.
    :key fix:       Do not raise error - fix problem instead.
    :return:        Exit status.
    """
    docformatter = Subprocess("docformatter")
    args = ("--recursive", "--wrap-summaries", "72", *tree.reduce())
    try:
        return docformatter.call("--check", *args, **kwargs)

    except CalledProcessError as err:
        args = ("--in-place", *args)
        if kwargs.get("fix", False):
            return docformatter.call(*args, **kwargs)

        raise PyAuditError(
            f"{docformatter} {tuple([str(p) for p in args])}"
        ) from err


@register(name="generate-rcfile")
def make_generate_rcfile(**__: bool) -> None:
    """Print rcfile to stdout.

    Print rcfile to stdout so it may be piped to chosen filepath.
    """
    generate_rcfile()
