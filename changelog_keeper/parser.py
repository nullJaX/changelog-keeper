"""
Changelog Parser - This file stores whole definition on how the file should be
structured and encoded/decoded.
"""
from datetime import datetime
from pathlib import Path
from re import compile, Match  # pylint: disable=redefined-builtin
from typing import List, Optional, Set, Tuple
from changelog_keeper.model import Changelog, ChangeType, ModelError, Version

OPEN_FILE_MODES = ("r", "w")
FILE_ENCODING = "utf-8"
ENDLINE_CHAR = "\n"

VERSION_HEADING_PREFIX = "## "
DATE_SEPARATOR = " - "
DATE_INTERNAL_SEPARATOR = DATE_SEPARATOR.strip()
DATE_FORMAT = f"%Y{DATE_INTERNAL_SEPARATOR}%m{DATE_INTERNAL_SEPARATOR}%d"
YANKED_TAG = "YANKED"
YANKED_SUFFIX = f"[{YANKED_TAG}]"
VERSION_REGEX = compile(
    rf"^{VERSION_HEADING_PREFIX}"
    r"\[(?P<name>(\S*))\]"
    r"(\((?P<ref>(\S*))\))?"
    rf"({DATE_SEPARATOR}"
    rf"(?P<date>(\d\d\d\d{DATE_INTERNAL_SEPARATOR}\d\d{DATE_INTERNAL_SEPARATOR}\d\d))"
    rf"( (\[(?P<yanked>({YANKED_TAG}))\]))?)?$"
)

CHANGE_TYPE_PREFIX = "### "

ENTRY_PREFIXES = ("- ", "  ")

UNRELEASED_ENTRY_PREFIX_FORMAT = "<{version}-{change_type}/>"
UNRELEASED_ENTRY_PREFIX_REGEX = compile(
    r"<(?P<version>(\S+))-(?P<change_type>(\S+))\/\>"
)


class ParserException(BaseException):
    """
    This exception indicates that the issue has been encountered during loading or
    saving a file.
    """


class ChangelogParser:
    """
    Parser class - All file encoding/decoding methods are stored in this class. It is
    not meant to be instantiated (though it can be).
    """

    ###################################################################################
    ### Main (public) functions
    ###################################################################################

    @classmethod
    def load(cls, path: Path) -> Changelog:
        """
        Loads a file specified by the path and returns a changelog instance.
        Loading is done in two phases:
        1. Parse the contents into objects
        2. Iterate through ALL entries, sort them in case some entries were
           misplaced (ie. by VCS during a merge or rebase) and remove prefixes for all
           items.
        If there are any invalid entries and cannot be sorted automatically,
        raises ParserException with a list of invalid lines to fix manually.
        """
        with open(path, OPEN_FILE_MODES[0], encoding=FILE_ENCODING) as file:
            lines = [line.replace(ENDLINE_CHAR, "") for line in file]

        changelog = Changelog()
        lines = cls._load_header(lines, changelog)
        lines = cls._load_versions(lines, changelog)
        changelog.rest = lines

        invalid_entries: Set[Tuple[str, ...]] = set()
        for version in changelog:
            invalid_entries.update(cls._organize_entries(version, changelog))

        if invalid_entries:
            joined_entries = [f"'{''.join(entry)}'" for entry in invalid_entries]
            joined_entries = ", ".join(joined_entries)
            raise ParserException(
                "Provided CHANGELOG is invalid and some conflicts "
                f"could not be fixed: {joined_entries}"
            )

        return changelog

    @classmethod
    def save(cls, changelog: Changelog, path: Path):
        """
        Saves Changelog object into a file specified by a path.
        Saving is done in two phases:
        1. For all unreleased versions' entries prefixes are added
        2. The contents are written into the file
        Prefixes are meant to solve the issue of entries being misplaced during casual
        repository operations.
        """
        for version in changelog:
            cls._prepare_entries(version)

        content = [cls._save_header(changelog)]
        content.extend(cls._save_versions(changelog))
        with open(path, OPEN_FILE_MODES[1], encoding=FILE_ENCODING) as file:
            file.write(ENDLINE_CHAR.join(content))
            file.write(ENDLINE_CHAR.join(changelog.rest))

    ###################################################################################
    ### Header
    ###################################################################################

    @classmethod
    def _load_header(cls, lines: List[str], changelog: Changelog) -> List[str]:
        for idx, line in enumerate(lines):
            if line.startswith(VERSION_HEADING_PREFIX):
                return lines[idx:]
            changelog.header.append(line)
        return []

    @classmethod
    def _save_header(cls, changelog: Changelog) -> str:
        return ENDLINE_CHAR.join(changelog.header)

    ###################################################################################
    ### Version
    ###################################################################################

    @classmethod
    def _load_versions(cls, lines: List[str], changelog: Changelog) -> List[str]:
        last_recognized_line = 0
        prefixes = (VERSION_HEADING_PREFIX, CHANGE_TYPE_PREFIX) + ENTRY_PREFIXES

        version: Optional[Version] = None
        change_type: Optional[ChangeType] = None

        for idx, line in enumerate(lines):
            if not (line and any(line.startswith(prefix) for prefix in prefixes)):
                continue
            last_recognized_line = idx
            if line.startswith(VERSION_HEADING_PREFIX):
                version: Version = cls._load_version_heading(line)
                changelog.append(version)
                continue
            if line.startswith(CHANGE_TYPE_PREFIX):
                change_type: ChangeType = cls._load_change_type(line)
                continue
            cls._load_entry(line, version, change_type)

        for version in changelog:
            for change_type in version.changes.keys():
                version.changes[change_type] = {
                    tuple(entry) for entry in version.changes[change_type]
                }
        return lines[last_recognized_line + 1 :]

    @classmethod
    def _save_versions(cls, changelog: Changelog) -> List[str]:
        sections = []
        for version in changelog:
            sections.append(cls._save_version_heading(version))
            sections.extend(cls._save_version_changes(version))
        return sections

    ###################################################################################
    ### Version Heading
    ###################################################################################

    @classmethod
    def _load_version_heading(cls, line: str) -> Version:
        match = VERSION_REGEX.fullmatch(line)
        if not match:
            raise ParserException(f"Cannot parse the version heading line: '{line}'")
        params = match.groupdict()
        name = params.get("name", None)
        if not name:
            raise ParserException(
                f"Cannot parse the version name in version heading line: '{line}'"
            )
        ref = params.get("ref", None)
        release_date = params.get("date", None)
        if release_date:
            release_date = datetime.strptime(release_date, DATE_FORMAT)
        is_yanked = bool(params.get("yanked", ""))
        return Version(name, ref, release_date, is_yanked)

    @classmethod
    def _save_version_heading(cls, version: Version) -> str:
        heading = f"{VERSION_HEADING_PREFIX}[{version.name}]"
        if version.ref:
            heading += f"({version.ref})"
        if version.release_date:
            heading += f"{DATE_SEPARATOR}{version.release_date.strftime(DATE_FORMAT)}"
            if version.is_yanked:
                heading += f" {YANKED_SUFFIX}"
        return heading + ENDLINE_CHAR

    ###################################################################################
    ### Version Changes
    ###################################################################################

    @classmethod
    def _load_change_type(cls, line: str) -> ChangeType:
        return ChangeType(line[len(CHANGE_TYPE_PREFIX) :].strip())

    @classmethod
    def _load_entry(cls, line: str, version: Version, change_type: ChangeType):
        first, continuation = (line.startswith(match) for match in ENTRY_PREFIXES)
        entries: List[List[str]] = version.changes.setdefault(change_type, [])
        if first or (continuation and not entries):
            entries.append([])
        if first or continuation:
            entries[-1].append(line[len(ENTRY_PREFIXES[int(continuation)]) :])

    @classmethod
    def _save_version_changes(cls, version: Version) -> List[str]:
        changes_list = []
        keys = sorted(version.changes.keys(), key=lambda x: x.value)
        for change_type in keys:
            changes = version.changes[change_type]
            if not changes:
                continue
            changes_list.extend(
                [f"{CHANGE_TYPE_PREFIX}{change_type.value}{ENDLINE_CHAR}", ""]
            )
            for change in sorted(changes):
                for line_no, change_line in enumerate(change):
                    prefix = ENTRY_PREFIXES[int(bool(line_no))]
                    changes_list[-1] += f"{prefix}{change_line}{ENDLINE_CHAR}"
        return changes_list

    ###################################################################################
    ### Organizing entries
    ###################################################################################

    @classmethod
    def _prepare_entries(cls, version: Version):
        if version.is_released:
            return
        for change_type in version.changes.keys():
            added_content = UNRELEASED_ENTRY_PREFIX_FORMAT.format(
                version=version.name, change_type=change_type.value
            )
            version.changes[change_type] = {
                tuple(added_content + line for line in change)
                for change in version.changes[change_type]
            }

    @classmethod
    def _organize_entries(
        cls, version: Version, changelog: Changelog
    ) -> Set[Tuple[str, ...]]:
        invalid_entries = set()
        for change_type in version.changes.copy().keys():
            changes = version.changes[change_type]
            to_be_removed: Set[Tuple[str, ...]] = set()

            for change in changes.copy():
                to_remove, invalid_entry = cls._process_change(change, changelog)
                if to_remove:
                    to_be_removed.add(to_remove)
                if invalid_entry:
                    invalid_entries.add(invalid_entry)
            changes.difference_update(to_be_removed)

            if not changes:
                del version.changes[change_type]
        return invalid_entries

    @classmethod
    def _process_change(
        cls, change: Tuple[str, ...], changelog: Changelog
    ) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
        invalid, found_versions, found_change_types = cls._find_matches(change)
        if invalid or len(found_versions) != 1 or len(found_change_types) != 1:
            return (
                (),
                change
                if invalid
                or len(found_versions) > 1
                or len(found_change_types) > 1
                or (found_versions and found_versions[0] not in changelog)
                else (),
            )

        try:
            version: Version = changelog[found_versions[0]]
            change_type = ChangeType(found_change_types[0])
        except (ModelError, ValueError):
            return (), change

        replacement_string = UNRELEASED_ENTRY_PREFIX_FORMAT.format(
            version=version.name, change_type=change_type.value
        )
        version.changes.setdefault(change_type, set()).add(
            tuple(line.replace(replacement_string, "") for line in change)
        )
        return change, ()

    @classmethod
    def _find_matches(
        cls, change: Tuple[str, ...]
    ) -> Tuple[bool, List[Optional[str]], List[Optional[str]]]:
        found: List[Optional[Match]] = [
            UNRELEASED_ENTRY_PREFIX_REGEX.match(line) for line in change
        ]
        if not all(found):
            return any(found), [], []
        found_versions, found_change_types = set(), set()
        for match in found:
            groups = match.groupdict()
            found_versions.add(groups.get("version"))
            found_change_types.add(groups.get("change_type"))
        return False, list(found_versions), list(found_change_types)
