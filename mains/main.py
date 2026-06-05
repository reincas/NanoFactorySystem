import os
import datetime
from nanofactorysystem.devices.coordinate_system import Point2D
#from Experiments.parameter_study.line_test.Power_speed_line_test import print_file as print_program
# from Experiments.Kailas.padding_test_0_5mm import print_file as print_program
# from Experiments.Kailas.ifovGrating_diffPower_500um import print_file as print_program
# from Experiments.Kailas.ifovGrating_diffPower_75um import print_file as print_program
from Experiments.Kailas.ifovGrating_diffPower_500um import print_file as print_program
# from Experiments.IFOV_63.ifov_test import print_file as print_program


def main():
    edges = [
        [900, 17500],  # right edge
        [1000, 26700],  # left edge
        [-3700, 22000],  # near edge
        [5500, 22200]  # far edge
    ]
    # old experiment 100-20200 (double corner) - other corners in negative x and negative y direction

    # center = Point2D(X=-1000,  #
    #                  Y=22000)  #
    center = Point2D(X=1000,  #
                     Y=22000)  #

    # ToDo: Make sure center is within the edges
    # assert center.Y in [ymin, ymax]
    # assert center.X in [xmin, xmax]

    root_path = os.path.join(os.getcwd(), ".output/")
    t1 = datetime.datetime.now()

    print_program(absolute_center=center,
                  resin_dimension=edges,
                  ask_continue_box=True,
                  path=r"C:\Users\Nanofactory\Desktop\Hannes\Experiment data\Kailas",  # please change here
                  objective="Zeiss 63x",
                  # objective="Zeiss 20x",
                  user="Hannes",
                  substrate={"Name": "IFOV Binary Grating different power with DHM",
                             "Number of drops": 1,
                             "Used drop": "Mitte",
                             "Description": f"Testing Gratings of 500µm size and different powers : "
                                            f"[0.1, 0.15, 0.2, 0.25 , 0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7]"},
                  dhm_usage=False,
                  setup="IFOV_on")

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
