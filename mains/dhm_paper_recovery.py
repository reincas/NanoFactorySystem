##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, Rectangle
from scidatacontainer import Container

from nanofactorysystem import System, ImageContainer, Plane, mkdir, getLogger
from nanofactorysystem.aerobasic.ascii import AerotechError
from nanofactorysystem.devices.coordinate_system import Coordinate

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


def get_grid_coordinates(
        x0: float,
        y0: float,
        dx: float = 80.0,
        dy: float = 80.0,
        nx: int = 2,
        ny: int = 2,
) -> list[tuple[float, float]]:
    coordinates = []
    for j in range(ny):
        for i in range(nx):
            x = x0 + i * dx
            y = y0 + j * dy
            coordinates.append((x, y))
    return coordinates


def find_and_log_plane(
        system: System,
        save_folder: Path,
        *,
        plane_coordinates: list[tuple[float, float]],
) -> Container:
    zlo = zup = system.z0

    # Plane needs micrometer coordinates
    plane = Plane(zlo, zup, system, logger, **args)

    logger.info("Store background image...")
    plane.layer.focus.imgBack.write(str(save_folder / f"back.zdc"))

    logger.info("Run plane detection...")
    for x, y in plane_coordinates:
        plane.run(x, y, path=path)

    logger.info("Store results...")
    dc = plane.container()
    dc.write(str(save_folder / f"plane.zdc"))
    logger.info("Done.")
    return dc


def measure(system: System, coordinate: Coordinate, name: str, *, save_folder: Path) -> tuple[
    Container, ImageContainer]:
    """
    Coordinate in mm in absolute coordinates
    """
    # DHM Image before
    # if input(f"Measuring {name}. Drive to {coordinate}? (y,n)") != "y":
    #     return None, None
    system.a3200_new.api.LINEAR(**coordinate, F=20)
    dhm_container = system.dhm.container(opt=True)
    fn = save_folder / f"hologram_{name}.zdc"
    logger.info(f"Store hologram container file '{fn}'")
    dhm_container.write(fn)

    # Camera Image before
    system.a3200_new.api.LINEAR(**coordinate, F=20)
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
    absolute_grid_center: tuple[float, float]
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
    def grid_center(self) -> np.ndarray:
        return np.asarray(
            [self.absolute_grid_center[0] - self.center_point[0], self.absolute_grid_center[1] - self.center_point[1]])

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
    user = "Hannes"
    objective = "Zeiss 20x"

    logger.info("Initialize system object...")
    with System(user, objective, logger, **args) as system:
        logger.info("Initialize plane object...")

        # TODO: Determine automatically

        right_edge = [0, 15650]
        left_edge = [0, 29150]
        front_edge = [-5300, 22400]
        far_edge = [7200, 22400]
        edges = np.asarray([right_edge, left_edge, far_edge, front_edge])

        experiment_configuration = ExperimentConfiguration(
            resin_corner_bl=np.min(edges, axis=0),  # um
            resin_corner_tr=np.max(edges, axis=0),  # um
            fov_size=500,
            margin=200,
            padding=100,
            absolute_grid_center=(975, 22400 + 2100),
            # grid_center=(-2000, -1000),
            grid=(4, 7),  # Rows, Cols
        )
        logger.info(experiment_configuration)

        # Set laser power
        system.controller.power(0.7)
        a3200_new = system.a3200_new

        plane_fit_points = sample_points_for_experiment_configuration(experiment_configuration, n_mid_points=3)

        # Visualize experiment
        experiment_configuration.plot(plane_fit_points)

        structure_programs = [pgm for pgm in (path / "programs").iterdir() if
                              pgm.name.startswith("structure") and pgm.suffix == ".txt"]

        for i, (structure_program, (x, y)) in enumerate(zip(
                sorted(structure_programs, key=lambda p: p.name),
                experiment_configuration.iter_experiment_locations()
        )):
            if i > 7:
                system.log.info(f"Printing structure {i:02d}: {structure_program.name}")
                structure_center_absolute_mm = {"X": x/1000, "Y": y/1000}

                measure(system, structure_center_absolute_mm, f"Structure_{i:02d}_before", save_folder=path)
                t1 = time.time()
                try:
                    task = a3200_new.run_program_as_task(structure_program, task_id=1)
                    task.wait_to_finish()
                    task.finish()
                except AerotechError as e:
                    logger.error(f"Program failed for structure {i:02d}: {e}")
                t2 = time.time()
                logger.info(f"Making structure {i:02d} took {t2 - t1:.2f}s")
                measure(system, structure_center_absolute_mm, f"Structure_{i:02d}_after", save_folder=path)
            else:
                print(f"Skipping printing program {i:02d}")


if __name__ == '__main__':
    # path = Path(mkdir(f".output/dhm_paper/{datetime.datetime.now():%Y%m%d_%H%M%S}", clean=False))
    path = Path(mkdir(f".output/dhm_paper/20240612", clean=False))
    logger = getLogger(logfile=f"{path}/console_recovery.log")

    main()
