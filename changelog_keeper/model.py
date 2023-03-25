"""
Changelog Keeper Model - stores all model classes used in the entire application.
"""
from collections import deque
from datetime import datetime
from dataclasses import dataclass
from enum import Enum, IntEnum
from pathlib import Path
from typing import Deque, Dict, Optional, Set, Tuple, Union, List

#######################################################################################
### Constants & utilities
#######################################################################################

DEFAULT_CHANGELOG_PATH = Path("./CHANGELOG.md")
UNRELEASED_VERSION_NAME = "Unreleased"


def missing_enum(cls, value, func):
    """
    Helper function for resolving missing item for enums.
    Applies an arbitrary function and checks whether a changed value is a member of an
    enum.
    """
    value = func(value)
    for member in cls:
        if member.value == value:
            return member
    return None


class ModelError(BaseException):
    """This exception is raised when the model constraints have been violated."""


#######################################################################################
### Changelog Model
#######################################################################################


class ChangeType(Enum):
    """All change types that are valid for an entry in the changelog"""

    ADDED = "Added"
    CHANGED = "Changed"
    DEPRECATED = "Deprecated"
    FIXED = "Fixed"
    REMOVED = "Removed"
    SECURITY = "Security"

    @classmethod
    def _missing_(cls, value: str):
        return missing_enum(cls, value, lambda x: x.capitalize())


class VersionPhase(IntEnum):
    """
    Indicates the phase of the version. Allowed transitions:
    UNRELEASED ---> RELEASED
    RELEASED   ---> YANKED
    """

    UNRELEASED = 0
    RELEASED = 1
    YANKED = 2


class VersionState:
    # pylint: disable=missing-function-docstring
    """
    State of a version. The object of this class handles and validates all operations
    that can be performed on a version instance.
    """

    _name: str

    @property
    def name(self) -> str:
        return self._name

    _reference: Optional[str]

    @property
    def ref(self) -> Optional[str]:
        return self._reference

    _release_date: Optional[datetime]

    @property
    def release_date(self) -> Optional[datetime]:
        return self._release_date

    _phase: VersionPhase

    @property
    def phase(self) -> VersionPhase:
        return self._phase

    def __init__(
        self,
        name: str,
        reference: Optional[str],
        release_date: Optional[datetime],
        is_yanked: bool,
    ):
        self._name = name
        self._phase = VersionPhase(bool(release_date is not None))
        if is_yanked:
            self._validate_unreleased()
            self._phase = VersionPhase.YANKED
        self._reference = reference
        self._release_date = release_date

    def __eq__(self, __o: object) -> bool:
        return (
            isinstance(__o, VersionState)
            and (self.name == __o.name)
            and (self.ref == __o.ref)
            and (self.phase == __o.phase)
            and (
                (self.release_date.date() if self.release_date else None)
                == (__o.release_date.date() if __o.release_date else None)
            )  # Only consider the date part when comparing
        )

    def _release(self, version: str, ref_name: Optional[str]):
        if bool(self._phase):
            raise ModelError(
                f"Released or yanked version cannot be released: {self._name}"
            )
        self._name = version
        self._reference = ref_name
        self._release_date = datetime.now()
        self._phase = VersionPhase.RELEASED

    def _yank(self):
        self._validate_unreleased()
        self._phase = VersionPhase.YANKED

    def _validate_unreleased(self):
        if not bool(self._phase):
            raise ModelError(f"Unreleased version cannot be yanked: {self._name}")


class Version:
    # pylint: disable=protected-access,missing-function-docstring
    """Changelog version representation"""
    _state: VersionState

    @property
    def name(self) -> str:
        return self._state.name

    @property
    def ref(self) -> Optional[str]:
        return self._state.ref

    @ref.setter
    def ref(self, reference: Optional[str]):
        self._state._reference = reference

    @property
    def release_date(self) -> Optional[datetime]:
        return self._state.release_date

    @property
    def is_released(self) -> bool:
        return bool(self._state.phase)

    @property
    def is_yanked(self) -> bool:
        return bool(self._state.phase == VersionPhase.YANKED)

    _changes: Dict[ChangeType, Set[Tuple[str, ...]]]

    @property
    def changes(self) -> Dict[ChangeType, Set[Tuple[str, ...]]]:
        return self._changes

    def __init__(
        self,
        name: str,
        reference: Optional[str],
        release_date: Optional[datetime],
        is_yanked: bool,
    ):
        self._state = VersionState(name, reference, release_date, is_yanked)
        self._changes = {}

    def __eq__(self, __o: object) -> bool:
        return (
            isinstance(__o, Version)
            and self._state == __o._state
            and self._changes == __o._changes
        )

    def _add_entry(self, change_type: ChangeType, entry: Tuple[str, ...]):
        if self.is_released:
            raise ModelError(
                "Cannot modify changes for released or yanked version: "
                f"{self._state.name}"
            )
        self._changes.setdefault(change_type, set()).add(entry)

    def _release(self, version: str, ref_name: Optional[str]):
        self._state._release(version, ref_name)

    def _yank(self):
        self._state._yank()


class Changelog:
    # pylint: disable=protected-access,missing-function-docstring
    """Changelog representation"""
    header: List[str]

    _versions: Deque[Version]

    @property
    def versions(self) -> Tuple[Version]:
        return tuple(self._versions)

    _names: Dict[str, Version]

    _refs: Dict[str, Version]

    rest: List[str]

    def __init__(self):
        super().__init__()
        self.header = []
        self._versions = deque()
        self._names = {}
        self._refs = {}
        self.rest = []

    def __contains__(self, name: str) -> bool:
        return name in self._names or name in self._refs

    def __len__(self) -> int:
        return len(self._versions)

    def __iter__(self):
        return iter(self.versions)

    def __bool__(self):
        return bool(self._versions)

    def __getitem__(self, index: Union[str, int]):
        try:
            if isinstance(index, int):
                return self._versions[index]
            version = self._names.get(index)
            return version if version else self._refs[index]
        except (IndexError, KeyError) as exc:
            raise ModelError(
                f"Version is not present in the changelog: {index}"
            ) from exc

    def __eq__(self, __o: object) -> bool:
        return (
            isinstance(__o, Changelog)
            and self.header == __o.header
            and self.versions == __o.versions
            and self.rest == __o.rest
        )

    def append_top(self, version: Version):
        return self.append(version, top=True)

    def append(self, version: Version, top: bool = False):
        name, reference = version.name, version.ref
        self._validate_missing(name, reference)
        getattr(self._versions, "appendleft" if top else "append")(version)
        if reference:
            self._refs[reference] = version
        self._names[name] = version

    def add_entry(self, index: Union[str, int], change_type: ChangeType, entry: str):
        self[index]._add_entry(change_type, entry)

    def release(
        self, index: Union[str, int], release_name: str, reference: Optional[str]
    ):
        self._validate_missing(release_name, reference)
        version = self[index]
        old_name = version.name
        old_ref = version.ref
        version._release(release_name, reference)
        if old_ref in self._refs:
            del self._refs[old_ref]
        if reference:
            self._refs[reference] = version
        self._names[release_name] = version
        del self._names[old_name]

    def yank(self, index: Union[str, int]):
        self[index]._yank()

    def _validate_missing(self, name: str, ref: Optional[str]):
        if name in self._names:
            raise ModelError(f"Version already exists in changelog: {name}")
        if ref in self._refs:
            raise ModelError(f"Version link already exists in changelog: {ref}")


#######################################################################################
### CLI arguments DTO
#######################################################################################


class Operation(Enum):
    """Allowed operations that can be executed against a changelog."""

    CREATE = "create"
    ADD = "add"
    CHECK = "check"
    RELEASE = "release"
    YANK = "yank"

    @classmethod
    def _missing_(cls, value: str):
        return missing_enum(cls, value, lambda x: x.lower())


@dataclass
class Config:
    """
    Stores all arguments (passed from CLI) needed to perform any action on the
    changelog.
    """

    operation: Operation

    # add
    change_type: Optional[ChangeType]
    entry: Optional[str]

    # release & yank
    version: Optional[str]

    # release
    repo_ref: Optional[str]

    # default, for all subcommands
    file: Path = DEFAULT_CHANGELOG_PATH
