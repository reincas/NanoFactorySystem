##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
import datetime
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, Rectangle
from scidatacontainer import Container

from nanofactorysystem import System, ImageContainer, Plane, mkdir, getLogger
from nanofactorysystem.aerobasic import SingleAxis, AxisStatusDataItem
from nanofactorysystem.aerobasic.ascii import AerotechError
from nanofactorysystem.aerobasic.programs import AeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings import DrawableObject
from nanofactorysystem.aerobasic.programs.drawings.lines import CornerRectangle, Stair
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
        plt.savefig(path / "experiment_configuration.png")
        plt.show()
        # TODO: Comment in again maybe
        # if input("Continue with plane fitting? (y/n)") != "y":
        #     return

        # Old Plane-Fitting
        plane_path = path / "plane.zdc"
        if Path(plane_path).exists():
            dc = Container(file=str(plane_path))
        else:
            dc = find_and_log_plane(
                system,
                save_folder=path,
                plane_coordinates=plane_fit_points
            )

        plane_points = dc["meas/result.json"]["lower"]["points"]
        plane_fit_function = PlaneFit.from_points(np.asarray(plane_points))  # in um
        logger.info(plane_fit_function)

        # TODO: Comment in again maybe
        # if input("Plane fitting completed. Continue? (y/n)") != "y":
        #     return

        # Setup system for drawing
        ifov_setup = SetupIFOV()
        system.a3200_new.api(DefaultSetup())
        # system.a3200_new.api(ifov_setup)  # IFOV Setup currently does not work correctly

        # TODO: Make full image of whole scene

        # Define rectangle
        rectangle = CornerRectangle(
            Point3D(0, 0, -2),
            rectangle_width=experiment_configuration.grid_width,
            rectangle_height=experiment_configuration.grid_height,
            corner_width=50,
            corner_length=400,
            height=7,
            hatch_size=0.5,
            slice_height=0.75,
            F=5000
        )

        # Custom drawing on coordinate system specified for each point depending on plane fitting
        rectangle_program = AeroBasicProgram()
        rectangle_program(DefaultSetup())
        coordinate_system_grid_to_absolute = CoordinateSystem(
            offset_x=experiment_configuration.absolute_grid_center[0],
            offset_y=experiment_configuration.absolute_grid_center[1],
            z_function=plane_fit_function,
            drop_direction=DropDirection.DOWN,
            unit=Unit.um
        )

        for corner in [rectangle.tl_corner, rectangle.bl_corner, rectangle.br_corner, rectangle.tr_corner]:
            corner_center = corner.center_point
            z_offset = coordinate_system_grid_to_absolute.convert(corner_center.as_dict())["Z"]

            coordinate_system = CoordinateSystem(
                offset_x=experiment_configuration.absolute_grid_center[0],
                offset_y=experiment_configuration.absolute_grid_center[1],
                z_function=z_offset / Unit.um.value,
                drop_direction=DropDirection.DOWN,
                unit=Unit.um
            )
            coordinate_system_galvo = CoordinateSystem(
                offset_x=-corner_center.X,
                offset_y=-corner_center.Y,
                z_function=z_offset / Unit.um.value,
                drop_direction=DropDirection.DOWN,
                unit=Unit.um
            )
            coordinate_system_galvo.axis_mapping = {"X": "A", "Y": "B"}
            rectangle_program.LINEAR(**coordinate_system.convert(corner_center.as_dict()))
            rectangle_program.add_programm(corner.draw_on(coordinate_system_galvo))

        # Make tr corner thicker
        corner = rectangle.tr_corner
        z_offset = coordinate_system_grid_to_absolute.convert(corner.center_point.as_dict())["Z"]
        coordinate_system = CoordinateSystem(
            offset_x=experiment_configuration.absolute_grid_center[0] + corner.width * 2,
            offset_y=experiment_configuration.absolute_grid_center[1] - corner.width * 2,
            z_function=z_offset / Unit.um.value,
            drop_direction=DropDirection.DOWN,
            unit=Unit.um
        )

        coordinate_system_galvo = CoordinateSystem(
            offset_x=-corner.center_point.X,
            offset_y=-corner.center_point.Y,
            z_function=z_offset / Unit.um.value,
            drop_direction=DropDirection.DOWN,
            unit=Unit.um
        )
        coordinate_system_galvo.axis_mapping = {"X": "A", "Y": "B"}
        rectangle_program.LINEAR(**coordinate_system.convert(corner.center_point.as_dict()))

        rectangle_program.add_programm(corner.draw_on(coordinate_system_galvo))

        # Calibrate in center
        image_center = coordinate_system_grid_to_absolute.convert(rectangle.center_point.as_dict())

        # TODO: Comment in again maybe
        # if input(f"Drive to image center: {image_center}? (y/n)") != "y":
        #     return

        # Calibrate DHM
        a3200_new.api.LINEAR(**image_center, F=2)  # Slower, as we also move in z direction and it is scary

        # TODO: Comment in, but only once.
        optImageMedian(system.dhm, vmedian=32, logger=logger)
        m = system.dhm.motorscan()
        logger.info(f"Motor pos at {image_center}: {system.dhm.device.MotorPos:.1f} µm (set: {m:.1f} µm)")

        measure(system, image_center, "before", save_folder=path)

        pgm_file = path / "programs" / "corners.txt"

        rectangle_program.write(pgm_file)
        movements = read_file(pgm_file)
        system.log.info("Plot corners")
        # TODO: COrners wieder plotten
        plot_movements(movements)
        plt.savefig(path / "programs" / "corners.png")
        plt.close()
        # if input("Execute movements to draw corners (y/n): ") == "y":
        # TODO: Make optional again
        t1 = time.time()
        task = a3200_new.run_program_as_task(pgm_file, task_id=1)
        print("\n".join(map(str, a3200_new.api.history)))
        task.wait_to_finish()
        task.finish()

        t2 = time.time()
        logger.info(f"Making corner took {t2 - t1:.2f}s")

        a_mm_x = float(a3200_new.api.AXISSTATUS(SingleAxis.X, AxisStatusDataItem.AccelerationRate).replace(",", "."))
        a_mm_galvo = float(
            a3200_new.api.AXISSTATUS(SingleAxis.A, AxisStatusDataItem.AccelerationRate).replace(",", "."))
        a_um_x = a_mm_x / Unit.um.value
        a_um_galvo = a_mm_galvo / Unit.um.value
        velocity = 5000

        structures: list[DrawableObject] = [
            # SphericalLens(
            #     Point3D(0, 0, -2),
            #     5,
            #     50,
            #     0.2,
            #     circle_object_factory=FilledCircle2D.as_circle_factory(velocity),
            #     hatch_size=0.1,
            #     velocity=velocity
            # ),
            # SphericalLens(
            #     Point3D(0, 0, -2),
            #     5,
            #     50,
            #     0.2,
            #     circle_object_factory=LineCircle2D.as_circle_factory(acceleration=a_um, velocity=velocity),
            #     hatch_size=0.1,
            #     velocity=velocity
            # ),
            # Cylinder(
            #     Point3D(0, 0, -2),
            #     10,
            #     3,
            #     0.2,
            #     circle_object_factory=LineCircle2D.as_circle_factory(acceleration=a_um, velocity=velocity),
            #     hatch_size=0.1,
            #     velocity=velocity
            # ),
            # Cylinder(
            #     Point3D(0, 0, -2),
            #     10,
            #     3,
            #     0.2,
            #     circle_object_factory=FilledCircle2D.as_circle_factory(velocity),
            #     hatch_size=0.1,
            #     velocity=velocity
            # ),
            # # Cylinder(
            # #     Point3D(0, 0, -2),
            # #     10,
            # #     3,
            # #     0.2,
            # #     circle_object_factory=Spiral2D.as_circle_factory(velocity),
            # #     hatch_size=0.1,
            # #     velocity=velocity
            # # ),
            Stair(
                Point3D(0, 0, -2),
                n_steps=6,
                step_height=0.6,
                step_length=20,
                step_width=50,
                hatch_size=0.125,
                slice_size=0.3,
                socket_height=7,
                velocity=velocity,
                acceleration=a_um_galvo
            )
        ]

        structures = [Stair(
            Point3D(0, 0, -2),
            n_steps=6,
            step_height=0.6,
            step_length=20,
            step_width=50,
            hatch_size=0.125,
            slice_size=0.3,
            socket_height=7,
            velocity=velocity,
            acceleration=a_um_galvo
        )] * 28

        structure_programs = []
        structure_configs = []
        for i, ((x, y), structure) in enumerate(zip(experiment_configuration.iter_experiment_locations(), structures)):
            system.log.info(f"Creating program for structure {i:02d}: {structure}")

            # Create program
            z_offset = plane_fit_function(x, y)
            structure_center_absolute_um = {
                "X": x,
                "Y": y,
                "Z": z_offset
            }
            structure_center_absolute_mm = {k: v * Unit.um.value for k, v in structure_center_absolute_um.items()}

            coordinate_system = CoordinateSystem(
                offset_x=structure_center_absolute_um["X"],
                offset_y=structure_center_absolute_um["Y"],
                z_function=structure_center_absolute_um["Z"],
                unit=Unit.um
            )
            coordinate_system_galvo = CoordinateSystem(
                offset_x=0,
                offset_y=0,
                z_function=structure_center_absolute_um["Z"],
                unit=Unit.um
            )
            coordinate_system_galvo.axis_mapping = {"X": "A", "Y": "B"}

            program = DefaultSetup() + structure.draw_on(coordinate_system_galvo)
            structure_pgm_file = path / "programs" / f"structure_{i:02d}.txt"
            program.write(structure_pgm_file)
            structure_programs.append(structure_pgm_file)

            # Create configs
            assert isinstance(structure, DrawableObject)
            structure_configs.append({
                "index": i,
                "x": x,
                "y": y,
                "structure": structure.to_json(),
                "program_file": str(structure_pgm_file.absolute())
            })

            # Plot
            # TODO: Add plotting again
            movements = read_file(structure_pgm_file)
            system.log.info(f"Plot structure {i:02d}")
            plot_movements(movements)
            plt.savefig(path / "programs" / f"structure {i:02d}.png")
            plt.close()

        (path / "structures.json").write_text(json.dumps(structure_configs, indent=4))

        # if input("Continue to print structures? (y/n)") != "y":
        #     return

        for i, (structure_program, (x, y)) in enumerate(zip(
                structure_programs,
                experiment_configuration.iter_experiment_locations()
        )):
            system.log.info(f"Printing structure {i:02d}: {structure}")
            structure_center_absolute_mm = {"X": x / 1000, "Y": y / 1000}

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

        measure(system, image_center, "after", save_folder=path)


if __name__ == '__main__':
    # path = Path(mkdir(f".output/dhm_paper/{datetime.datetime.now():%Y%m%d_%H%M%S}", clean=False))
    path = Path(mkdir(f".output/dhm_paper/{datetime.datetime.now():%Y%m%d}", clean=False))
    logger = getLogger(logfile=f"{path}/console.log")

    main()
