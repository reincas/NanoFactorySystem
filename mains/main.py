import os
import datetime
from nanofactorysystem.devices.coordinate_system import Point2D
from Experiments.parameter_testprint_slicing_hatching import testprint as print_program


def main():
    edges = [
        [0, 18550],  # right edge
        [- 600, 27800],  # left edge
        [- 5200, 23100],  # near edge
        [4600, 22900]  # far edge
    ]

    center = Point2D(X=-1500,
                     Y=23500)
    # ToDo: Make sure center is within the edges
    # assert center.Y in [ymin, ymax]
    # assert center.X in [xmin, xmax]

    root_path = os.path.join(os.getcwd(), ".output/")
    t1 = datetime.datetime.now()
    print_program(absolute_center=center,
                  resin_dimension=edges,
                  ask_continue_box=False,
                  # path=root_path,
                  objective="Zeiss 63x",
                  user="Hannes")
    t2 = datetime.datetime.now()
    time = t2 - t1
    print(f"Total time: {time}")
    # ToDo: Get a timelogger or a overview on how long it will take


# General ToDos
# ToDo 1: identification for substrate to track the printing of different experiments on one substrate
# ToDo 2: Build a custom experiment database based on different identification factors (e.g. substrate, date, objective etc)
# ToDo 3: Plane Fitting: change to a "just border" mode and the currently used mode (Between each FOV of a print)

if __name__ == "__main__":
    main()
