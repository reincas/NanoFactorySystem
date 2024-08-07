##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
import datetime
import time
from pathlib import Path

from nanofactorysystem import (System, mkdir, getLogger)
from nanofactorysystem.aerobasic.programs.setups import DefaultSetup
from nanofactorysystem.aerobasic.ascii import AerotechError
from nanofactorysystem.aerobasic.programs import AeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings import DrawableObject, DrawableAeroBasicProgram
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, PlaneFit, DropDirection, Unit, \
    Point2D, Point3D, Coordinate


def create_programs(path, n_prog: int = 150):
    structure_center_absolute_um = {
        "X": 0,
        "Y": 0,
        "Z": 0
    }

    coordinate_system = CoordinateSystem(
        offset_x=structure_center_absolute_um["X"],
        offset_y=structure_center_absolute_um["Y"],
        z_function=structure_center_absolute_um["Z"],
        unit=Unit.um
    )
    zline = AeroBasicProgram()
    zline.lines = [
                   "ABSOLUTE",
                   "LINEAR X0 Y0 Z0",
                   "DWELL 0.5",
                   "GALVO LASEROVERRIDE A ON",
                   "GALVO LASEROVERRIDE A OFF"
                   ]
    for i in range(n_prog):
        program = DrawableAeroBasicProgram(coordinate_system)
        program.add_programm(zline)
        test_file_path = path / "programs" / f"test_{i:02d}.txt"
        program.write(test_file_path)


def weitermachen():
    if input("Continue? (y/n)") != "y":
        return


if __name__ == '__main__':
    user = "Hannes"
    objective = "Zeiss 20x"

    # path = Path(mkdir(f".output/dhm_paper/{datetime.datetime.now():%Y%m%d_%H%M%S}", clean=False))
    path = Path(mkdir(f".output/task-test/{datetime.datetime.now():%Y%m%d}", clean=False))
    logger = getLogger(logfile=f"{path}/console.log")

    # one time creation of programs
    n_prog = 220
    # create_programs(path, n_prog)
    # weitermachen()

    logger.info("Initialize system object...")
    args = {"controller": {
        "zMax": 25700.0,
    }}
    with System(user, objective, logger, **args) as system:
        logger.info("Initialize plane object...")
        a3200 = system.a3200_new
        a3200.api(DefaultSetup())
        # i = 0
        for i in range(n_prog):
            test_file_path = path / "programs" / f"test_{i:02d}.txt"

            # Documentation: A3200 Help (AeroBasic Programming - Commands- and Functions - Program Control)
            # This should work
            # a3200.api.PROGRAM_LOAD(2, test_file_path)
            # a3200.api.PROGRAM_ASSOCIATE(2, f"test_{i:02d}.txt")
            task = system.a3200_new.run_program_as_task(test_file_path, task_id=2)
            task.wait_to_finish()
            task.finish()
            # This should also work
            # a3200.api.PROGRAM_START(2)
            # a3200.api.PROGRAM_STOP(2)

            # a3200.api.REMOVE_PROGRAM(f"test_{i:02d}.pgm")
            # print("waiting")
            time.sleep(0.3)
            print(i+1)
        # a3200.api.PROGRAM_ASSOCIATE(2, f"test_{i:02d}.txt")
