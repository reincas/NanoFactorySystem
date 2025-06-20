import os
import datetime
from nanofactorysystem.devices.coordinate_system import Point2D
from Experiments.qr_code_investigation import qr_code_test as print_program
# from Experiments.testprint_dhm import dhm_testprint as print_program

"""
Maximum Dimensions DHM
70µm x 70µm with 63x 
"""
def main():
    edges = [
        [1700, 18900],  # right edge
        [1800, 28400],  # left edge
        [-3100, 23600],  # near edge
        [6600, 23900]  # far edge
    ]
    # one structure at 280 25720 - seems like stair

    center = Point2D(X=2000,        #
                     Y=25000)       #
    # ToDo: Make sure center is within the edges
    # assert center.Y in [ymin, ymax]
    # assert center.X in [xmin, xmax]

    root_path = os.path.join(os.getcwd(), ".output/")
    t1 = datetime.datetime.now()
    print_program(absolute_center=center,
                  resin_dimension=edges,
                  ask_continue_box=True,
                  # path=r"C:\Users\Nanofactory\Documents\OFFLINE_Hannes\March_2025_Power_test_DHMPaper",
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
