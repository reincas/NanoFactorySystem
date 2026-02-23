import os
import datetime
from nanofactorysystem.devices.coordinate_system import Point2D
from Experiments.Grating_63.binary_grating_test1 import binary_testprint as print_program
# from Experiments.Grating_63.binary_grating_test1 import binary_testprint as print_program
# from Experiments.parameter_study.line_test.Power_speed_line_test import dhm_testprint as print_program

# from Experiments.parameter_study.parameter_testprint_power_speed_test4orientation import testprint as print_program
# from Experiments.testprint_dhm import dhm_testprint as print_program



def main():
    edges = [

        [700,   16050],  # right edge
        [700,  27900],  # left edge
        [-5100, 21900],  # near edge
        [6800,  22100]  # far edge

    ]
    # old experiment 100-20200 (double corner) - other corners in negative x and negative y direction

    center = Point2D(X=600,  #
                     Y=20000)  #
    # ToDo: Make sure center is within the edges
    # assert center.Y in [ymin, ymax]
    # assert center.X in [xmin, xmax]

    root_path = os.path.join(os.getcwd(), ".output/")
    t1 = datetime.datetime.now()

    print_program(absolute_center=center,
                  resin_dimension=edges,
                  ask_continue_box=False,
                  path=r"C:\Users\Nanofactory\Desktop\Hannes\Gratings\2025_11_25_1",  # please change here
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
