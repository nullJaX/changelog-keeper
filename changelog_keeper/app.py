"""
Changelog Keeper Application Layer - main entrypoint
"""
import sys
from typing import List
from changelog_keeper.cli import cli
from changelog_keeper.keeper import ChangelogKeeper, ChangelogKeeperError
from changelog_keeper.model import Config, ModelError
from changelog_keeper.parser import ParserException


class App:
    # pylint: disable=too-few-public-methods
    """
    Main App instance. Responsible for:
    - executing CLI routine
    - executing underlying service layer
    - catching all application errors
    - assigning the exit code based on the caught exception
    """

    ERROR_MSG = "ERROR: {0!s}"
    ERROR_CODES = {
        ModelError: 3,
        ParserException: 4,
        ChangelogKeeperError: 5,
    }

    def __init__(self, arguments: List[str]):
        self.config: Config = cli(arguments)

    def run(self) -> int:
        """
        Main run method:
        - runs a Service
        - catches any exception raised, prints its message and returns an exit code
        """
        exit_code = 0
        try:
            keeper: ChangelogKeeper = ChangelogKeeper(self.config)
            keeper.run()
        except BaseException as exc:  # pylint: disable=broad-exception-caught
            print(App.ERROR_MSG.format(exc))
            exit_code = App.ERROR_CODES.get(type(exc), 1)
        return exit_code


def main_cli():  # pragma: no cover
    # pylint: disable=missing-function-docstring
    sys.exit(App(sys.argv).run())


if __name__ == "__main__":  # pragma: no cover
    main_cli()
