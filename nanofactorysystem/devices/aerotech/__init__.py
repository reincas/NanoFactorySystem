import datetime
import hashlib
import random
import time
from functools import cached_property
from os import PathLike
from pathlib import Path
from typing import Optional

from nanofactorysystem.aerobasic import AxisStatusDataItem, SingleAxis, SystemStatusDataItem, WaitMode, Axis
from nanofactorysystem.aerobasic.ascii import AerotechAsciiInterface, DummyAsciiInterface
from nanofactorysystem.aerobasic.constants import AxisStatus
from nanofactorysystem.aerobasic.constants.tasks import ProgrammingMode, TaskState, TaskStatusDataItem, TaskMode, TaskStatus, \
    VelocityMode
from nanofactorysystem.aerobasic.programs import AeroBasicProgram
from nanofactorysystem.devices.aerotech.task import Task
from nanofactorysystem.devices.coordinate_system import Point3D


class Aerotech3200:
    MAX_NUMBER_OF_TASKS = 32

    def __init__(self, hostname: str = "127.0.0.1", port: int = 8000, *, dummy=False):
        if dummy:
            self.api = DummyAsciiInterface()
        else:
            self.api = AerotechAsciiInterface(hostname=hostname, port=port)

        # Own state
        self.programming_mode: Optional[ProgrammingMode] = None
        self.velocity_mode: Optional[VelocityMode] = None
        self.wait_mode: Optional[WaitMode] = None
        self.enabled_axes = SingleAxis._NO_AXIS
        self.tasks = tuple([Task(self.api, i) for i in range(Aerotech3200.MAX_NUMBER_OF_TASKS)])

    def __del__(self):
        self.close()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False  # Propagate exception to higher levels

    def connect(self):
        self.api.connect()

    def close(self):
        self.api.close()

    def initialize(self):
        """
        1. Retrieve current configurations
            - Axis status (Enabled, disabled)
            - Axis position
            - Version
        2. Set standard parameter
            - SECONDS
            - PRIMARY
        :return:
        """
        self.set_programming_mode(ProgrammingMode.ABSOLUTE)
        self.set_velocity_mode(VelocityMode.ON)
        self.set_wait_mode(WaitMode.AUTO)

    def sync_internal_state(self):
        for task in self.tasks:
            task.sync_all()

    @cached_property
    def version(self):
        return self.api.VERSION()

    @property
    def system_time(self) -> datetime.datetime:
        time_ms = float(self.api.SYSTEMSTATUS(SystemStatusDataItem.Timer))
        return datetime.datetime.fromtimestamp(time_ms / 1000)

    @property
    def xyz(self) -> Point3D:
        response = self.api.STATUS(
            (SingleAxis.X, AxisStatusDataItem.PositionFeedback),
            (SingleAxis.Y, AxisStatusDataItem.PositionFeedback),
            (SingleAxis.Z, AxisStatusDataItem.PositionFeedback)
        )
        return Point3D(*tuple(map(float, response.replace(",", ".").split(" "))))

    @property
    def axis_status(self) -> dict[SingleAxis, AxisStatus]:
        query_tuples = (
            (SingleAxis.X, AxisStatusDataItem.AxisStatus),
            (SingleAxis.Y, AxisStatusDataItem.AxisStatus),
            (SingleAxis.Z, AxisStatusDataItem.AxisStatus),
            (SingleAxis.A, AxisStatusDataItem.AxisStatus),
            (SingleAxis.B, AxisStatusDataItem.AxisStatus),
        )
        response = self.api.STATUS(*query_tuples)
        axis_status_tmp = map(lambda x: AxisStatus(int(x)), response.replace(",", ".").split(" "))
        axis_status = {axis: status for ((axis, dataitem), status) in zip(query_tuples, axis_status_tmp)}
        return axis_status

    def set_programming_mode(self, programming_mode: ProgrammingMode):
        # self.api.send(programming_mode.value)  # Quick, but dirty way

        programming_mode = ProgrammingMode(programming_mode)

        if programming_mode == ProgrammingMode.ABSOLUTE:
            self.api.ABSOLUTE()
        elif programming_mode == ProgrammingMode.INCREMENTAL:
            self.api.INCREMENTAL()
        else:
            raise NotImplementedError(f"Programming mode {programming_mode} not implemented yet.")
        self.programming_mode = programming_mode

    def set_velocity_mode(self, velocity_mode: VelocityMode):
        velocity_mode = VelocityMode(velocity_mode)

        self.api.VELOCITY(velocity_mode)
        self.velocity_mode = velocity_mode

    def set_wait_mode(self, wait_mode: WaitMode):
        wait_mode = WaitMode(wait_mode)

        self.api.WAIT_MODE(wait_mode)
        self.wait_mode = wait_mode

    def get_task_state(self, task_id: int) -> TaskState:
        return TaskState(int(self.api.PROGRAM_STATUS(task_id, TaskStatusDataItem.TaskState)))

    def get_task_status(self, task_id: int) -> TaskState:
        response = (self.api.STATUS(
            (task_id, TaskStatusDataItem.TaskStatus0),
            (task_id, TaskStatusDataItem.TaskStatus1),
            (task_id, TaskStatusDataItem.TaskStatus2)
        )).split(" ")
        return TaskStatus.from_strings(*response)
        # return TaskStatus.from_strings(response[0],response[1],response[2])

    def get_task_mode(self, task_id: int) -> TaskMode:
        return TaskMode(int(self.api.PROGRAM_STATUS(task_id, TaskStatusDataItem.TaskMode)))

    def get_wait_mode(self, task_id: int) -> WaitMode:
        task_mode = self.get_task_mode(task_id)
        return WaitMode.from_task_mode(task_mode)

    def run_program_as_task(
            self,
            program: PathLike | AeroBasicProgram,
            *,
            task_id: Optional[int] = None,
            program_ready_timeout=10,  # Seconds
            program_start_running_timeout=10,  # Seconds
    ) -> Task:
        # Either use path as program or convert AeroBasicProgram to temporary file
        if isinstance(program, AeroBasicProgram):
            now = datetime.datetime.now()
            hash_str = hashlib.sha256(str(random.random()).encode()).hexdigest()
            path = Path(f"{now :%Y%m%d_%H%M%S}_automatic_program_{hash_str[:5]}.pgm")
            path.parent.mkdir(exist_ok=True, parents=True)
            program.write(path)
        else:
            path = Path(program)

        # Load program
        if task_id is None:
            # TODO: Better algorithm to determine task_id
            task_id = 2
        self.api.PROGRAM_LOAD(task_id, path)

        # Wait for program to be ready
        task = Task(self.api, task_id, file_path=path)
        query_delay = 0.1
        for i in range(int(program_ready_timeout / query_delay)):
            task.sync_all()
            if task.task_state == TaskState.program_ready:
                break
            time.sleep(query_delay)
        else:
            raise RuntimeError(f"Could not load program {path} after {program_ready_timeout} seconds!")

        # Start program
        self.api.PROGRAM_START(task_id)

        # Wait for program to run
        for i in range(int(program_start_running_timeout / query_delay)):
            task.sync_all()
            if task.task_state == TaskState.program_running:
                break
            time.sleep(query_delay)
        else:
            raise RuntimeError("Program did not start")

        return task

    def run_program_synchron(self, program: AeroBasicProgram):
        for line in program:
            self.api.send(line)

    def enable_axes(self, axes: SingleAxis):
        self.api.ENABLE(axes)
        self.enabled_axes |= axes

    def home(self):
        self.api.HOME(Axis.YZ | Axis.AB)
        self.api.LINEAR(Y=80)
        self.api.HOME(SingleAxis.X)
        self.api.LINEAR(Y=0)
