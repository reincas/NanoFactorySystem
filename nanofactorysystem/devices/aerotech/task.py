from nanofactorysystem.aerobasic import TaskStatusDataItem, WaitMode
from nanofactorysystem.aerobasic.ascii import AerotechAsciiInterface
from nanofactorysystem.aerobasic.constants.tasks import TaskMode, TaskStatus0, TaskState, TaskStatus2, TaskStatus1


class Task:
    def __init__(self, api: AerotechAsciiInterface, task_id: int):
        self.api = api
        self.task_id = task_id

        self._task_status0 = None
        self._task_status1 = None
        self._task_status2 = None
        self._task_mode = None
        self._task_state = None

    def sync_all(self):
        mode, state, status_0, status_1, status_2 = self.api.STATUS(
            (self.task_id, TaskStatusDataItem.TaskMode),
            (self.task_id, TaskStatusDataItem.TaskState),
            (self.task_id, TaskStatusDataItem.TaskStatus0),
            (self.task_id, TaskStatusDataItem.TaskStatus1),
            (self.task_id, TaskStatusDataItem.TaskStatus2),
        ).split(" ")

        self._task_mode = TaskMode(int(mode))
        self._task_state = TaskState(int(state))
        self._task_status0 = TaskStatus0(int(status_0))
        self._task_status1 = TaskStatus1(int(status_1))
        self._task_status2 = TaskStatus2(int(status_2))

    def reset(self):
        self._task_mode = None
        self._task_state = None
        self._task_status0 = None
        self._task_status1 = None
        self._task_status2 = None

    @property
    def task_mode(self) -> TaskMode:
        if self._task_mode is None:
            self.sync_all()
        return self._task_mode

    @property
    def task_state(self) -> TaskState:
        if self._task_state is None:
            self.sync_all()
        return self._task_state

    @property
    def task_status0(self) -> TaskStatus0:
        if self._task_status0 is None:
            self.sync_all()
        return self._task_status0

    @property
    def task_status1(self) -> TaskStatus1:
        if self._task_status1 is None:
            self.sync_all()
        return self._task_status1

    @property
    def task_status2(self) -> TaskStatus2:
        if self._task_status2 is None:
            self.sync_all()
        return self._task_status2

    @property
    def wait_mode(self) -> WaitMode:
        return WaitMode.from_task_mode(self.task_mode)
