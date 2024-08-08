import os

from nanofactorysystem.devices.coordinate_system import Point2D
from Experiments.testprint_dhm import dhm_testprint


def main():
    edges = [
        [-250, 18500],  # right edge
        [0, 27850],  # left edge
        [-4300, 23000],  # near edge
        [4800, 23300],  # far edge
    ]
    center = Point2D(X=0,
                     Y=20000)
    # ToDo: Make sure center is within the edges
    # assert center.Y in [ymin, ymax]
    # assert center.X in [xmin, xmax]

    root_path = os.path.join(os.getcwd(), ".output/")

    dhm_testprint(absolute_center=center,
                  resin_dimension=edges,
                  path=root_path,
                  objective="Zeiss 63x",
                  user="Hannes")

    # ToDo: Get a timelogger oder a overview on how long it will take


if __name__ == "__main__":
    main()
