"""
Changelog Keeper CLI - converts CLI arguments into Config object.
"""
from argparse import ArgumentParser
from pathlib import Path
from sys import exit  # pylint: disable=redefined-builtin
from typing import List
from changelog_keeper.model import ChangeType, DEFAULT_CHANGELOG_PATH, Config, Operation

#######################################################################################
### Constants
#######################################################################################

ENTRYPOINT_COMMAND = "clkpr"
DESCRIPTION = "Command line utility for keeping your changelog tidy"
SUBPARSERS_META = {"title": "operations", "dest": "operation"}
VERSION_ARGUMENT = (
    ("version",),
    {"action": "store", "type": str, "metavar": "VERSION"},
)
FILE_ARGUMENT = (
    ("-f", "--file"),
    {
        "dest": "file",
        "action": "store",
        "default": DEFAULT_CHANGELOG_PATH,
        "type": Path,
        "required": False,
        "metavar": "PATH",
        "help": (
            "path to CHANGELOG file that will be read/written during the operation. "
            f"Default: {str(DEFAULT_CHANGELOG_PATH)}"
        ),
    },
)

#######################################################################################
### Subcommands (considered to be 'private')
#######################################################################################


def _cli_create(subparsers):
    help_msg = "Generates new CHANGELOG file"
    return subparsers.add_parser("create", help=help_msg, description=help_msg)


def _cli_add(subparsers):
    help_msg = "Adds new entry to CHANGELOG file"
    add = subparsers.add_parser("add", help=help_msg, description=help_msg)
    add.add_argument(
        "change_type",
        action="store",
        type=ChangeType,
        metavar="CHANGE_TYPE",
        help=(
            "case insensitive. Type of change and section to be used in the "
            "changelog. Supported values: "
            f"{', '.join([str(ct.value).lower() for ct in list(ChangeType)])}"
        ),
    )
    add.add_argument(
        "entry",
        action="store",
        type=str,
        metavar="ENTRY",
        help="message to be inserted into CHANGELOG file",
    )
    return add


def _cli_check(subparsers):
    help_msg = "Validates CHANGELOG file"
    return subparsers.add_parser("check", help=help_msg, description=help_msg)


def _cli_release(subparsers):
    help_msg = "Releases a version within CHANGELOG file"
    version_kwargs = {
        "help": (
            "version name to be released. This value must not be present in the "
            "changelog versions."
        )
    }
    version_kwargs.update(VERSION_ARGUMENT[1])
    release = subparsers.add_parser("release", help=help_msg, description=help_msg)
    release.add_argument(*VERSION_ARGUMENT[0], **version_kwargs)
    release.add_argument(
        "-r",
        "--ref",
        "--reference",
        action="store",
        default=None,
        type=str,
        required=False,
        metavar="REFNAME",
        dest="repo_ref",
        help="reference URL in the repository. If provided, makes a version heading in"
        " the changelog to behave like a link.",
    )
    return release


def _cli_yank(subparsers):
    help_msg = "Yanks already released version within CHANGELOG file"
    version_kwargs = {
        "help": (
            "version name to be yanked. This value has to exist in the changelog "
            "versions."
        )
    }
    version_kwargs.update(VERSION_ARGUMENT[1])
    yank = subparsers.add_parser("yank", help=help_msg, description=help_msg)
    yank.add_argument(*VERSION_ARGUMENT[0], **version_kwargs)
    return yank


#######################################################################################
### Main CLI function
#######################################################################################


def cli(arguments: List[str]) -> Config:
    """
    Converts CLI arguments into Config object.
    """
    sub_cmds = (_cli_create, _cli_add, _cli_check, _cli_release, _cli_yank)
    parser = ArgumentParser(ENTRYPOINT_COMMAND, description=DESCRIPTION, add_help=True)
    parser.add_argument(*FILE_ARGUMENT[0], **FILE_ARGUMENT[1])
    subparsers = parser.add_subparsers(**SUBPARSERS_META)
    for subcommand in sub_cmds:
        subcommand(subparsers).add_argument(*FILE_ARGUMENT[0], **FILE_ARGUMENT[1])

    args = parser.parse_args(arguments[1:])
    if not args.operation:  # pragma: no cover
        parser.print_help()
        exit(2)
    return Config(
        operation=Operation(args.operation),
        change_type=getattr(args, "change_type", None),
        entry=getattr(args, "entry", None),
        version=getattr(args, "version", None),
        repo_ref=getattr(args, "repo_ref", None),
        file=args.file,
    )
