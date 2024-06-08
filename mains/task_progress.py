from nanofactorysystem.aerobasic import TaskStatusDataItem
from nanofactorysystem.devices.aerotech import Task, Aerotech3200

task_id = 1
device = Aerotech3200()
device.connect()
task = Task(device.api, task_id=task_id, file_path=".output/dhm_paper/20240607/rectangle.txt")
task.wait_to_finish()
