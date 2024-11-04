import os
import datetime
from nanofactorysystem.devices.coordinate_system import Point2D
from Experiments.dhm_paper_print import dhm_paper as print_program
# from Experiments.testprint_dhm import dhm_testprint as print_program

"""
Maximum Dimensions DHM
70µm x 70µm with 63x 
"""
def main():
    edges = [
        [1700, 15850],  # right edge
        [2300, 25200],  # left edge
        [-2550, 20100],  # near edge
        [6600, 20800]  # far edge
    ]

    center = Point2D(X=2000,
                     Y=20500)
    # ToDo: Make sure center is within the edges
    # assert center.Y in [ymin, ymax]
    # assert center.X in [xmin, xmax]

    root_path = os.path.join(os.getcwd(), ".output/")
    t1 = datetime.datetime.now()
    print_program(absolute_center=center,
                  resin_dimension=edges,
                  ask_continue_box=True,
                  # path=os.path.join(root_path, "test"),
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
