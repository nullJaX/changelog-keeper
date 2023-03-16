from datetime import datetime
import pytest
from changelog_keeper.model import (
    Changelog,
    ChangeType,
    ModelError,
    Operation,
    UNRELEASED_VERSION_NAME,
    Version,
    VersionPhase,
    VersionState,
)

STRING_FUNCTIONS = ("capitalize", "lower", "upper", "strip")


class TestChangeType:
    @pytest.mark.parametrize("value", list(ChangeType))
    @pytest.mark.parametrize("function", STRING_FUNCTIONS)
    def test_valid(self, value: ChangeType, function: str):
        str_value = value.value
        str_value = getattr(str_value, function)()
        assert value == ChangeType(str_value)

    @pytest.mark.parametrize("value", list(ChangeType))
    @pytest.mark.parametrize("function", STRING_FUNCTIONS)
    def test_invalid(self, value: ChangeType, function: str):
        str_value = value.value
        str_value = getattr(str_value, function)()[:4]
        with pytest.raises(ValueError):
            ChangeType(str_value)


class TestVersionPhase:
    def test_boolean_value(self):
        assert not bool(VersionPhase.UNRELEASED)
        assert bool(VersionPhase.RELEASED)
        assert bool(VersionPhase.YANKED)


class TestVersionState:
    @pytest.mark.parametrize("name", (None, "some.version.name"))
    @pytest.mark.parametrize("ref", (None, "example.ref"))
    @pytest.mark.parametrize(
        "release_date,is_yanked,phase,should_fail",
        (
            (None, False, VersionPhase.UNRELEASED, False),
            (None, True, VersionPhase.YANKED, True),
            (datetime.now(), False, VersionPhase.RELEASED, False),
            (datetime.now(), True, VersionPhase.YANKED, False),
        ),
    )
    def test_init(self, name, ref, release_date, is_yanked, phase, should_fail):
        if should_fail:
            with pytest.raises(ModelError, match="Unreleased version cannot be yanked"):
                VersionState(name, ref, release_date, is_yanked)
            return

        state = VersionState(name, ref, release_date, is_yanked)
        assert state.name == name
        assert state.ref == ref
        assert state.release_date == release_date
        assert state.phase == phase

    @pytest.mark.parametrize("old_ref", (None, "old_ref"))
    @pytest.mark.parametrize("new_ref", (None, "new_ref"))
    @pytest.mark.parametrize(
        "release_date,is_yanked,should_fail",
        (
            (None, False, False),
            (datetime.now(), False, True),
            (datetime.now(), True, True),
        ),
    )
    def test_release(self, old_ref, release_date, is_yanked, new_ref, should_fail):
        new_version = "version.name"
        state = VersionState("old.name", old_ref, release_date, is_yanked)
        if should_fail:
            with pytest.raises(
                ModelError, match="Released or yanked version cannot be released"
            ):
                state._release("version.name", "version.ref")
            return

        state._release(new_version, new_ref)
        assert state.name == new_version
        assert state.ref == new_ref
        assert state.phase == VersionPhase.RELEASED
        assert state.release_date.date() == datetime.now().date()

    @pytest.mark.parametrize(
        "release_date,is_yanked,should_fail",
        (
            (None, False, True),
            (datetime.now(), False, False),
            (datetime.now(), True, False),
        ),
    )
    def test_yank(self, release_date, is_yanked, should_fail):
        state = VersionState("some_version", None, release_date, is_yanked)
        if should_fail:
            with pytest.raises(ModelError, match="Unreleased version cannot be yanked"):
                state._yank()
            return

        state._yank()
        assert state.phase == VersionPhase.YANKED


class TestVersion:
    def test_init_and_state(self):
        version = Version("name", None, None, False)
        assert not version.changes
        assert version.ref is None
        version.ref = "some_ref"
        assert version.ref == "some_ref"
        assert version.release_date is None
        assert not version.is_released
        assert not version.is_yanked
        version._release("new_name", "new_ref")
        assert version.name == "new_name"
        assert version.ref == "new_ref"
        assert (
            isinstance(version.release_date, datetime)
            and version.release_date.date() == datetime.now().date()
        )
        assert version.is_released
        assert not version.is_yanked
        version._yank()
        assert version.is_released
        assert version.is_yanked

    @pytest.mark.parametrize("change_type", list(ChangeType))
    @pytest.mark.parametrize(
        "release_date,is_yanked,should_fail",
        (
            (None, False, False),
            (datetime.now(), False, True),
            (datetime.now(), True, True),
        ),
    )
    def test_add_entry(self, change_type, release_date, is_yanked, should_fail):
        expected_changes = {change_type: {("Some multiline", "entry")}}
        version = Version("some.version", None, release_date, is_yanked)
        if should_fail:
            with pytest.raises(
                ModelError, match="Cannot modify changes for released or yanked version"
            ):
                for change, entries in expected_changes.items():
                    for entry in entries:
                        version._add_entry(change, entry)
            return

        for change, entries in expected_changes.items():
            for entry in entries:
                version._add_entry(change, entry)
        assert version.changes == expected_changes


class TestChangelog:
    @pytest.mark.parametrize("index", (UNRELEASED_VERSION_NAME, 9))
    @pytest.mark.parametrize(
        "function,args",
        (
            ("add_entry", [ChangeType.CHANGED, "Some entry"]),
            ("release", ["release_name", None]),
            ("yank", []),
        ),
    )
    def test_init(self, index, function, args):
        changelog = Changelog()
        assert index not in changelog
        assert not changelog
        assert len(changelog) == 0
        arguments = [index] + args
        with pytest.raises(ModelError, match="Version is not present in the changelog"):
            getattr(changelog, function)(*arguments)

        changelog.append_top(Version(str(index), None, None, False))
        assert str(index) in changelog
        assert changelog
        assert len(changelog) == 1
        assert changelog[str(index)] == changelog[0]

    @pytest.mark.parametrize("function", ("append", "append_top"))
    @pytest.mark.parametrize(
        "existing_name,existing_ref,name,ref,error_msg",
        (
            (
                UNRELEASED_VERSION_NAME,
                None,
                UNRELEASED_VERSION_NAME,
                None,
                "Version already exists in changelog",
            ),
            (
                UNRELEASED_VERSION_NAME,
                "some_ref1",
                "new_version",
                "some_ref1",
                "Version link already exists in changelog",
            ),
        ),
    )
    def test_append_already_existing(
        self, function, existing_name, existing_ref, name, ref, error_msg
    ):
        changelog = Changelog()
        getattr(changelog, function)(Version(existing_name, existing_ref, None, False))
        with pytest.raises(ModelError, match=error_msg):
            getattr(changelog, function)(Version(name, ref, None, False))

    @pytest.mark.parametrize(
        "existing_name,existing_ref,name,ref,error_msg",
        (
            (
                "0.0.1",
                None,
                "0.0.1",
                None,
                "Version already exists in changelog",
            ),
            (
                "0.0.1",
                "some_ref1",
                "new_version",
                "some_ref1",
                "Version link already exists in changelog",
            ),
        ),
    )
    def test_release_already_existing(
        self, existing_name, existing_ref, name, ref, error_msg
    ):
        changelog = Changelog()
        changelog.append(Version(UNRELEASED_VERSION_NAME, None, None, False))
        changelog.release(UNRELEASED_VERSION_NAME, existing_name, existing_ref)
        changelog.append_top(Version(UNRELEASED_VERSION_NAME, None, None, False))
        with pytest.raises(ModelError, match=error_msg):
            changelog.release(UNRELEASED_VERSION_NAME, name, ref)

    def test_release(self):
        changelog = Changelog()
        changelog.append(
            Version(
                UNRELEASED_VERSION_NAME,
                "https://github.com/me/my-project/releases/tag/HEAD",
                None,
                False,
            )
        )
        assert UNRELEASED_VERSION_NAME in changelog
        assert "https://github.com/me/my-project/releases/tag/HEAD" in changelog
        changelog.release(
            UNRELEASED_VERSION_NAME,
            "1.0.0",
            "https://github.com/me/my-project/releases/tag/v1.0.0",
        )
        assert UNRELEASED_VERSION_NAME not in changelog
        assert "1.0.0" in changelog
        assert "https://github.com/me/my-project/releases/tag/HEAD" not in changelog
        assert "https://github.com/me/my-project/releases/tag/v1.0.0" in changelog


class TestOperation:
    @pytest.mark.parametrize("value", list(Operation))
    @pytest.mark.parametrize("function", STRING_FUNCTIONS)
    def test_valid(self, value: Operation, function: str):
        str_value = value.value
        str_value = getattr(str_value, function)()
        assert value == Operation(str_value)

    @pytest.mark.parametrize("value", list(Operation))
    @pytest.mark.parametrize("function", STRING_FUNCTIONS)
    def test_invalid(self, value: Operation, function: str):
        str_value = value.value
        str_value = getattr(str_value, function)()[:2]
        with pytest.raises(ValueError):
            Operation(str_value)
