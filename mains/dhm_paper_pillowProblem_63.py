##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import datetime
from pathlib import Path
from tkinter import messagebox
import numpy as np

from nanofactorysystem import mkdir, getLogger
from nanofactorysystem.aerobasic.programs.drawings.lens import AsphericalLens
from nanofactorysystem.aerobasic.programs.drawings.lines import Stair, Rectangle3D
from nanofactorysystem.devices.coordinate_system import DropDirection, Point2D, Point3D
from nanofactorysystem.experiment import Experiment, StructureType


def main():
    ask_continue_box = True
    path = Path(mkdir(f".output/dhm_paper/{datetime.datetime.now():%Y%m%d}_pillow_63", clean=False))
    # path = Path(mkdir(f".output/dhm_paper/20240624_pillow", clean=False))
    logger = getLogger(logfile=f"{path}/console.log")

    sys_args = {
        "attenuator": {
            "fitKind": "quadratic",
        },
        "controller": {
            "zMax": 25450.0,
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

    # Size of (oval) resin drop in micrometres
    # TODO: Determine automatically
    edges = np.asarray([
        [100, 18550],
        [200, 26300],
        [-3500, 22400],
        [4000, 22400]])
    resin_corner_tr = Point2D(*np.max(edges, axis=0))
    resin_corner_bl = Point2D(*np.min(edges, axis=0))
    absolute_grid_center = Point2D(0, 20000)

    with Experiment(
            path=path,
            user="Hannes",
            objective="Zeiss 63x",
            logger=logger,
            sys_args=sys_args,
            default_power=0.7,
            low_speed_um=1000,
            high_speed_um=5000,
            resin_corner_tr=resin_corner_tr,
            resin_corner_bl=resin_corner_bl,
            fov_size=150,
            margin=100,
            padding=50,
            absolute_grid_center=absolute_grid_center,
            grid=(2, 6),
            n_mid_points=0,
            drop_direction=DropDirection.DOWN,
            corner_z=-2,
            corner_width=20,
            corner_length=100,
            corner_height=5,
            corner_hatch=0.15,
            corner_slice=0.25,
            skip_corner=False) as experiment:

        # Visualize experiment
        experiment.plot_experiment(show=True)

        # Get substrate surface plane
        if ask_continue_box and not messagebox.askyesno(message="Run plane fitting?"): return
        experiment.plane_fit(force=False)

        # Optical path length for DHM
        if ask_continue_box and not messagebox.askyesno(message="Run OPL motor scan?"): return
        experiment.opl_scan(m0=3847.0, force=False)

        # TODO: Take image of whole scene
        # center = experiment.coordinate_system_grid_to_absolute.convert({"X": 0, "Y": 0, "Z": 0})
        # experiment.measure(coordinate=center, name="before")

        # Add structures
        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="rect_v5000_p07_100",
            axes="ABZ",
            power=0.7,
            structure=Rectangle3D(
                Point3D(0, 0, -2),
                height=5,
                length=100,
                width=100,
                hatch_size=0.125,
                slice_size=0.15,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="rect_v5000_p07_50",
            axes="ABZ",
            power=0.7,
            structure=Rectangle3D(
                Point3D(0, 0, -2),
                height=5,
                length=50,
                width=50,
                hatch_size=0.125,
                slice_size=0.15,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="rect_v5000_p07_20",
            axes="ABZ",
            power=0.7,
            structure=Rectangle3D(
                Point3D(0, 0, -2),
                height=5,
                length=20,
                width=20,
                hatch_size=0.125,
                slice_size=0.15,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="rect_v5000_p07_10",
            axes="ABZ",
            power=0.7,
            structure=Rectangle3D(
                Point3D(0, 0, -2),
                height=5,
                length=10,
                width=10,
                hatch_size=0.125,
                slice_size=0.15,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="rect_v5000_p07_5",
            axes="ABZ",
            power=0.7,
            structure=Rectangle3D(
                Point3D(0, 0, -2),
                height=5,
                length=5,
                width=5,
                hatch_size=0.125,
                slice_size=0.15,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="rect_v5000_p07_1",
            axes="ABZ",
            power=0.7,
            structure=Rectangle3D(
                Point3D(0, 0, -2),
                height=5,
                length=1,
                width=1,
                hatch_size=0.125,
                slice_size=0.15,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        # -----------------------------------------------------------------------------------
        # -----------------------------------------------------------------------------------
        # -----------------------------------------------------------------------------------

        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="stair_v5000_p07_7um_1",
            axes="ABZ",
            power=0.7,
            structure=Stair(
                Point3D(0, 0, -2),
                n_steps=6,
                step_height=0.6,
                step_length=20,
                step_width=50,
                hatch_size=0.125,
                slice_size=0.1,
                socket_height=7,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="stair_v5000_p07_7um_2",
            axes="ABZ",
            power=0.7,
            structure=Stair(
                Point3D(0, 0, -2),
                n_steps=6,
                step_height=0.6,
                step_length=20,
                step_width=50,
                hatch_size=0.125,
                slice_size=0.1,
                socket_height=7,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="stair_v5000_p07_7um_slice_high_1",
            axes="ABZ",
            power=0.7,
            structure=Stair(
                Point3D(0, 0, -2),
                n_steps=6,
                step_height=0.6,
                step_length=20,
                step_width=50,
                hatch_size=0.125,
                slice_size=0.2,
                socket_height=7,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="stair_v5000_p07_7um_slice_high_2",
            axes="ABZ",
            power=0.7,
            structure=Stair(
                Point3D(0, 0, -2),
                n_steps=6,
                step_height=0.6,
                step_length=20,
                step_width=50,
                hatch_size=0.125,
                slice_size=0.2,
                socket_height=7,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="lens_v5000_p07_5um",
            axes="ABZ",
            power=0.7,
            structure=AsphericalLens(
                Point3D(0, 0, -2),
                height=5,
                length=100,
                width=60,
                sphere_radius=1030,
                conic_constant=-2.3,
                hatch_size=0.100,
                slice_size=0.05,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        experiment.add_structure(
            structure_type=StructureType.NORMAL,
            name="lens_v5000_p07_5um_2",
            axes="ABZ",
            power=0.7,
            structure=AsphericalLens(
                Point3D(0, 0, -2),
                height=5,
                length=100,
                width=60,
                sphere_radius=1030,
                conic_constant=-2.3,
                hatch_size=0.100,
                slice_size=0.1,
                velocity=5000,
                acceleration=experiment.accel_a_um))

        # Build corner and structure programs
        if ask_continue_box:
            if messagebox.askyesno(message="Create programs for all structures?"):
                experiment.build_programs()
            else:
                if not messagebox.askyesno(message="Programs already created?"): return
        else:
            experiment.build_programs()

        # Print corners and structures
        if ask_continue_box and not messagebox.askyesno(message="FINAL STEP: Print experiment?"): return
        experiment.print_experiment()

        # TODO: Take image of whole scene
        # experiment.measure(coordinate=center, name="after")


if __name__ == '__main__':
    main()
