from copy import deepcopy
from datetime import datetime
import pytest
from changelog_keeper.keeper import (
    Config,
    Changelog,
    ChangelogKeeper,
    ChangelogKeeperError,
    ENDLINE_CHAR,
    Operation,
    UNRELEASED_VERSION_NAME,
    Version,
)
from changelog_keeper.model import ChangeType


class TestKeeper:
    @pytest.fixture
    def config(self) -> Config:
        return Config(
            operation=Operation.CHECK,
            change_type=ChangeType.CHANGED,
            entry="Some entry",
            version="some.version",
            repo_ref="v.some.version",
        )

    @pytest.fixture
    def keeper(self, config: Config) -> ChangelogKeeper:
        return ChangelogKeeper(config)

    @pytest.fixture
    def changelog(self) -> Changelog:
        changelog = Changelog()
        changelog.header = ChangelogKeeper.DEFAULT_HEADER
        changelog.append_top(Version(UNRELEASED_VERSION_NAME, None, None, False))
        return changelog

    def test_create(self, keeper: ChangelogKeeper, changelog: Changelog):
        assert changelog == keeper._create()

    @pytest.fixture
    def expected_add_changelog(
        self, keeper: ChangelogKeeper, changelog: Changelog
    ) -> Changelog:
        expected = deepcopy(changelog)
        expected[UNRELEASED_VERSION_NAME].changes.setdefault(
            keeper.config.change_type, set()
        ).add(tuple(keeper.config.entry.split(ENDLINE_CHAR)))
        return expected

    def test_add(
        self,
        keeper: ChangelogKeeper,
        changelog: Changelog,
        expected_add_changelog: Changelog,
    ):
        keeper._add(changelog)
        assert expected_add_changelog == changelog

    @pytest.fixture
    def expected_release_changelog(
        self, keeper: ChangelogKeeper, expected_add_changelog: Changelog
    ) -> Changelog:
        expected = deepcopy(expected_add_changelog)
        expected.release(
            UNRELEASED_VERSION_NAME, keeper.config.version, keeper.config.repo_ref
        )
        expected.append_top(Version(UNRELEASED_VERSION_NAME, None, None, False))
        return expected

    def test_release(
        self,
        keeper: ChangelogKeeper,
        expected_add_changelog: Changelog,
        expected_release_changelog: Changelog,
    ):
        keeper.config.repo_ref = expected_release_changelog[keeper.config.version].ref
        keeper._release(expected_add_changelog)
        assert expected_release_changelog == expected_add_changelog

    @pytest.fixture
    def expected_yank_changelog(
        self, keeper: ChangelogKeeper, expected_release_changelog: Changelog
    ) -> Changelog:
        expected = deepcopy(expected_release_changelog)
        expected[keeper.config.version]._yank()
        return expected

    def test_yank(
        self,
        keeper: ChangelogKeeper,
        expected_release_changelog: Changelog,
        expected_yank_changelog: Changelog,
    ):
        keeper._yank(expected_release_changelog)
        assert expected_yank_changelog == expected_release_changelog

    def test_check_successful(self, keeper: ChangelogKeeper, changelog: Changelog):
        expected = deepcopy(changelog)
        keeper._check(changelog)
        assert expected == changelog

    def test_check_failed(self, keeper: ChangelogKeeper):
        changelog = Changelog()
        self._validate_fail(  # No unreleased version
            keeper, changelog, "There is no Unreleased version in the changelog"
        )
        changelog.append_top(Version(UNRELEASED_VERSION_NAME, None, None, False))
        changelog.append_top(Version("Fancy version", None, datetime.now(), False))
        self._validate_fail(  # First version has to be called Unreleased
            keeper,
            changelog,
            "Unreleased version is not a first version in the changelog",
        )
        changelog.release(UNRELEASED_VERSION_NAME, "Fancy_version2.0", None)
        changelog.append_top(Version(UNRELEASED_VERSION_NAME + "1", None, None, False))
        changelog.append_top(Version(UNRELEASED_VERSION_NAME, None, None, False))
        self._validate_fail(  # There has to be always one version unreleased
            keeper,
            changelog,
            "There has to be exactly one unreleased version",
        )
        for i in range(2):
            changelog.append(Version(i, None, datetime.now(), bool(i)))
        self._validate_fail(  # There has to be always one version unreleased
            keeper,
            changelog,
            "There has to be exactly one unreleased version",
        )
        changelog.release(UNRELEASED_VERSION_NAME + "1", "Fancy_version3.0", None)
        keeper._check(changelog)

    def _validate_fail(self, keeper_obj: ChangelogKeeper, invalid_changelog, match):
        with pytest.raises(ChangelogKeeperError, match=match):
            keeper_obj._check(invalid_changelog)
