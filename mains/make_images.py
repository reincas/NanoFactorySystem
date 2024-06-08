##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
import datetime
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, Rectangle
from scidatacontainer import Container

from nanofactorysystem import System, ImageContainer, Plane, mkdir, getLogger
from nanofactorysystem.aerobasic.constants import TaskState
from nanofactorysystem.aerobasic.programs import AeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings import DrawableObject
from nanofactorysystem.aerobasic.programs.drawings.circle import FilledCircle2D, LineCircle2D
from nanofactorysystem.aerobasic.programs.drawings.lens import Cylinder, SphericalLens
from nanofactorysystem.aerobasic.programs.drawings.lines import CornerRectangle
from nanofactorysystem.aerobasic.programs.setups import DefaultSetup, SetupIFOV
from nanofactorysystem.aerobasic.utils.visualization import read_file, plot_movements
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, PlaneFit, DropDirection, Unit, \
    Point3D, Coordinate
from nanofactorysystem.dhm.optimage import optImageMedian

args = {
    "attenuator": {
        "fitKind": "quadratic",
    },
    "controller": {
        "zMax": 25700.0,
    },
    "sample": {
        "name": "#1",
        "orientation": "top",
        "substrate": "boro-silicate glass",
        "substrateThickness": 700.0,
        "material": "SZ2080",
        "materialThickness": 75.0,
    },
    "focus": {},
    "layer": {
        "beta": 0.7,
    },
    "plane": {},
}



def main():
    user = "Reinhard"
    objective = "Zeiss 20x"

    logger.info("Initialize system object...")
    with System(user, objective, logger, **args) as system:
        right_edge = [0, 15640]
        left_edge = [1000, 28810]
        front_edge = [-5600, 21935]
        far_edge = [6100, 21934]

        for name, (x,y) in {
            "right": right_edge,
            "left": left_edge,
            "front":front_edge,
            "far":far_edge,
        }.items():
            system.log.info(f"Go to {name} edge: {x*Unit.um.value,y*Unit.um.value}")
            system.a3200_new.api.LINEAR(X=x * Unit.um.value, Y=y * Unit.um.value, F=20)
            system.log.info(f"Create image")
            image = system.camera.container()
            img_path = path / f"image_edge_{name}.zdc"
            system.log.info(f"Save image to {img_path}")
            image.write(img_path)


if __name__ == '__main__':
    # path = Path(mkdir(f".output/dhm_paper/{datetime.datetime.now():%Y%m%d_%H%M%S}", clean=False))
    path = Path(mkdir(f".output/dhm_paper/{datetime.datetime.now():%Y%m%d}", clean=False))
    logger = getLogger(logfile=f"{path}/console.log")

    main()
