from copy import deepcopy
from datetime import datetime
from pathlib import Path
import pytest
from changelog_keeper.parser import (
    Changelog,
    ChangelogParser,
    ChangeType,
    ParserException,
    Version,
)

FILES_DIR = Path(__file__).parent / "files"
CHANGELOG_FILE = FILES_DIR / "MOCKED_CHANGELOG.md"
SHUFFLED_CHANGELOG = FILES_DIR / "SHUFFLED_CHANGELOG.md"


class TestChangelogParser:
    @pytest.fixture
    def changelog(self) -> Changelog:
        changelog = Changelog()
        changelog.header = ["# Changelog", "something"]
        changelog.rest = ["", "END"]
        for idx, change_type in enumerate(list(ChangeType)):
            version = Version(
                str(idx),
                str(idx) if idx % 2 else None,
                datetime(2023, 3, 16) if idx % 3 else None,
                idx % 3 == 2,
            )
            version.changes.setdefault(
                change_type, {("Single line entry",), ("Multi line", "entry")}
            )
            changelog.append(version)
        changelog.append_top(Version("Random", None, None, False))
        return changelog

    def test_save_and_load(self, changelog: Changelog):
        try:
            ChangelogParser.save(deepcopy(changelog), CHANGELOG_FILE)
            output_changelog = ChangelogParser.load(CHANGELOG_FILE)
            assert output_changelog == changelog
        finally:
            if CHANGELOG_FILE.exists():
                CHANGELOG_FILE.unlink()

    def test_load_shuffled(self, changelog: Changelog):
        parsed = ChangelogParser.load(SHUFFLED_CHANGELOG)
        assert changelog == parsed

    @pytest.mark.parametrize("file_idx", list(range(5)))
    def test_load_invalid(self, file_idx):
        with pytest.raises(
            ParserException,
            match="Provided CHANGELOG is invalid and "
            "some conflicts could not be fixed",
        ):
            ChangelogParser.load(FILES_DIR / f"INVALID_CHANGELOG_{file_idx}.md")
