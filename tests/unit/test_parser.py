from copy import deepcopy
from datetime import datetime
import pytest
from changelog_keeper.parser import (
    Changelog,
    ChangelogParser,
    ChangeType,
    ENDLINE_CHAR,
    ParserException,
    UNRELEASED_ENTRY_PREFIX_FORMAT,
    Version,
)


class TestChangelogParser:
    def test_header(self):
        example_header = ["# Changelog", "Some header content"]
        changelog = Changelog()
        output_changelog_1 = deepcopy(changelog)
        output_changelog_2 = deepcopy(changelog)

        changelog.header = example_header
        dumped = ChangelogParser._save_header(changelog)
        rest = ChangelogParser._load_header(
            dumped.split(ENDLINE_CHAR), output_changelog_1
        )
        assert not rest
        assert changelog.header == output_changelog_1.header

        example_header = example_header + ["## [Unreleased](HEAD)"]
        rest = ChangelogParser._load_header(example_header, output_changelog_2)
        assert rest == example_header[-1:]
        assert output_changelog_2.header == changelog.header

    @pytest.mark.parametrize("name", ("Unreleased", "1.0.0"))
    @pytest.mark.parametrize("ref", (None, "v1.0.0"))
    @pytest.mark.parametrize(
        "release_date,is_yanked",
        (
            (None, False),
            (datetime.now(), False),
            (datetime.now(), True),
        ),
    )
    def test_version_heading_success(self, name, ref, release_date, is_yanked):
        version = Version(name, ref, release_date, is_yanked)
        dumped = ChangelogParser._save_version_heading(version)
        dumped = dumped.replace(ENDLINE_CHAR, "")
        parsed_version = ChangelogParser._load_version_heading(dumped)
        assert version == parsed_version

    @pytest.mark.parametrize(
        "line,match",
        (
            ("Some random line", "Cannot parse the version heading line"),
            ("## []()", "Cannot parse the version name in version heading line"),
        ),
    )
    def test_version_heading_failed(self, line, match):
        with pytest.raises(ParserException, match=match):
            ChangelogParser._load_version_heading(line)

    @pytest.mark.parametrize("change_type", list(ChangeType))
    @pytest.mark.parametrize("entries", (set(), {("Single line",), ("Multi", "line")}))
    def test_version_changes(self, change_type, entries):
        version = Version("Unreleased", None, None, False)
        output_version = deepcopy(version)
        version.changes[change_type] = entries

        dumped = ChangelogParser._save_version_changes(version)
        reloaded = []
        for section in dumped:
            reloaded.extend(section.split(ENDLINE_CHAR))

        if entries:
            parsed_change_type = ChangelogParser._load_change_type(reloaded[0])
        for line in reloaded[1:]:
            if not line:
                continue
            ChangelogParser._load_entry(line, output_version, parsed_change_type)
        output_version._changes = {
            k: {tuple(entry) for entry in v}
            for k, v in output_version.changes.items()
            if v
        }
        version._changes = {k: v for k, v in version.changes.items() if v}

        assert version == output_version

    @pytest.mark.parametrize(
        "ref", (None, "https://github.com/me/my-project/releases/tag/v1.0.0")
    )
    @pytest.mark.parametrize(
        "release_date,is_yanked",
        ((None, False), (datetime.now(), False), (datetime.now(), True)),
    )
    @pytest.mark.parametrize("change_type", list(ChangeType) + [None])
    @pytest.mark.parametrize(
        "entry",
        (
            ("Single line entry",),
            ("Multiline", "entry"),
        ),
    )
    def test_versions(self, ref, release_date, is_yanked, change_type, entry):
        name = "SOME_VERSION"
        input_changelog = Changelog()
        output_changelog = deepcopy(input_changelog)

        version = Version(name, ref, release_date, is_yanked)
        if change_type:
            version.changes.setdefault(change_type, {entry})
        input_changelog.append(version)

        dumped = ChangelogParser._save_versions(input_changelog)
        reloaded = []
        for section in dumped:
            reloaded.extend(section.split(ENDLINE_CHAR))

        assert [""] == ChangelogParser._load_versions(reloaded, output_changelog)
        assert input_changelog == output_changelog

    @pytest.mark.parametrize("change_type", list(ChangeType))
    def test_find_matches(self, change_type):
        VERSION = "UNRELEASED"
        prefix = UNRELEASED_ENTRY_PREFIX_FORMAT.format(
            version=VERSION, change_type=change_type.value
        )

        single_line = ("Single line entry",)
        multi_line = ("Multi line", "entry")
        assert (False, [], []) == ChangelogParser._find_matches(single_line)
        assert (False, [], []) == ChangelogParser._find_matches(multi_line)

        single_line = (prefix + single_line[0],)
        assert (False, [VERSION], [change_type.value]) == ChangelogParser._find_matches(
            single_line
        )

        multi_line_only_first = (prefix + multi_line[0], multi_line[1])
        assert (True, [], []) == ChangelogParser._find_matches(multi_line_only_first)

        multi_line_only_second = (multi_line[0], prefix + multi_line[1])
        assert (True, [], []) == ChangelogParser._find_matches(multi_line_only_second)

        multi_line = (prefix + multi_line[0], prefix + multi_line[1])
        assert (False, [VERSION], [change_type.value]) == ChangelogParser._find_matches(
            multi_line
        )

    @pytest.mark.parametrize(
        "release_date,is_yanked",
        ((None, False), (datetime.now(), False), (datetime.now(), True)),
    )
    @pytest.mark.parametrize("change_type", list(ChangeType))
    @pytest.mark.parametrize(
        "entry",
        (
            ("Single line entry",),
            ("Multiline", "entry"),
        ),
    )
    def test_prepare_entries(self, release_date, is_yanked, change_type, entry):
        version = Version("1.2.3", None, release_date, is_yanked)
        version.changes.setdefault(change_type, {entry})
        prefix = (
            ""
            if version.is_released
            else UNRELEASED_ENTRY_PREFIX_FORMAT.format(
                version=version.name, change_type=change_type.value
            )
        )
        expected_changes = {
            k: {tuple(prefix + line for line in entry) for entry in v}
            for k, v in version.changes.items()
        }

        output_version = deepcopy(version)

        ChangelogParser._prepare_entries(output_version)
        assert expected_changes == output_version.changes
