"""
tests.cache_test
================
"""
# pylint: disable=protected-access,too-few-public-methods,no-member,no-self-use
# pylint: disable=too-many-arguments,too-many-statements,invalid-name
import copy
import json
import os
import typing as t
from pathlib import Path

import pytest

import pyaud
from pyaud import environ as pe

from . import (
    FILES,
    INIT,
    REPO,
    MockCachedPluginType,
    NoColorCapsys,
    StrategyMockPlugin,
    Tracker,
)

FileHashDict = t.Dict[str, str]
ClsDict = t.Dict[str, FileHashDict]
CommitDict = t.Dict[str, ClsDict]
CacheDict = t.Dict[str, CommitDict]
CacheUnion = t.Union[CacheDict, CommitDict, ClsDict, FileHashDict]


def test_no_cache(monkeypatch: pytest.MonkeyPatch, main: t.Any) -> None:
    """Test all runs as should when ``-n/--no-cache`` arg is passed.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    """

    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name="plugin")
    class Plugin(pyaud.plugins.Action):  # pylint: disable=unused-variable
        """Nothing to do."""

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            """Nothing to do."""

    match_parent = Tracker()
    match_file = Tracker()
    remove = Tracker()
    clear = Tracker()
    hash_files = Tracker()
    save_cache = Tracker()
    monkeypatch.setattr("pyaud.plugins._files.remove", remove)
    monkeypatch.setattr("pyaud.plugins._files.clear", clear)
    monkeypatch.setattr(
        "pyaud._cache.HashMapping.write", lambda *_: save_cache
    )
    main("plugin", "--no-cache")
    assert match_parent.was_called() is False
    assert match_file.was_called() is False
    assert remove.was_called() is False
    assert clear.was_called() is False
    assert hash_files.was_called() is False
    assert save_cache.was_called() is False


def test_remove_matched_files(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that correct files are removed for matching md5 hashes.

    :param monkeypatch: Mock patch environment and attributes.
    """
    remove = Tracker()
    pyaud.plugins._files.append(Path.cwd() / REPO)
    monkeypatch.setattr("pyaud.plugins._files.remove", remove)
    monkeypatch.setattr("pyaud._cache._Path.read_bytes", lambda *_: b"")
    monkeypatch.setattr("pyaud._cache.HashMapping.match_file", lambda *_: True)
    # noinspection PyUnresolvedReferences
    class_decorator = pyaud._wraps.ClassDecorator(MockCachedPluginType)
    MockCachedPluginType.__call__ = class_decorator.files(  # type: ignore
        MockCachedPluginType.__call__
    )
    obj = MockCachedPluginType("object")
    obj()
    assert remove.was_called() is True


# noinspection PyUnresolvedReferences
class TestCacheStrategy:
    """Test strategy."""

    #: PACKAGES
    P = (REPO,)

    #: COMMITS
    C = (
        pyaud._cache.HashMapping._FALLBACK,
        "7c57dc943941566f47b9e7ee3208245d0bcd7656",
        "7c57dc943941566f47b9e7ee3208245d0bcd7657",
        "7c57dc943941566f47b9e7ee3208245d0bcd7658",
    )

    #: CLASS NAMES
    N = ("MockPlugin1", "MockPlugin2")

    #: FILE HASHES
    H = (
        "2e8246890aa2d92b0a793279527aa64e",
        "28e644b6bf7ba8083bf6749c5c50df9c",
        "07fbf822c1b1fb1a8cd0646ca2c248a7",
        "a2cd06cc24b8bf0327d6b5c1dd6a7f9f",
        "b26d6c0d8dcf45ea0c27546a0f4f18d1",
        "5bc4970a3b076a058d17904ed17586be",
        "0845ae1927a40f6de1e7e3e7e5b9dacf",
        "986672f10a7cf52375c9e44b292e245f",
        "6e0888c79c8471f3ac2bd76939e2dc4c",
    )

    NO_CHANGE_MSG = "No changes have been made to audited files"

    def _get_commit(self, commit: int, prefixed: bool = False) -> str:
        key = self.C[commit]
        if prefixed:
            return f"uncommitted-{key}"

        return key

    def _cls_key(self, name: int) -> str:
        return f"<class 'abc.{self.N[name]}'>"

    def _idx(
        self,
        o: CacheDict,
        p: t.Optional[int] = None,
        c: t.Optional[int] = None,
        n: t.Optional[int] = None,
        prefix: bool = False,
    ) -> CacheUnion:
        if p is not None:
            o: CommitDict = o[self.P[p]]  # type: ignore
            if c is not None:
                o: ClsDict = o[self._get_commit(c, prefix)]  # type: ignore
                if n is not None:
                    o: FileHashDict = o[self._cls_key(n)]  # type: ignore

        return o

    @staticmethod
    def _d_eq(o1: CacheUnion, o2: CacheUnion) -> bool:
        return json.dumps(o1, sort_keys=True) == json.dumps(o2, sort_keys=True)

    def _cls_in_commit(
        self, o: CacheDict, p: int, c: int, n: int, prefix=False
    ) -> bool:
        return self._cls_key(n) in o[self.P[p]][self._get_commit(c, prefix)]

    def _get_instance(
        self,
        monkeypatch: pytest.MonkeyPatch,
        c: int,
        n: int,
        clean: bool = True,
        cache_all: bool = False,
        cache_file: t.Optional[Path] = None,
        single_file: bool = False,
    ) -> type:
        monkeypatch.setattr("pyaud._cache._get_commit_hash", lambda: self.C[c])
        monkeypatch.setattr("pyaud._cache._working_tree_clean", lambda: clean)
        attr = "file" if single_file else "files"
        check = getattr(pyaud._wraps.CheckCommand, attr)
        strat = copy.deepcopy(StrategyMockPlugin)
        strat.cache_all = cache_all
        strat.cache_file = cache_file
        plugin = type(self.N[n], (StrategyMockPlugin,), {})
        plugin.__call__ = check(plugin.__call__)  # type: ignore
        return plugin(self.N[n])

    @staticmethod
    def _success_msg(i: int) -> str:
        return f"Success: no issues found in {i} source files"

    @staticmethod
    def _fmt(o: t.Dict[Path, str]) -> FileHashDict:
        return {str(k.relative_to(Path.cwd())): v for k, v in o.items()}

    # noinspection DuplicatedCode
    @pytest.mark.usefixtures(
        "unpatch_hash_mapping_hash_files", "unpatch_hash_mapping_match_file"
    )
    def test_cache(
        self, monkeypatch: pytest.MonkeyPatch, nocolorcapsys: NoColorCapsys
    ) -> None:
        """Test cache strategy.

        :param monkeypatch: Mock patch environment and attributes.
        :param nocolorcapsys: Capture system output while stripping ANSI
            color codes.
        """
        #: PATHS
        p = (
            Path.cwd() / REPO / "__main__.py",
            Path.cwd() / REPO / "_version.py",
            Path.cwd() / REPO / INIT,
            Path.cwd() / REPO / FILES,
            Path.cwd() / "plugins" / INIT,
            Path.cwd() / "plugins" / FILES,
            Path.cwd() / "tests" / INIT,
            Path.cwd() / "tests" / "_test.py",
            Path.cwd() / "tests" / "conftest.py",
        )

        #: FILES & HASHES
        f = {p[c]: self.H[c] for c, _ in enumerate(p)}

        #: When hashlib.md5(path.read_bytes()).hexdigest() is called
        #: `Path`'s returned self will match to the key in init and
        #: hexdigest` will return the hash value
        class _Md5:
            def __init__(self, path: Path) -> None:
                self.path = path

            def hexdigest(self) -> str:
                """Mock to return predefined hash.

                :return: Mapped hash to `Path` key.
                """
                return f[self.path]

        monkeypatch.setattr("pyaud._cache._Path.read_bytes", lambda x: x)
        monkeypatch.setattr("pyaud._cache._hashlib.md5", _Md5)
        pyaud.files.extend(f.keys())

        #: Test when there is no cache file already.
        #: Test that a new instance is created wrapped with a cache
        #: object pegged to a commit.
        #: Test calling of the plugin instance.
        #: Test success message is displayed with the correct number of
        #: files noted as completed.
        #: Test that the cache object holds a dict, with the commit as
        #: the primary key, and the plugin which called the process.
        #: Test that the object is identical to the fallback, as the
        #: last process called.
        i1 = self._get_instance(monkeypatch, 1, 0)
        i1()
        o = json.loads(pe.FILECACHE_FILE.read_text())
        assert self._success_msg(len(f)) in nocolorcapsys.stdout()
        assert self._cls_in_commit(o, 0, 1, 0)
        assert self._d_eq(self._idx(o, 0, 1, 0), self._fmt(f))
        assert self._d_eq(self._idx(o, 0, 1), self._idx(o, 0, 0))

        #: Test when a process is run again with no changes to anything.
        #: Call the instance again.
        #: Test that a success message notifies user that no changes
        #: have been made, so no process needed to be run.
        i1()
        o = json.loads(pe.FILECACHE_FILE.read_text())
        assert self.NO_CHANGE_MSG in nocolorcapsys.stdout()
        assert self._cls_in_commit(o, 0, 1, 0)
        assert self._d_eq(self._idx(o, 0, 1), self._idx(o, 0, 0))

        #: Test when a process is run again with changes to a file.
        #: Call the instance again.
        #: Test that a success message notifies user that only 1 change
        #: have been made, so only a partial process needed to be run.
        f[p[0]] = f[p[0]][::-1]
        i1()
        o = json.loads(pe.FILECACHE_FILE.read_text())
        assert self._success_msg(1) in nocolorcapsys.stdout()
        assert self._cls_in_commit(o, 0, 1, 0)
        assert self._d_eq(self._idx(o, 0, 1), self._idx(o, 0, 0))

        #: Test new process running under a different commit.
        #: Test that instance displays a success message notifying user
        #: that no changes have been made, so no process needs to be
        #: run.
        #: The commit should have been able to copy the fallback as a
        #: start to minimally find any changed files.
        #: Test that the object is identical to the fallback, as it is
        #: the last process that ran.
        i2 = self._get_instance(monkeypatch, 2, 0)
        i2()
        o = json.loads(pe.FILECACHE_FILE.read_text())
        assert self.NO_CHANGE_MSG in nocolorcapsys.stdout()
        assert self._cls_in_commit(o, 0, 1, 0)
        assert self._d_eq(self._idx(o, 0, 1), self._idx(o, 0, 0))
        assert self._cls_in_commit(o, 0, 2, 0)
        assert self._d_eq(self._idx(o, 0, 2), self._idx(o, 0, 0))

        #: Call the instance's ``__call__`` again.
        #: instance displays a success message again with the correct
        #: number of files noted as completed.
        #: The process needs to ignore all prior cache as this is an
        #: entirely new process that hasn't been checked for validity.
        #: Test that the first cache object still holds a dict with the
        #: commit as the name and the plugin which called the
        #: process.
        #: Also test that the object holds a dict with the second commit
        #: as the name and the same plugin which called the process.
        #: Test that the object is still identical to the fallback, as
        #: it is still the last process that ran.
        i3 = self._get_instance(monkeypatch, 1, 1)
        i3()
        o = json.loads(pe.FILECACHE_FILE.read_text())
        assert self._success_msg(len(f)) in nocolorcapsys.stdout()
        assert self._cls_in_commit(o, 0, 1, 0)
        assert self._cls_in_commit(o, 0, 1, 1)
        assert self._d_eq(self._idx(o, 0, 1), self._idx(o, 0, 0))
        assert self._cls_in_commit(o, 0, 2, 0)
        assert not self._d_eq(self._idx(o, 0, 2), self._idx(o, 0, 0))

        #: Test that a new class is being used.
        #: instance displays a success message with the correct number
        #: of files noted as completed.
        #: Test that the first object still exists and is still
        #: identical to the fallback as it does not hold any fewer
        #: objects than any of the other objects, therefore any of the
        #: latter objects will have borrowed its values from the
        #: fallback.
        #: Test that the second object still exists, but that it is not
        #: identical to the fallback as it is not the last process which
        #: was run.
        #: Test that the cache object holds a dict with the commit as
        #: the name, the plugin which called the process, and that the
        #: object is identical to the fallback, as it is the last
        #: process that ran.
        i4 = self._get_instance(monkeypatch, 3, 1)
        i4()
        o = json.loads(pe.FILECACHE_FILE.read_text())
        assert self.NO_CHANGE_MSG in nocolorcapsys.stdout()
        assert self._cls_in_commit(o, 0, 1, 0)
        assert self._cls_in_commit(o, 0, 1, 1)
        assert self._d_eq(self._idx(o, 0, 1), self._idx(o, 0, 0))
        assert self._cls_in_commit(o, 0, 2, 0)
        assert not self._d_eq(self._idx(o, 0, 2), self._idx(o, 0, 0))
        assert self._cls_in_commit(o, 0, 3, 1)
        assert self._d_eq(self._idx(o, 0, 3), self._idx(o, 0, 0))

        #: Test a new instance running under a new commit.
        #: Test that a new object is created when working on a commit
        #: with uncommitted changes.
        #: Only one tagged object like this should exist for each
        #: commit.
        #: Test this is used as the fallback as it is the last process
        #: called.
        i5 = self._get_instance(monkeypatch, 3, 1, clean=False)
        i5()
        o = json.loads(pe.FILECACHE_FILE.read_text())
        assert self.NO_CHANGE_MSG in nocolorcapsys.stdout()
        assert self._cls_in_commit(o, 0, 1, 0)
        assert self._cls_in_commit(o, 0, 1, 1)
        assert self._d_eq(self._idx(o, 0, 1), self._idx(o, 0, 0))
        assert self._cls_in_commit(o, 0, 2, 0)
        assert not self._d_eq(self._idx(o, 0, 2), self._idx(o, 0, 0))
        assert self._cls_in_commit(o, 0, 3, 1)
        assert self._d_eq(self._idx(o, 0, 3), self._idx(o, 0, 0))
        assert self._cls_in_commit(o, 0, 3, 1)
        assert self._d_eq(self._idx(o, 0, 3, prefix=True), self._idx(o, 0, 0))

        #: Test files hashes
        assert self._d_eq(self._idx(o, 0, 1, 0), self._fmt(f))
        assert self._d_eq(self._idx(o, 0, 1, 1), self._fmt(f))
        assert self._d_eq(self._idx(o, 0, 2, 0), self._fmt(f))
        assert self._d_eq(self._idx(o, 0, 3, 1), self._fmt(f))
        assert self._d_eq(self._idx(o, 0, 3, 1, prefix=True), self._fmt(f))

        #: Test all files get repopulated if a ``cache_all`` flag is set
        #: to True.
        #: ``cache_all`` means that all files must be saved, or
        # otherwise the cache is void.
        i6 = self._get_instance(monkeypatch, 1, 0, cache_all=True)
        f[p[1]] = f[p[1]][::-1]
        i6()
        o = json.loads(pe.FILECACHE_FILE.read_text())
        assert self._success_msg(len(f)) in nocolorcapsys.stdout()
        assert self._cls_in_commit(o, 0, 1, 0)
        assert self._d_eq(self._idx(o, 0, 1), self._idx(o, 0, 0))

    @pytest.mark.usefixtures(
        "unpatch_hash_mapping_hash_files", "unpatch_hash_mapping_match_file"
    )
    def test_cache_file(self, nocolorcapsys) -> None:
        """Test caching a single file.

        :param monkeypatch: Mock patch environment and attributes.
        :param nocolorcapsys: Capture system output while stripping ANSI
            color codes.
        """
        expected_1 = "Success: no issues found in file"
        path = Path.cwd() / "whitelist.py"

        class _Fix(pyaud.plugins.Fix):
            cache_file = path

            def audit(self, *args: str, **kwargs: bool) -> int:
                if self.cache_file.is_file():
                    return int(self.cache_file.read_text() != "unused")

                return 1

            def fix(self, *args: str, **kwargs: bool) -> int:
                path.write_text("unused")
                return 0

        fix = _Fix("name")
        with pytest.raises(pyaud.exceptions.AuditError):
            fix()

        fix(fix=True)
        assert expected_1 in nocolorcapsys.stdout()

        fix()
        assert (
            "No changes have been made to audited file"
            in nocolorcapsys.stdout()
        )

        path.write_text("change")
        with pytest.raises(pyaud.exceptions.AuditError):
            fix()

        fix(fix=True)
        assert expected_1 in nocolorcapsys.stdout()

        os.remove(path)
        with pytest.raises(pyaud.exceptions.AuditError):
            fix()

        fix(fix=True)
        assert (
            "No changes have been made to audited file"
            not in nocolorcapsys.stdout()
        )
