import os
import datetime
from nanofactorysystem.devices.coordinate_system import Point2D
#from Experiments.parameter_study.line_test.Power_speed_line_test import print_file as print_program
from Experiments.Kailas.padding_test_0_5mm import print_file as print_program


def main():
    edges = [
        [3500, 18650],  # right edge
        [2900, 28500],  # left edge
        [-2900, 24000],  # near edge
        [7800, 23700]  # far edge
    ]
    # old experiment 100-20200 (double corner) - other corners in negative x and negative y direction

    # center = Point2D(X=-1000,  #
    #                  Y=22000)  #
    center = Point2D(X=00,  #
                     Y=24000)  #

    # ToDo: Make sure center is within the edges
    # assert center.Y in [ymin, ymax]
    # assert center.X in [xmin, xmax]

    root_path = os.path.join(os.getcwd(), ".output/")
    t1 = datetime.datetime.now()

    print_program(absolute_center=center,
                  resin_dimension=edges,
                  ask_continue_box=False,
                  path=r"C:\Users\Nanofactory\Desktop\Hannes\Experiment data\Kailas_Exp",  # please change here
                  objective="Zeiss 63x",
                  # objective="Zeiss 20x",
                  user="Hannes",
                  substrate={"Name": "Kailas - surface lens quality",
                             "Number of drops": 1,
                             "Used drop": "Mitte",
                             "Description": "25 lenses. Big Interface Scan to adress the issue of tilt angle of the substrate."
                                            "Surface investigation in bottom middle."
                                            "Padding investigation with rectangles on top."
                                            "0µm offset and 5µm offset"},
                  dhm_usage=False,
                  setup="IFOV_off")

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
