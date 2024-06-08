import unittest

from nanofactorysystem.aerobasic import Axis, SingleAxis, AxisStatusDataItem
from nanofactorysystem.aerobasic.ascii import AerotechError
from . import FemtikaTest


class TestFemtikaNoLaser(FemtikaTest):

    def test_system_commands(self):
        version = self.a3200.version
        print(f"Version {version}")
        last_error = self.api.LAST_ERROR()
        print(f"Last Error: {last_error}")
        system_time = self.a3200.system_time
        print(f"System Time: {system_time}")

    def test_get_position(self):
        x, y, z = self.a3200.xyz
        print(f"Position: {x=}, {y=}, {z=}")

    def test_axis_status(self):
        axis_status = self.a3200.axis_status
        for ax, status in axis_status.items():
            print(f"{ax} -> {status}")

    @unittest.skip
    def test_linear(self):
        self.api.ABSOLUTE()
        self.api.LINEAR(X=0, Y=0, Z=0)
        x, y, z = self.a3200.xyz
        print(f"Position: {x=}, {y=}, {z=}")
        self.assertAlmostEqual(0, x, places=2)
        self.assertAlmostEqual(0, y, places=2)
        self.assertAlmostEqual(0, z, places=2)

        self.api.LINEAR(X=0, Y=5, Z=2)

        x, y, z = self.a3200.xyz
        print(f"Position: {x=}, {y=}, {z=}")
        self.assertAlmostEqual(0, x, places=2)
        self.assertAlmostEqual(5, y, places=2)
        self.assertAlmostEqual(2, z, places=2)

    def test_move_home(self):
        self.api.LINEAR(X=0, Y=0, Z=0)

        x, y, z = self.a3200.xyz
        print(f"Position: {x=}, {y=}, {z=}")
        self.assertAlmostEqual(0, x, places=2)
        self.assertAlmostEqual(0, y, places=2)
        self.assertAlmostEqual(0, z, places=2)

    def test_tasks_manual(self):
        for i in range(32):
            print(f"Task {i:02d}:")
            task_state = self.a3200.get_task_state(i)
            print(task_state)
            task_status = self.a3200.get_task_status(i)
            print(task_status)
            task_mode = self.a3200.get_task_mode(i)
            print(task_mode)
            wait_mode = self.a3200.get_wait_mode(i)
            print(wait_mode)
            print()

    def test_tasks(self):
        for task in self.a3200.tasks:
            print(f"Task {task.task_id:02d}:")
            print(task.task_state)
            print(task.task_status0)
            print(task.task_status1)
            print(task.task_status2)
            print(task.task_mode)
            print(task.wait_mode)

    def test_homing(self):
        self.a3200.home()

    def test_get_axis_ramp_rate(self):
        for ax in SingleAxis.__members__.values():
            if not ax.is_single_axis():
                continue
            acceleration_rate = self.a3200.api.AXISSTATUS(ax, AxisStatusDataItem.AccelerationRate)
            print(f"{ax}: {acceleration_rate}")