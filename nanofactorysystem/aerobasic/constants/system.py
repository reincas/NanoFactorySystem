from enum import auto, Enum

from nanofactorysystem.aerobasic.constants import DataItemEnum
from nanofactorysystem.aerobasic.constants.tasks import TaskMode


class SystemStatusDataItem(DataItemEnum):
    DataCollectionSampleIndex = auto()
    DataCollectionSampleTime = auto()
    DataCollectionStatus = auto()
    EstimatedProcessorUsage = auto()
    FieldbusConnected = auto()
    FieldbusErrorCode = auto()
    FieldbusErrorLocation = auto()
    GlobalVariable = auto()
    PCModbusMasterConnected = auto()
    PCModbusMasterErrorCode = auto()
    PCModbusMasterErrorLocation = auto()
    PCModbusSlaveConnected = auto()
    PCModbusSlaveErrorCode = auto()
    PCModbusSlaveErrorLocation = auto()
    SafeZoneActiveMask = auto()
    SafeZoneViolationMask = auto()
    SystemParameter = auto()
    ThermoCompStatus = auto()
    Timer = auto()
    TimerPerformance = auto()
    VirtualBinaryInput = auto()
    VirtualBinaryOutput = auto()
    VirtualRegisterInput = auto()
    VirtualRegisterOutput = auto()
    ZYGOPosition1 = auto()
    ZYGOPosition2 = auto()
    ZYGOPosition3 = auto()
    ZYGOPosition4 = auto()


class WaitMode(Enum):
    AUTO = "AUTO"
    IN_POSITION = "INPOS"
    MOVE_DONE = "MOVEDONE"

    @classmethod
    def from_task_mode(cls, task_mode: TaskMode):
        if task_mode.WaitAuto:
            return WaitMode.AUTO
        if task_mode.WaitForInPos:
            return WaitMode.IN_POSITION
        return WaitMode.MOVE_DONE
