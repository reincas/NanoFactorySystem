##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
import time
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np

from scidatacontainer import Container
from nanofactorysystem import System, Plane, getLogger, mkdir, ImageContainer
from nanofactorysystem.aerobasic.constants import TaskState
from nanofactorysystem.aerobasic.programs.drawings.lines import Corner
from nanofactorysystem.aerobasic.programs.setups import DefaultSetup
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, PlaneFit, StaticOffset, DropDirection, Unit, \
    Point3D
from nanofactorysystem.aerobasic.utils.visualization import read_file, plot_movements
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


def find_and_log_plane(system) -> Plane:
    zlo = zup = system.z0
    plane = Plane(zlo, zup, system, logger, **args)

    # logger.info("Load steps...")
    # with open(f"{path}/steps.json", "r") as fp:
    #    plane.steps = json.loads(fp.read())

    logger.info("Store background image...")
    plane.layer.focus.imgBack.write(f"{path}/back.zdc")

    logger.info("Run plane detection...")
    for j in range(ny):
        for i in range(nx):
            x = system.x0 + i * dx
            y = system.y0 + j * dy
            plane.run(x, y, path=path)

    # logger.info("Store steps...")
    # with open(f"{path}/steps.json", "w") as fp:
    #    fp.write(json.dumps(plane.steps))

    logger.info("Store results...")
    dc = plane.container()
    dc.write(f"{path}/plane.zdc")
    logger.info("Done.")
    return dc


if __name__ == '__main__':
    dx = 80.0
    dy = 80.0
    nx = 2
    ny = 2

    user = "Reinhard"
    objective = "Zeiss 20x"
    path = Path(mkdir(".test/plane", clean=False))
    logger = getLogger(logfile=f"{path}/console.log")

    logger.info("Initialize system object...")
    with System(user, objective, logger, **args) as system:
        logger.info("Initialize plane object...")

        # Old Plane-Fitting
        plane_path = path / "plane.zdc"
        if Path(plane_path).exists():
            dc = Container(file=str(plane_path))
        else:
            dc = find_and_log_plane(system)

        points = dc["meas/result.json"]["lower"]["points"]

        # New coordinate system
        system.a3200_new.api(DefaultSetup())
        plane_fit_function = PlaneFit.from_points(np.asarray(points))
        current_position = system.a3200_new.xyz
        coordinate_system = CoordinateSystem(
            offset_x=current_position.X / Unit.um.value,
            offset_y=current_position.Y / Unit.um.value,
            z_function=StaticOffset(plane_fit_function(current_position.X / Unit.um.value, current_position.Y / Unit.um.value)),
            drop_direction=DropDirection.DOWN,
            unit=Unit.um
        )
        print(plane_fit_function)
        print(coordinate_system)

        corner = Corner(
            Point3D(-50, -50, -2),
            length=100,
            width=10,
            height=7,
            hatch_size=0.5,
            layer_height=0.75,
            rotation_degree=90,
            coordinate_system=coordinate_system,
            F=2000
        )

        image_center = coordinate_system.convert(corner.center_point.as_dict())
        if input(f"Driving to {image_center} to take an image. Continue? (y/n)") != "y":
            exit(1)

        # Calibrate DHM
        system.a3200_new.api.LINEAR(**image_center)
        optImageMedian(system.dhm, vmedian=32, logger=logger)
        m = system.dhm.motorscan()
        logger.info(f"Motor pos: {system.dhm.device.MotorPos:.1f} µm (set: {m:.1f} µm)")

        # DHM Image before
        system.a3200_new.api.LINEAR(**image_center)
        dc = system.dhm.container(opt=True)
        fn = path / "hologram_before.zdc"
        logger.info(f"Store hologram container file '{fn}'")
        dc.write(fn)

        # Camera Image before
        system.a3200_new.api.LINEAR(**image_center)
        camera_image_container = system.getimage()
        assert isinstance(camera_image_container, ImageContainer)
        camera_image_container.write(path / "camera_image_before.zdc")
        print(f"Location: {camera_image_container.location}")
        cv2.imshow("Image before", camera_image_container.img)
        cv2.waitKey(10)
        # system.a3200_new.api.send("RAMP RATE ")
        # img_before = system.dhm.getimage()

        pgm_file = path / "corner1.txt"
        corner = DefaultSetup() + corner
        corner.write(pgm_file)
        movements = read_file(pgm_file)
        plot_movements(movements)
        plt.show()
        if input("Execute movements (y/n):") == "y":
            t1 = time.time()
            task = system.a3200_new.run_program_as_task(pgm_file, task_id=1)
            while task.task_state == TaskState.program_running:
                time.sleep(0.1)
                task.sync_all()

            t2 = time.time()
            logger.info(f"Making corner took {t2 - t1:.2f}s")


        # DHM after
        system.a3200_new.api.LINEAR(**image_center)
        dc = system.dhm.container(opt=True)
        fn = path / "hologram_after.zdc"
        logger.info(f"Store hologram container file '{fn}'")
        dc.write(fn)

        # Camera after
        system.a3200_new.api.LINEAR(**image_center)
        camera_image_container = system.getimage()
        assert isinstance(camera_image_container, ImageContainer)

        camera_image_container.write(path / "camera_image_after.zdc")
        cv2.imshow("Image After", camera_image_container.img)
        cv2.waitKey(10)

        img_after = system.dhm.getimage()
