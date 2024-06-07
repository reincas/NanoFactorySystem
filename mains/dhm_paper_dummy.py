##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
import logging
import time
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Iterator

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, Rectangle
from scidatacontainer import Container

from nanofactorysystem.aerobasic.constants import TaskState
from nanofactorysystem.aerobasic.programs import AeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings import DrawableObject
from nanofactorysystem.aerobasic.programs.drawings.circle import FilledCircle2D, LineCircle2D
from nanofactorysystem.aerobasic.programs.drawings.lens import Cylinder, SphericalLens
from nanofactorysystem.aerobasic.programs.drawings.lines import CornerRectangle
from nanofactorysystem.aerobasic.programs.setups import DefaultSetup
from nanofactorysystem.aerobasic.utils.visualization import read_file, plot_movements
from nanofactorysystem.devices.aerotech import Aerotech3200
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, PlaneFit, DropDirection, Unit, \
    Point3D, Coordinate


def measure(system: "System", coordinate: Coordinate, name: str, *, save_folder: Path) -> tuple[
    Container, "ImageContainer"]:
    """
    Coordinate in mm in absolute coordinates
    """
    print(f"Cannot measure \"{name}\" in dummy mode!")
    return None, None
    # DHM Image before
    system.a3200_new.api.LINEAR(**coordinate)
    dhm_container = system.dhm.container(opt=True)
    fn = save_folder / f"hologram_{name}.zdc"
    logger.info(f"Store hologram container file '{fn}'")
    dhm_container.write(fn)

    # Camera Image before
    system.a3200_new.api.LINEAR(**coordinate)
    camera_container = system.getimage()
    assert isinstance(camera_container, ImageContainer)
    camera_container.write(str(path / f"camera_{name}.zdc"))
    print(f"Location: {camera_container.location}")
    return dhm_container, camera_container


@dataclass
class ExperimentConfiguration:
    resin_corner_tr: np.ndarray  # 2D
    resin_corner_bl: np.ndarray  # 2D

    fov_size: float
    margin: float
    padding: float
    grid_center: tuple[float, float]
    grid: tuple[int, int]

    def iter_experiment_locations(self) -> Iterator[tuple[float, float]]:
        for i in range(self.grid[0]):
            for j in range(self.grid[1]):
                rect_x = self.rectangle_tl[0] + self.margin + j * (self.fov_size + self.padding)
                rect_y = self.rectangle_tl[1] + self.margin + i * (self.fov_size + self.padding)
                yield rect_x + self.fov_size / 2, rect_y + self.fov_size / 2

    def __post_init__(self):
        self.resin_corner_tr = np.asarray(self.resin_corner_tr)
        self.resin_corner_bl = np.asarray(self.resin_corner_bl)

    @property
    def center_point(self) -> np.ndarray:
        return (self.resin_corner_bl + self.resin_corner_tr) / 2

    @property
    def resin_size(self) -> np.ndarray:
        return self.resin_corner_tr - self.resin_corner_bl

    @property
    def absolute_grid_center(self) -> np.ndarray:
        return np.asarray([self.grid_center[0] + self.center_point[0], self.grid_center[1] + self.center_point[1]])

    @property
    def grid_width(self):
        return self.grid[1] * (self.fov_size + self.padding) - self.padding + 2 * self.margin

    @property
    def grid_height(self):
        return self.grid[0] * (self.fov_size + self.padding) - self.padding + 2 * self.margin

    @property
    def rectangle_tl(self):
        return self.center_point + self.grid_center - [self.grid_width / 2, self.grid_height / 2]

    @property
    def rectangle_br(self):
        return self.center_point + self.grid_center + [self.grid_width / 2, self.grid_height / 2]

    def plot(self, plane_fit_points=None):
        # Visualize experiment
        fig, ax = plt.subplots()
        assert isinstance(ax, plt.Axes)

        # Draw the ellipse
        ellipse = Ellipse(self.center_point, self.resin_size[0], self.resin_size[1], edgecolor='lightblue',
                          facecolor='none', lw=2, label="Resin Drop")
        ax.add_patch(ellipse)

        # Draw the outer rectangle
        outer_rectangle = Rectangle(self.rectangle_tl, self.grid_width, self.grid_height, edgecolor='blue',
                                    facecolor='none', lw=2, label="Experiment Field")
        ax.add_patch(outer_rectangle)

        # Draw the grid of rectangles
        center_xs = []
        center_ys = []
        for i, (x, y) in enumerate(self.iter_experiment_locations()):
            x_tl = x - self.fov_size / 2
            y_tl = y - self.fov_size / 2
            rect = Rectangle(
                (x_tl, y_tl),
                width=self.fov_size,
                height=self.fov_size,
                edgecolor='green',
                facecolor='none',
                lw=1
            )
            ax.text(x_tl, y_tl, f"{i}", color="green")
            ax.add_patch(rect)
            center_xs.append(x)
            center_ys.append(y)

        ax.scatter(center_xs, center_ys, s=3, marker="x", color="green", label="Structures")

        if plane_fit_points is not None:
            ax.scatter(*zip(*plane_fit_points), s=3, marker=".", color="red", label="Plane Fitting Probe Points")

        # Set limits and aspect ratio
        ax.set_xlim(self.resin_corner_bl[0], self.resin_corner_tr[0])
        ax.set_ylim(self.resin_corner_bl[1], self.resin_corner_tr[1])
        ax.set_xlabel("X [um]")
        ax.set_ylabel("Y [um]")
        ax.set_aspect('equal')
        plt.legend()
        plt.tight_layout()


def sample_points_for_experiment_configuration(experiment_configuration: ExperimentConfiguration, n_mid_points: 2) -> \
        list[tuple[float, float]]:
    tl = experiment_configuration.rectangle_tl + experiment_configuration.margin / 2
    br = experiment_configuration.rectangle_br - experiment_configuration.margin / 2
    points = set()
    for x in np.linspace(tl[0], br[0], n_mid_points + 2):
        points.add((x, tl[1]))
        points.add((x, br[1]))

    for y in np.linspace(tl[1], br[1], n_mid_points + 2):
        points.add((tl[0], y))
        points.add((br[0], y))

    return list(points)


def main():
    system = None

    logger.info("DUMMY MODE. SYSTEM DISABLED")
    logger.info("Initialize plane object...")

    # TODO: Determine automatically
    experiment_configuration = ExperimentConfiguration(
        resin_corner_bl=np.asarray((-5700, 15000)),  # um
        resin_corner_tr=np.asarray((6700, 28100)),  # um
        fov_size=500,
        margin=200,
        padding=100,
        grid_center=(0, 5100),
        grid=(2, 3),  # Rows, Cols
    )

    a3200_new = Aerotech3200(dummy=True)

    plane_fit_points = sample_points_for_experiment_configuration(experiment_configuration, n_mid_points=2)

    # Visualize experiment
    experiment_configuration.plot(plane_fit_points)
    plt.show()
    # if input("Continue with plane fitting? (y/n)") != "y":
    #     return

    # Old Plane-Fitting
    plane_path = path / "plane.zdc"
    if Path(plane_path).exists():
        dc = Container(file=str(plane_path))
    else:
        raise FileNotFoundError("In Dummy mode a container is needed")

    plane_points = dc["meas/result.json"]["lower"]["points"]
    plane_fit_function = PlaneFit.from_points(np.asarray(plane_points))  # in um
    logger.info(plane_fit_function)

    # Setup system for drawing
    a3200_new.api(DefaultSetup())  # TODO: Comment in again
    # system.a3200_new.api(SetupIFOV())

    # TODO: Make full image of whole scene

    # Define rectangle
    rectangle = CornerRectangle(
        Point3D(0, 0, -2),
        rectangle_width=experiment_configuration.grid_width,
        rectangle_height=experiment_configuration.grid_height,
        corner_width=100,
        corner_length=800,
        height=7,
        hatch_size=0.5,
        layer_height=0.75,
        F=2000
    )
    # Custom drawing on coordinate system specified for each point depending on plane fitting
    rectangle_program = AeroBasicProgram()
    rectangle_program(DefaultSetup())
    coordinate_system_grid = CoordinateSystem(
        offset_x=experiment_configuration.absolute_grid_center[0],
        offset_y=experiment_configuration.absolute_grid_center[1],
        z_function=plane_fit_function,
        drop_direction=DropDirection.DOWN,
        unit=Unit.um
    )

    for corner in [rectangle.tl_corner, rectangle.bl_corner, rectangle.br_corner, rectangle.tr_corner]:
        z_offset = coordinate_system_grid.convert(corner.center_point.as_dict())["Z"]

        coordinate_system = CoordinateSystem(
            offset_x=experiment_configuration.absolute_grid_center[0],
            offset_y=experiment_configuration.absolute_grid_center[1],
            z_function=z_offset / Unit.um.value,
            drop_direction=DropDirection.DOWN,
            unit=Unit.um
        )
        rectangle_program.add_programm(corner.draw_on(coordinate_system))

    # Make tr corner thicker
    corner = rectangle.tr_corner
    z_offset = coordinate_system_grid.convert(corner.center_point.as_dict())["Z"]

    coordinate_system = CoordinateSystem(
        offset_x=experiment_configuration.absolute_grid_center[0] + corner.width,
        offset_y=experiment_configuration.absolute_grid_center[1] - corner.width,
        z_function=z_offset / Unit.um.value,
        drop_direction=DropDirection.DOWN,
        unit=Unit.um
    )
    rectangle_program.add_programm(corner.draw_on(coordinate_system))

    image_center = coordinate_system_grid.convert(rectangle.center_point.as_dict())
    # Calibrate DHM
    a3200_new.api.LINEAR(**image_center)

    # TODO: Comment in again
    # optImageMedian(system.dhm, vmedian=32, logger=logger)
    # m = system.dhm.motorscan()
    # logger.info(f"Motor pos at {image_center}: {system.dhm.device.MotorPos:.1f} µm (set: {m:.1f} µm)")

    measure(system, image_center, "before", save_folder=path)

    pgm_file = path / "rectangle.txt"

    rectangle_program.write(pgm_file)
    movements = read_file(pgm_file)
    all_movements = movements[:]
    plot_movements(movements)
    plt.show()
    if input("Execute movements (y/n):") == "y":
        t1 = time.time()
        task = a3200_new.run_program_as_task(pgm_file, task_id=1)
        while task.task_state == TaskState.program_running:
            time.sleep(0.1)
            task.sync_all()

        t2 = time.time()
        logger.info(f"Making corner took {t2 - t1:.2f}s")

    structures: list[DrawableObject] = [
        SphericalLens(Point3D(0, 0, -2), 150, 500, 0.75, circle_object_factory=FilledCircle2D.as_circle_factory(2000), hatch_size=0.5, velocity=2000),
        Cylinder(Point3D(0, 0, -2), 150, 12, 0.75, circle_object_factory=LineCircle2D.as_circle_factory(100, 2000), hatch_size=0.5, velocity=2000),
        Cylinder(Point3D(0, 0, -2), 150, 12, 0.75, circle_object_factory=FilledCircle2D.as_circle_factory(2000), hatch_size=0.5, velocity=2000),
        # Cylinder(Point3D(0, 0, -2), 150, 12, 0.75, circle_object_factory=Spiral2D, hatch_size=0.5, velocity=2000),
    ]

    for i, ((x, y), structure) in enumerate(zip(experiment_configuration.iter_experiment_locations(), structures)):
        assert isinstance(structure, DrawableObject)
        z_offset = plane_fit_function(x, y)
        structure_center_absolute_um = {
            "X": x,
            "Y": y,
            "Z": z_offset
        }
        structure_center_absolute_mm = {k:v*Unit.um.value for k,v in structure_center_absolute_um.items()}

        coordinate_system = CoordinateSystem(
            offset_x=structure_center_absolute_um["X"],
            offset_y=structure_center_absolute_um["Y"],
            z_function=structure_center_absolute_um["Z"],
            unit=Unit.um
        )

        measure(system, structure_center_absolute_mm, f"Structure_{i:02d}_before", save_folder=path)
        program = DefaultSetup() + structure.draw_on(coordinate_system)
        structure_pgm_file = path / f"structure_{i:02d}.txt"
        program.write(structure_pgm_file)
        movements = read_file(structure_pgm_file)
        all_movements += movements
        plot_movements(movements)
        plt.title(f"Structure {i:02d}")
        plt.show()
        measure(system, structure_center_absolute_mm, f"Structure_{i:02d}_after", save_folder=path)

    plot_movements(movements)
    plt.title(f"All")
    plt.show()

    measure(system, image_center, "after", save_folder=path)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("PIL").setLevel(logging.WARN)
    logging.getLogger("matplotlib").setLevel(logging.WARN)
    path = Path(".test/plane")
    logger = getLogger()

    main()
