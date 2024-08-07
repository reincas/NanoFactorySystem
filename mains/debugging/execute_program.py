import time

from nanofactorysystem.aerobasic.constants import TaskState
from nanofactorysystem.aerobasic.programs.drawings.circle import Circle2D, Spiral2D, FilledCircle2D, LineCircle2D
from nanofactorysystem.aerobasic.programs.setups import DefaultSetup
from nanofactorysystem.devices.aerotech import Aerotech3200
from nanofactorysystem.devices.coordinate_system import Point2D, CoordinateSystem, Point3D

if __name__ == '__main__':
    # Connect
    a3200 = Aerotech3200()
    a3200.connect()

    # Create program
    # circle = Circle2D(center=a3200.xyz, radius=0.1, velocity=0.2)
    # prg = DefaultSetup() + circle.draw_on(CoordinateSystem())

    spiral = LineCircle2D(center=Point3D(0, 0, 0), radius_start=0.1, radius_end=0.02, hatch_size=0.002, velocity=1,
                          acceleration=20)
    coord = CoordinateSystem(z_function=a3200.xyz.Z)
    coord.axis_mapping = {"X": "A", "Y": "B"}
    prg = DefaultSetup() + spiral.draw_on(coord)
    print(prg.n_lines)

    # Execute
    t1 = time.perf_counter()
    task = a3200.run_program_as_task(prg, task_id=2)
    task.wait_to_finish()
    t2 = time.perf_counter()

    print(f"Program took {t2 - t1:.3f}s")
