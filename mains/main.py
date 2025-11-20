import os
import datetime
from nanofactorysystem.devices.coordinate_system import Point2D
from Experiments.parameter_study.parameter_testprint_power_speed import testprint as print_program
# from Experiments.Grating.binary_grating_test1 import binary_testprint as print_program
# from Experiments.parameter_study.line_test.Power_speed_line_test import dhm_testprint as print_program

# from Experiments.parameter_study.parameter_testprint_power_speed_test4orientation import testprint as print_program
# from Experiments.testprint_dhm import dhm_testprint as print_program

"""
Binary Grating
Hannes 21.08
"""


def main():
    edges = [

        [800,   16800],  # right edge
        [600,  27100],  # left edge
        [-4600, 22300],  # near edge
        [5800,  21900]  # far edge

    ]
    # old experiment 100-20200 (double corner) - other corners in negative x and negative y direction

    center = Point2D(X=0,  #
                     Y=20000)  #
    # ToDo: Make sure center is within the edges
    # assert center.Y in [ymin, ymax]
    # assert center.X in [xmin, xmax]

    root_path = os.path.join(os.getcwd(), ".output/")
    t1 = datetime.datetime.now()

    print_program(absolute_center=center,
                  resin_dimension=edges,
                  ask_continue_box=True,
                  path=r"C:\Users\Nanofactory\Desktop\Sibin Joseph\Experiment data\parameter_study\main_experiments\second_print",  # please change here
                  objective="Zeiss 63x",
                  user="Hannes",
                  dhm_usage=False)
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
