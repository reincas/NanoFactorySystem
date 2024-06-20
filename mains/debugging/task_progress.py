from nanofactorysystem.aerobasic import TaskStatusDataItem
from nanofactorysystem.devices.aerotech import Task, Aerotech3200

task_id = 1
device = Aerotech3200()
device.connect()
task = Task(device.api, task_id=task_id, file_path=".output/dhm_paper/20240617/programs/layers/structure_01.027.txt")
print(task.task_state)
print(task.task_status0)
print(task.task_status1)
print(task.task_status2)
print(task.task_mode)
print(task.wait_mode)

task.finish()
# task.wait_to_finish()
