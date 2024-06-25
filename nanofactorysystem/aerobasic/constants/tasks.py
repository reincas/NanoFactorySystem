from dataclasses import dataclass
from enum import Enum, auto, Flag

from nanofactorysystem.aerobasic.constants import DataItemEnum


class TaskState(Enum):
    unavailable = 0
    inactive = 1
    idle = 2
    program_ready = 3
    program_running = 4
    programfeed_held = 5
    program_paused = 6
    program_complete = 7
    error = 8
    queue = 9


class TaskStatusDataItem(DataItemEnum):
    ActiveFixtureOffset = auto()
    CoordinateSystem1I = auto()
    CoordinateSystem1J = auto()
    CoordinateSystem1K = auto()
    CoordinateSystem1Plane = auto()
    CoordinatedAccelerationCommand = auto()
    CoordinatedAccelerationRate = auto()
    CoordinatedAccelerationTime = auto()
    CoordinatedDecelerationRate = auto()
    CoordinatedDecelerationTime = auto()
    CoordinatedPercentDone = auto()
    CoordinatedPositionCommand = auto()
    CoordinatedSpeedCommand = auto()
    CoordinatedSpeedTarget = auto()
    CoordinatedSpeedTargetActual = auto()
    CoordinatedTotalDistance = auto()
    CriticalSectionActive = auto()
    DependentCoordinatedSpeedTarget = auto()
    DependentCoordinatedSpeedTargetActual = auto()
    EnableAlignmentAxes = auto()
    ExecutionMode = auto()
    FiberPower = auto()
    FiberPowerSampleCount = auto()
    FiberSearchResult = auto()
    IFOVSpeedScale = auto()
    MFO = auto()
    MotionLineNumber = auto()
    ProgramLineNumber = auto()
    ProgramLineNumberInternal = auto()
    ProgramPersistent = auto()
    ProgramVariable = auto()
    QueueLineCapacity = auto()
    QueueLineCount = auto()
    QueueStatus = auto()
    Spindle0SpeedTarget = auto()
    Spindle1SpeedTarget = auto()
    Spindle2SpeedTarget = auto()
    Spindle3SpeedTarget = auto()
    TaskDoubleVariable = auto()
    TaskErrorCode = auto()
    TaskErrorLocation = auto()
    TaskExecutionLines = auto()
    TaskExecutionLinesMaximum = auto()
    TaskExecutionTime = auto()
    TaskExecutionTimeMaximum = auto()
    TaskInfoVariable = auto()
    TaskMode = auto()
    TaskParameter = auto()
    TaskReturnVariable = auto()
    TaskState = auto()
    TaskStateInternal = auto()
    TaskStatus0 = auto()
    TaskStatus1 = auto()
    TaskStatus2 = auto()
    TaskWarningCode = auto()
    TaskWarningLocation = auto()
    ToolNumberActive = auto()


class ProgrammingMode(Enum):
    ABSOLUTE = "ABSOLUTE"
    INCREMENTAL = "INCREMENTAL"


class VelocityMode(Enum):
    ON = "ON"
    OFF = "OFF"


class VelocityUnit(Enum):
    SECONDS = "SECONDS"
    MINUTES = "MINUTES"


class TaskMode(Flag):
    Secondary = 0x00000001
    Absolute = 0x00000002
    AccelTypeLinear = 0x00000004
    AccelModeRate = 0x00000008
    InverseDominance = 0x00000010
    MotionContinuous = 0x00000020
    InverseCircular = 0x00000040
    SpindleStopOnProgramHalt = 0x00000080
    BlockDelete = 0x00000100
    OptionalPause = 0x00000200
    AccelTypeScurve = 0x00000400
    MFOLock = 0x00000800
    MSOLock = 0x00001000
    DecelTypeLinear = 0x00002000
    DecelTypeScurve = 0x00004000
    AutoMode = 0x00008000
    ProgramFeedRateMPU = 0x00010000
    ProgramFeedRateUPR = 0x00020000
    BlockDelete2 = 0x00400000
    OverMode = 0x00800000
    DecelModeRate = 0x01000000
    MFOActiveOnJog = 0x04000000
    WaitForInPos = 0x08000000
    Minutes = 0x10000000
    WaitAuto = 0x40000000


class TaskStatus0(Flag):
    ProgramAssociated = 0x00000001
    ImmediateConcurrent = 0x00000004
    ImmediateExecuting = 0x00000008
    ReturnMotionExecuting = 0x00000010
    SingleStepInto = 0x00000040
    SingleStepOver = 0x00000080
    ProgramReset = 0x00000100
    PendingAxesStop = 0x00000200
    SoftwareESTOPActive = 0x00000400
    FeedHoldActive = 0x00000800
    CallbackHoldActive = 0x00001000
    CallbackResponding = 0x00002000
    SpindleActive0 = 0x00004000
    SpindleActive1 = 0x00008000
    SpindleActive2 = 0x00010000
    SpindleActive3 = 0x00020000
    ProbeCycle = 0x00040000
    Retrace = 0x00080000
    SoftHomeActive = 0x00100000
    InterruptMotionActive = 0x00200000
    JoystickActive = 0x00400000
    CornerRounding = 0x00800000
    JoystickLowSpeedActive = 0x02000000
    CannedFunctionExecuting = 0x08000000
    ProgramControlRestricted = 0x20000000


class TaskStatus1(Flag):
    MotionModeAbsOffsets = 0x00000001
    AsyncSMCMotionAbortPending = 0x00000002
    RetraceRequested = 0x00000008
    MSOChange = 0x00000010
    SpindleFeedHeld = 0x00000020
    FeedHeldAxesStopped = 0x00000040
    CutterRadiusEnabling = 0x00000080
    CutterRadiusDisabling = 0x00000100
    CutterOffsetsEnablingPos = 0x00000200
    CutterOffsetsEnablingNeg = 0x00000400
    CutterOffsetsDisabling = 0x00000800
    OnGosubPending = 0x00008000
    ProgramStopPending = 0x00010000
    CannedFunctionPending = 0x00020000
    NoMFOFloor = 0x00040000
    Interrupted = 0x00080000
    GalvoIFVDeactivationPending = 0x01000000
    IFOVBufferHold = 0x02000000


class TaskStatus2(Flag):
    RotationActive = 0x00000001
    RThetaPolarActive = 0x00000002
    RThetaCylindricalActive = 0x00000004
    ScalingActive = 0x00000008
    OffsetFixtureActive = 0x00000010
    ProfileActive = 0x00000020
    MotionModeRapid = 0x00000040
    MotionModeCoordinated = 0x00000080
    MotionPVT = 0x00000100
    MotionContinuousActive = 0x00000200
    MotionFiber = 0x00000800
    CutterOffsetsActivePos = 0x00001000
    CutterRadiusActiveLeft = 0x00002000
    CutterRadiusActiveRight = 0x00004000
    CutterOffsetsActiveNeg = 0x00008000
    NormalcyActiveLeft = 0x00010000
    NormalcyActiveRight = 0x00020000
    NormalcyAlignment = 0x00040000
    MotionModeCW = 0x00080000
    MotionModeCCW = 0x00100000
    LimitFeedRateActive = 0x00200000
    LimitMFOActive = 0x00400000
    Coord1Plane1 = 0x00800000
    Coord1Plane2 = 0x01000000
    Coord1Plane3 = 0x02000000
    Coord2Plane1 = 0x04000000
    Coord2Plane2 = 0x08000000
    Coord2Plane3 = 0x10000000
    MirrorActive = 0x40000000


@dataclass
class TaskStatus:
    task_status_0: TaskStatus0
    task_status_1: TaskStatus1
    task_status_2: TaskStatus2

    @classmethod
    def from_strings(cls, task_status_0_str: str, task_status_1_str: str, task_status_2_str: str):
        return TaskStatus(
            task_status_0=TaskStatus0(int(task_status_0_str)),
            task_status_1=TaskStatus1(int(task_status_1_str)),
            task_status_2=TaskStatus2(int(task_status_2_str)),
        )
