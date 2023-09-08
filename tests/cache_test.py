"""
tests._cache_test
=================
"""
# pylint: disable=too-many-locals,too-many-statements,too-many-arguments
from __future__ import annotations

import json
import typing as t
from pathlib import Path

import git.exc
import pytest

import pyaud

from . import ContentHash, FixtureMain, FixtureMockRepo, flag, python_file

FALLBACK = "fallback"
UNCOMMITTED = "uncommitted"
COMMITS = (
    "0c57dc943941566f47b9e7ee3208245d0bcd7656",
    "1c57dc943941566f47b9e7ee3208245d0bcd7656",
)
CONTENT_HASHES = (
    ContentHash("test content", "9473fdd0d880a43c21b7778d34872157"),
    ContentHash("wrong content", "5cabbd5b4a8d005184f0e7bd0bc432f1"),
)


@pytest.mark.parametrize(
    [
        "commit",
        "dirty",
        "rev",
        "existing_cache",
        "append",
        "cache_file_action",
        "python_file_action",
        "file_content",
        "wanted_content",
        "commandline_args",
        "expected_returncode",
        "expected_message",
        "expected_cache",
    ],
    [
        (
            COMMITS[0],
            False,
            f"{COMMITS[0]}\n{COMMITS[1]}",
            lambda x: {},
            pyaud.files.append,
            lambda _, __, ___: None,
            lambda x, y: x.write_text(y),
            CONTENT_HASHES[0].content_str,
            CONTENT_HASHES[0].content_str,
            (flag.fix,),
            0,
            pyaud.messages.SUCCESS_FILE,
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
        ),
        (
            COMMITS[0],
            False,
            f"{COMMITS[0]}\n{COMMITS[1]}",
            lambda x: {COMMITS[0]: {x: {}}, FALLBACK: {x: {}}},
            pyaud.files.append,
            lambda x, y, z: x.write_text(json.dumps(y(z))),
            lambda x, y: x.write_text(y),
            CONTENT_HASHES[0].content_str,
            CONTENT_HASHES[0].content_str,
            (flag.fix,),
            0,
            pyaud.messages.SUCCESS_FILE,
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
        ),
        (
            COMMITS[0],
            False,
            f"{COMMITS[0]}\n{COMMITS[1]}",
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
            pyaud.files.append,
            lambda x, y, z: x.write_text(json.dumps(y(z))),
            lambda x, y: x.write_text(y),
            CONTENT_HASHES[0].content_str,
            CONTENT_HASHES[0].content_str,
            (),
            0,
            pyaud.messages.NO_FILE_CHANGED,
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
        ),
        (
            COMMITS[0],
            False,
            f"{COMMITS[0]}\n{COMMITS[1]}",
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
            pyaud.files.append,
            lambda x, y, z: x.write_text(json.dumps(y(z))),
            lambda x, y: x.write_text(y),
            CONTENT_HASHES[1].content_str,
            CONTENT_HASHES[0].content_str,
            (),
            1,
            pyaud.messages.FAILED.format(returncode=1),
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
            },
        ),
        (
            COMMITS[0],
            False,
            f"{COMMITS[0]}\n{COMMITS[1]}",
            lambda x: {
                COMMITS[1]: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
            },
            pyaud.files.append,
            lambda x, y, z: x.write_text(json.dumps(y(z))),
            lambda x, y: x.write_text(y),
            CONTENT_HASHES[1].content_str,
            CONTENT_HASHES[0].content_str,
            (flag.fix,),
            0,
            pyaud.messages.SUCCESS_FILE,
            lambda x: {
                COMMITS[1]: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
        ),
        (
            COMMITS[0],
            False,
            f"{COMMITS[0]}\n{COMMITS[1]}",
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
            },
            pyaud.files.append,
            lambda x, y, z: x.write_text(json.dumps(y(z))),
            lambda x, y: x.write_text(y),
            CONTENT_HASHES[1].content_str,
            CONTENT_HASHES[0].content_str,
            (flag.fix,),
            0,
            pyaud.messages.SUCCESS_FILE,
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
        ),
        (
            COMMITS[0],
            True,
            f"{COMMITS[0]}\n{COMMITS[1]}",
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
            },
            pyaud.files.append,
            lambda x, y, z: x.write_text(json.dumps(y(z))),
            lambda x, y: x.write_text(y),
            CONTENT_HASHES[1].content_str,
            CONTENT_HASHES[0].content_str,
            (flag.fix,),
            0,
            pyaud.messages.SUCCESS_FILE,
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
                f"{UNCOMMITTED}-{COMMITS[0]}": {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
        ),
        (
            COMMITS[0],
            False,
            f"{COMMITS[0]}\n{COMMITS[1]}",
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
            lambda _: None,
            lambda x, y, z: x.write_text(json.dumps(y(z))),
            lambda _, __: None,
            None,
            CONTENT_HASHES[0].content_str,
            (),
            1,
            pyaud.messages.FAILED.format(returncode=1),
            lambda x: {
                COMMITS[0]: {x: {}},
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
        ),
        (
            COMMITS[0],
            False,
            f"{COMMITS[0]}\n{COMMITS[1]}",
            lambda: "no json",
            pyaud.files.append,
            lambda x, y, z: x.write_text(z),
            lambda x, y: x.write_text(y),
            CONTENT_HASHES[0].content_str,
            CONTENT_HASHES[0].content_str,
            (flag.fix,),
            0,
            pyaud.messages.SUCCESS_FILE,
            lambda x: {
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
        ),
        (
            COMMITS[0],
            False,
            COMMITS[0],
            lambda x: {
                COMMITS[1]: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[1].content_hash}
                },
            },
            pyaud.files.append,
            lambda x, y, z: x.write_text(json.dumps(y(z))),
            lambda x, y: x.write_text(y),
            CONTENT_HASHES[1].content_str,
            CONTENT_HASHES[0].content_str,
            (flag.fix,),
            0,
            pyaud.messages.SUCCESS_FILE,
            lambda x: {
                FALLBACK: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
                COMMITS[0]: {
                    x: {python_file[1]: CONTENT_HASHES[0].content_hash}
                },
            },
        ),
    ],
    ids=[
        "initial-bad",
        "initial-fix",
        "good-no-change",
        "bad",
        "bad-to-good",
        "commit-change",
        "dirty-working-tree",
        "unlink",
        "invalid-json",
        "test-gc",
    ],
)
def test_fix_file(
    capsys: pytest.CaptureFixture,
    main: FixtureMain,
    mock_repo: FixtureMockRepo,
    cache_file: Path,
    commit: str,
    dirty: bool,
    rev: str,
    existing_cache: t.Callable[[str], dict[str, dict[str, dict[str, str]]]],
    append: t.Callable[[Path], None],
    cache_file_action: t.Callable[
        [Path, t.Callable[[str], dict[str, dict[str, dict[str, str]]]], str],
        None,
    ],
    python_file_action: t.Callable[[Path, str], None],
    file_content: str,
    wanted_content: str,
    commandline_args: tuple[str, ...],
    expected_returncode: int,
    expected_message: str,
    expected_cache: t.Callable[[str], dict[str, dict[str, dict[str, str]]]],
) -> None:
    """Test file cache with single file fix.

    :param capsys: Capture sys out and err.
    :param main: Patch package entry point.
    :param mock_repo: Mock ``git.Repo`` class.
    :param cache_file: Create test cache dir and return a test cache
        file.
    :param commit: Commit hash of the environment that's being tested.
    :param dirty: Boolean value for whether working tree dirty.
    :param rev: Commits that have a revision.
    :param existing_cache: State of the cache file before testing.
    :param append: Append to files.
    :param cache_file_action: Action to write to existing cache file.
    :param python_file_action: Action to write to existing python file.
    :param file_content: Contents of file for testing.
    :param wanted_content: Content that should be in the file for the
        audit to pass.
    :param commandline_args: Args that will be passed to main for
        testing.
    :param expected_returncode: Expected returncode resulting from test.
    :param expected_message: Expected message output resulting from
        test.
    :param expected_cache: Expected state of the cache file after test.
    """
    path = Path.cwd() / python_file[1]

    class _Whitelist(pyaud.plugins.Fix):
        cache_file = path
        content = wanted_content

        def audit(self, *args: str, **kwargs: bool) -> int:
            if self.cache_file.is_file():
                return int(
                    self.cache_file.read_text(encoding="utf-8") != self.content
                )

            return 1

        def fix(self, *args: str, **kwargs: bool) -> int:
            self.cache_file.write_text(self.content, encoding="utf-8")
            return int(
                self.cache_file.read_text(encoding="utf-8") != self.content
            )

    name = "whitelist"
    mock_repo(
        rev_parse=lambda _: commit,
        status=lambda _: dirty,
        rev_list=lambda _: rev,
    )
    append(path)
    cache_file_action(cache_file, existing_cache, str(_Whitelist))
    pyaud.plugins.register()(_Whitelist)
    python_file_action(path, file_content)
    returncode = main(name, *commandline_args)
    out = capsys.readouterr()[expected_returncode]
    cache = json.loads(cache_file.read_text())
    assert returncode == expected_returncode
    assert expected_message in out
    assert cache == expected_cache(str(_Whitelist))
    pyaud.files.clear()


@pytest.mark.parametrize(
    "no_cache,use_cache_all,expected_returncode,expected_output,conditions",
    [
        (
            False,
            False,
            0,
            [
                pyaud.messages.SUCCESS_FILES.format(len=3),
                pyaud.messages.NO_FILES_CHANGED,
                pyaud.messages.SUCCESS_FILES.format(len=1),
            ],
            [
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
                (
                    lambda x, y: x not in y,
                    lambda x, y: x not in y,
                    lambda x, y: x not in y,
                ),
                (
                    lambda x, y: x in y,
                    lambda x, y: x not in y,
                    lambda x, y: x not in y,
                ),
            ],
        ),
        (
            False,
            False,
            1,
            [
                pyaud.messages.FAILED.format(returncode=1),
                pyaud.messages.FAILED.format(returncode=1),
                pyaud.messages.FAILED.format(returncode=1),
            ],
            [
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
            ],
        ),
        (
            False,
            True,
            0,
            [
                pyaud.messages.SUCCESS_FILES.format(len=3),
                pyaud.messages.NO_FILES_CHANGED,
                pyaud.messages.SUCCESS_FILES.format(len=3),
            ],
            [
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
                (
                    lambda x, y: x not in y,
                    lambda x, y: x not in y,
                    lambda x, y: x not in y,
                ),
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
            ],
        ),
        (
            False,
            True,
            1,
            [
                pyaud.messages.FAILED.format(returncode=1),
                pyaud.messages.FAILED.format(returncode=1),
                pyaud.messages.FAILED.format(returncode=1),
            ],
            [
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
            ],
        ),
        (
            True,
            True,
            0,
            [
                pyaud.messages.SUCCESS_FILES.format(len=3),
                pyaud.messages.SUCCESS_FILES.format(len=3),
                pyaud.messages.SUCCESS_FILES.format(len=3),
            ],
            [
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
                (
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                    lambda x, y: x in y,
                ),
            ],
        ),
    ],
    ids=[
        "no-cache-all-passed",
        "no-cache-all-failed",
        "cache-all-passed",
        "cache-all-failed",
        "test-no-cache-passed",
    ],
)
def test_no_cache_all(
    capsys: pytest.CaptureFixture,
    main: FixtureMain,
    no_cache: bool,
    use_cache_all: bool,
    expected_returncode: int,
    expected_output: list[str],
    conditions: list[
        tuple[
            t.Callable[[Path, list[Path]], bool],
            t.Callable[[Path, list[Path]], bool],
            t.Callable[[Path, list[Path]], bool],
        ]
    ],
) -> None:
    """Test caching of all files.

    All files have to be processed for this check to be skipped.

    :param capsys: Capture sys out and err.
    :param main: Patch package entry point.
    :param no_cache: Boolean value for whether to use cache or not.
    :param use_cache_all: Cache all files to skip an audit or cache
        single files to skip a file in an audit.
    :param expected_returncode: Expected returncode.
    :param expected_output: Expected stdout or stderr.
    :param conditions: Condition for path in files object.
    """
    #: Setup files
    #: ===========
    files: list[Path] = []
    paths = [Path.cwd() / python_file[i] for i in range(3)]
    paths[0].write_text("one")
    paths[1].write_text("two")
    paths[2].write_text("three")
    pyaud.files.extend([paths[0], paths[1], paths[2]])

    #: Setup class
    #: ===========
    class _Lint(pyaud.plugins.Audit):
        cache = True
        cache_all = use_cache_all

        def audit(self, *args: str, **kwargs: bool) -> int:
            files.extend(pyaud.files)
            return expected_returncode

    name = _Lint.__name__[1:].lower()
    pyaud.plugins.register()(_Lint)

    #: First Run
    #: =========
    #: No files have been cached.
    #: Populating first cache.
    returncode = main(name, flag.no_cache) if no_cache else main(name)
    out = capsys.readouterr()[expected_returncode]
    assert expected_output[0] in out
    assert returncode == expected_returncode
    assert conditions[0][0](paths[0], files)
    assert conditions[0][1](paths[1], files)
    assert conditions[0][2](paths[2], files)
    files.clear()

    #: Second Run
    #: ==========
    #: Files cached.
    #: Running off cache generated through previous run.
    returncode = main(name)
    out = capsys.readouterr()[expected_returncode]
    assert expected_output[1] in out
    assert returncode == expected_returncode
    assert conditions[1][0](paths[0], files)
    assert conditions[1][1](paths[1], files)
    assert conditions[1][2](paths[2], files)
    files.clear()

    #: Third Run
    #: =========
    #: Cache generated and used.
    #: Updating new cache from this run.
    paths[0].write_text("one changed file")
    returncode = main(name)
    out = capsys.readouterr()[expected_returncode]
    assert expected_output[2] in out
    assert returncode == expected_returncode
    assert conditions[2][0](paths[0], files)
    assert conditions[2][1](paths[1], files)
    assert conditions[2][2](paths[2], files)
    files.clear()


def test_no_rev(main: FixtureMain, mock_repo: FixtureMockRepo) -> None:
    """Test caching of single file with multi stage audit.

    :param main: Patch package entry point.
    :param mock_repo: Mock ``git.Repo`` class.
    """
    path = Path.cwd() / python_file[0]

    class _Whitelist(pyaud.plugins.Action):
        cache_file = path.name

        def action(self, *args: str, **kwargs: bool) -> int:
            return 0

    def _rev_parse(_):
        raise git.GitCommandError("command")

    path.write_text(CONTENT_HASHES[0].content_str)
    pyaud.files.append(path)
    mock_repo(rev_parse=_rev_parse, status=lambda _: False)
    name = _Whitelist.__name__[1:].lower()
    pyaud.plugins.register()(_Whitelist)
    returncode = main(name)
    assert returncode == 0
