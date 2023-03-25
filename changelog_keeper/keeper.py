"""
Keeper Service Layer - This file stores main logic implementation.
"""
from typing import Tuple
from changelog_keeper.model import (
    Changelog,
    Config,
    Operation,
    Version,
    UNRELEASED_VERSION_NAME,
)
from changelog_keeper.parser import ChangelogParser, ENDLINE_CHAR


class ChangelogKeeperError(BaseException):
    """
    An exception indicating that the changelog content is logically invalid (ie. no
    unreleased version, multiple unreleased versions, unreleased version not being the
    first entry, etc.)
    """


class ChangelogKeeper:
    # pylint: disable=too-few-public-methods
    """
    Main service class, stores default header and executes all valid operations based
    on the value passed in the Config object.
    """

    DEFAULT_HEADER: Tuple[str, ...] = ["# Changelog", ""]

    def __init__(self, config: Config):
        self.config = config

    def run(self):
        """
        Executes the operation provided in the config.
        1a. If the operation is CREATE:
            - generates a new changelog object
        1b. Otherwise:
            - loads a file provided in the Config object
            - if the operation is not CHECK, performs a check
            - performs operation specified in the Config object
        2. Always overwrites the file with new content.
        """
        if self.config.operation == Operation.CREATE:
            changelog: Changelog = self._create()
        else:
            changelog: Changelog = ChangelogParser.load(self.config.file)
            if self.config.operation != Operation.CHECK:
                self._check(changelog)
            getattr(self, "_" + str(self.config.operation.value).lower())(changelog)
        ChangelogParser.save(changelog, self.config.file)

    def _create(self) -> Changelog:
        changelog: Changelog = Changelog()
        changelog.header = ChangelogKeeper.DEFAULT_HEADER
        changelog.append_top(Version(UNRELEASED_VERSION_NAME, None, None, False))
        return changelog

    def _check(self, changelog: Changelog):
        if UNRELEASED_VERSION_NAME not in changelog:
            raise ChangelogKeeperError(
                "There is no Unreleased version in the changelog"
            )
        if changelog[0].name != UNRELEASED_VERSION_NAME:
            raise ChangelogKeeperError(
                "Unreleased version is not a first version in the changelog"
            )
        release_states = {False: 0, True: 0}
        correct_state = {False: 1, True: len(changelog) - 1}
        for version in changelog:
            release_states[version.is_released] += 1
        if release_states != correct_state:
            raise ChangelogKeeperError("There has to be exactly one unreleased version")

    def _add(self, changelog: Changelog):
        changelog.add_entry(
            UNRELEASED_VERSION_NAME,
            self.config.change_type,
            tuple(self.config.entry.split(ENDLINE_CHAR)),
        )

    def _release(self, changelog: Changelog):
        changelog.release(
            UNRELEASED_VERSION_NAME, self.config.version, self.config.repo_ref
        )
        changelog.append_top(Version(UNRELEASED_VERSION_NAME, None, None, False))

    def _yank(self, changelog: Changelog):
        changelog.yank(self.config.version)
