from dataclasses import dataclass
from enum import Enum
from functools import cached_property


class ReturnCode(Enum):
    SUCCESS = 37  # %
    INVALID = 33  # !
    FAULT = 35  # #

    @cached_property
    def char(self) -> str:
        return chr(self.value)


@dataclass
class Version:
    major: str
    minor: str
    revision: str
    build: str

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.revision}.{self.build}"

    @classmethod
    def parse_string(cls, version_str) -> "Version":
        return Version(*version_str.split("."))


class DataItemEnum(Enum):
    @property
    def as_dataitem(self) -> str:
        return f"DATAITEM_{self.name}"


from .axes import SingleAxis, Axis, Stages, AxisError, AxisStatus, AxisStatusDataItem
from .tasks import TaskState, TaskStatusDataItem
