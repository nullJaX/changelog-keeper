from pathlib import Path
import pytest
from typing import List
from changelog_keeper.cli import ChangeType, cli, Config, ENTRYPOINT_COMMAND, Operation

PROG = [ENTRYPOINT_COMMAND]
SOME_FILE = Path("CHANGES.MD")


def _validate_cli_result(config: Config, arguments: List[str], file):
    if file:
        config.file = file
        arguments.extend(["--file", str(file)])
    assert config == cli(PROG + [config.operation.value] + arguments)


@pytest.mark.parametrize("file", (None, SOME_FILE))
def test_cli_create(file):
    config = Config(
        operation=Operation.CREATE,
        change_type=None,
        entry=None,
        version=None,
        repo_ref=None,
    )
    _validate_cli_result(config, [], file)


@pytest.mark.parametrize("change_type", list(ChangeType))
@pytest.mark.parametrize("file", (None, SOME_FILE))
def test_cli_add(change_type, file):
    example_entry = "Some new entry"
    config = Config(
        operation=Operation.ADD,
        change_type=change_type,
        entry=example_entry,
        version=None,
        repo_ref=None,
    )
    arguments = [change_type.value, example_entry]
    _validate_cli_result(config, arguments, file)


@pytest.mark.parametrize("file", (None, SOME_FILE))
def test_cli_check(file):
    config = Config(
        operation=Operation.CHECK,
        change_type=None,
        entry=None,
        version=None,
        repo_ref=None,
    )
    _validate_cli_result(config, [], file)


@pytest.mark.parametrize("file", (None, SOME_FILE))
def test_cli_release_with_reference(file):
    example_version = "1.2.3"
    example_version_ref = "v1.2.3"
    config = Config(
        operation=Operation.RELEASE,
        change_type=None,
        entry=None,
        version=example_version,
        repo_ref=example_version_ref,
    )
    _validate_cli_result(config, [example_version, "-r", example_version_ref], file)


@pytest.mark.parametrize(
    "operation",
    (Operation.RELEASE, Operation.YANK),
)
@pytest.mark.parametrize("file", (None, SOME_FILE))
def test_cli_release_and_yank(operation, file):
    example_version = "1.2.3"
    config = Config(
        operation=operation,
        change_type=None,
        entry=None,
        version=example_version,
        repo_ref=None,
    )
    _validate_cli_result(config, [example_version], file)
