##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
import datetime
import json
import time
import re
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox
from typing import Callable, Optional, Literal, Iterator

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, Rectangle
from scidatacontainer import Container

from mains.parameter_search_structure import structure_building
from nanofactorysystem import System, ImageContainer, Plane, mkdir, getLogger
from nanofactorysystem.aerobasic import SingleAxis, AxisStatusDataItem
from nanofactorysystem.aerobasic.ascii import AerotechError
from nanofactorysystem.aerobasic.programs import AeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings import DrawableObject, DrawableAeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.lines import Stair, Corner  # , CornerRectangle
from nanofactorysystem.aerobasic.programs.setups import DefaultSetup
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, PlaneFit, DropDirection, Unit, \
    Point2D, Point3D, Coordinate
from nanofactorysystem.dhm.optimage import optImageMedian
from nanofactorysystem.utils.visualization import read_file, plot_movements

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
        """ Return experiment locations in um """
        for i in range(self.grid[0]):
            for j in range(self.grid[1]):
                rect_x = self.rectangle_tl[0] + self.margin + j * (self.fov_size + self.padding)
                rect_y = self.rectangle_tl[1] + self.margin + i * (self.fov_size + self.padding)
                yield rect_x + self.fov_size / 2, rect_y + self.fov_size / 2

    def structure_location(self, index) -> Point2D:
        i, j = divmod(index, self.grid[0])
        rect_x = self.rectangle_tl[0] + self.margin + j * (self.fov_size + self.padding)
        rect_y = self.rectangle_tl[1] + self.margin + i * (self.fov_size + self.padding)
        return Point2D(rect_x + self.fov_size / 2, rect_y + self.fov_size / 2)

    def corner_location(self, position: Literal["tl", "tr", "bl", "br"]) -> Point2D:
        if position == "tl":
            point = self.rectangle_tl
        elif position == "tr":
            point = self.rectangle_tr
        elif position == "bl":
            point = self.rectangle_bl
        elif position == "br":
            point = self.rectangle_br
        else:
            raise ValueError(f'Unknown position string "{position}"')
        return Point2D(*point)

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
        return np.asarray([
            self.absolute_grid_center[0] - self.center_point[0],
            self.absolute_grid_center[1] - self.center_point[1]
        ]
        )

    @property
    def grid_width(self) -> float:
        return self.grid[1] * (self.fov_size + self.padding) - self.padding + 2 * self.margin

    @property
    def grid_height(self) -> float:
        return self.grid[0] * (self.fov_size + self.padding) - self.padding + 2 * self.margin

    @property
    def rectangle_tl(self) -> np.ndarray:
        return self.center_point + self.grid_center - [self.grid_width / 2, self.grid_height / 2]

    @property
    def rectangle_br(self) -> np.ndarray:
        return self.center_point + self.grid_center + [self.grid_width / 2, self.grid_height / 2]

    @property
    def rectangle_tr(self) -> np.ndarray:
        return self.center_point + self.grid_center + [self.grid_width / 2, -self.grid_height / 2]

    @property
    def rectangle_bl(self) -> np.ndarray:
        return self.center_point + self.grid_center + [-self.grid_width / 2, self.grid_height / 2]

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

    def sample_points_for_plane_fitting(self, n_mid_points: 2) -> list[tuple[float, float]]:
        tl = self.rectangle_tl + self.margin / 2
        br = self.rectangle_br - self.margin / 2
        points = set()
        for x in np.linspace(tl[0], br[0], n_mid_points + 2):
            points.add((x, tl[1]))
            points.add((x, br[1]))

        for y in np.linspace(tl[1], br[1], n_mid_points + 2):
            points.add((tl[0], y))
            points.add((br[0], y))

        return list(points)

def find_and_log_plane(
        system: System,
        path: Path,
        *,
        plane_coordinates: list[tuple[float, float]],
        drop_direction: DropDirection,
        force: bool = False
) -> PlaneFit:
    logger = system.log
    plane_path = Path(path) / "plane.zdc"

    if not force and plane_path.exists():
        logger.info("Load plane detection results...")
        dc = Container(file=str(plane_path))

    else:
        # Plane needs micrometer coordinates
        zlo = zup = system.z0
        plane = Plane(zlo, zup, system, logger, **args)

        logger.info("Store background image...")
        plane.layer.focus.imgBack.write(str(path / "back.zdc"))

        logger.info("Run plane detection...")
        for x, y in plane_coordinates:
            plane.run(x, y, path=path)

        logger.info("Store plane detection results...")
        dc = plane.container()
        dc.write(str(path / "plane.zdc"))

    if drop_direction == DropDirection.DOWN:
        plane_points = dc["meas/result.json"]["lower"]["points"]
    else:
        plane_points = dc["meas/result.json"]["upper"]["points"]
    plane_fit_function = PlaneFit.from_points(np.asarray(plane_points))  # in um
    logger.info(str(plane_fit_function))
    logger.info("Done.")
    return plane_fit_function


def find_and_log_opl(
        system: System,
        image_center: Point2D,
        path: Path,
        *,
        m0: float = None,
        force: bool = False):
    logger = system.log
    opl_path = Path(path) / "opl.txt"
    if not force and opl_path.exists():
        with open(opl_path, "r") as fp:
            m0 = float(fp.readline())
        logger.info(f"Retrieved OPL motor pos {m0:.1f} µm")
    else:
        m0 = system.dhm.motorscan(m0)
        logger.info(f"OPL motor pos at {image_center}: {system.dhm.device.MotorPos:.1f} µm (set: {m0:.1f} µm)")
        with open(opl_path, "w") as fp:
            fp.write(str(m0))
    return m0


def corner_list(
        center: Point2D | Point3D,
        corner_length: float,
        corner_width: float,
        height: float,
        slice_height: float,
        hatch_size: float,
        *,
        F: Optional[float] = None,
        E: Optional[float] = None,
) -> list[tuple[str, DrawableObject]]:
    corners = []

    # Top-right corner (marked)
    corners.append(("corner_tr", "ABZ", Corner(
        center,
        length=corner_length,
        width=corner_width,
        height=height,
        slice_size=slice_height,
        hatch_size=hatch_size,
        rotation_degree=90,
        E=E,
        F=F,
        mark=True,
    )))

    # Top-left corner
    corners.append(("corner_tl", "ABZ", Corner(
        center,
        length=corner_length,
        width=corner_width,
        height=height,
        slice_size=slice_height,
        hatch_size=hatch_size,
        rotation_degree=0,
        E=E,
        F=F,
        mark=False,
    )))

    # Bottom-left corner
    corners.append(("corner_bl", "ABZ", Corner(
        center,
        length=corner_length,
        width=corner_width,
        height=height,
        slice_size=slice_height,
        hatch_size=hatch_size,
        rotation_degree=270,
        E=E,
        F=F,
        mark=False,
    )))

    # Bottom-right corner
    corners.append(("corner_br", "ABZ", Corner(
        center,
        length=corner_length,
        width=corner_width,
        height=height,
        slice_size=slice_height,
        hatch_size=hatch_size,
        rotation_degree=180,
        E=E,
        F=F,
        mark=False,
    )))

    return corners


def structure_list(low_speed_um, accel_x_um, high_speed_um, accel_a_um) -> list[tuple[str, DrawableObject]]:
    structures = []

    # structures.append(SphericalLens(
    #     Point3D(0, 0, -2),
    #     5,
    #     50,
    #     0.2,
    #     circle_object_factory=FilledCircle2D.as_circle_factory(velocity),
    #     hatch_size=0.1,
    #     velocity=velocity
    # ))
    #
    # structures.append(SphericalLens(
    #     Point3D(0, 0, -2),
    #     5,
    #     50,
    #     0.2,
    #     circle_object_factory=LineCircle2D.as_circle_factory(acceleration=a_um, velocity=velocity),
    #     hatch_size=0.1,
    #     velocity=velocity
    # ))
    #
    # structures.append(Cylinder(
    #     Point3D(0, 0, -2),
    #     10,
    #     3,
    #     0.2,
    #     circle_object_factory=LineCircle2D.as_circle_factory(acceleration=a_um, velocity=velocity),
    #     hatch_size=0.1,
    #     velocity=velocity
    # ))
    #
    # structures.append(Cylinder(
    #     Point3D(0, 0, -2),
    #     10,
    #     3,
    #     0.2,
    #     circle_object_factory=FilledCircle2D.as_circle_factory(velocity),
    #     hatch_size=0.1,
    #     velocity=velocity
    # ))
    #
    # structures.append(Cylinder(
    #     Point3D(0, 0, -2),
    #     10,
    #     3,
    #     0.2,
    #     circle_object_factory=Spiral2D.as_circle_factory(velocity),
    #     hatch_size=0.1,
    #     velocity=velocity
    # ))

    structures.append(("stair_0", "ABZ",
                       Stair(
                           Point3D(0, 0, -2),
                           n_steps=6,
                           step_height=0.6,
                           step_length=20,
                           step_width=50,
                           hatch_size=0.125,
                           slice_size=0.3,
                           socket_height=7,
                           velocity=2000,
                           acceleration=accel_a_um,
                       )))

    structures.append(("stair_1", "XYZ",
                       Stair(
                           Point3D(0, 0, -2),
                           n_steps=6,
                           step_height=0.6,
                           step_length=20,
                           step_width=50,
                           hatch_size=0.125,
                           slice_size=0.3,
                           socket_height=7,
                           velocity=300,
                           acceleration=accel_x_um,
                       )))

    return structures


def measure(
        system: System,
        coordinate: Coordinate, name: str,
        *,
        save_folder: Path
) -> tuple[Container, ImageContainer]:
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


def measurement_factory(
        system: System,
        coordinate: Coordinate,
        name: str,
        *,
        save_folder: Path
) -> Callable[[int], None]:
    """
    Coordinate in mm in absolute coordinates
    """

    def do_measurement(layer_id: int):
        # DHM Image before
        system.a3200_new.api.LINEAR(**coordinate, F=20)
        dhm_container = system.dhm.container(opt=True)
        fn = save_folder / f"hologram_{name}.{layer_id}.zdc"
        logger.info(f"Store hologram container file '{fn}'")
        dhm_container.write(fn)

        # Camera Image before
        system.a3200_new.api.LINEAR(**coordinate, F=20)
        camera_container = system.getimage()
        assert isinstance(camera_container, ImageContainer)
        camera_container.write(str(path / f"camera_{name}.{layer_id}.zdc"))
        print(f"Location: {camera_container.location}")
        return None

    return do_measurement


def structure_program(
        log,
        x: float,
        y: float,
        structure: DrawableObject,
        name: str,
        printing_axes: str,
        plane_fit_function):
    log.info(f"Creating layer programs for {name}: {structure}")
    assert isinstance(structure, DrawableObject)

    # Absolute center coordinates
    offset_x = structure.center_point.X
    offset_y = structure.center_point.Y
    z = plane_fit_function(x, y)
    structure_center_absolute_um = {
        "X": x + offset_x,
        "Y": y + offset_y,
        "Z": z,
    }
    structure_center_absolute_mm = {k: v * Unit.um.value for k, v in structure_center_absolute_um.items()}

    # Coordinate systems of stages and galvo scanner
    coordinate_system_stage = CoordinateSystem(
        offset_x=structure_center_absolute_um["X"],
        offset_y=structure_center_absolute_um["Y"],
        z_function=structure_center_absolute_um["Z"],
        unit=Unit.um
    )
    coordinate_system_galvo = CoordinateSystem(
        offset_x=-offset_x,
        offset_y=-offset_y,
        z_function=structure_center_absolute_um["Z"],
        unit=Unit.um
    )
    coordinate_system_galvo.axis_mapping = {"X": "A", "Y": "B"}

    # Generate structure and layer programs
    if printing_axes == "ABZ":
        coordinate_system = coordinate_system_galvo
    else:
        coordinate_system = coordinate_system_stage
    structure_pgm = DrawableAeroBasicProgram(coordinate_system)
    layer_pgm_paths = []
    x_center = structure_center_absolute_mm["X"]
    y_center = structure_center_absolute_mm["Y"]
    for layer_id, layer in enumerate(structure.iterate_layers(coordinate_system)):
        # AeroBasic program for given layer
        layer_pgm = AeroBasicProgram()
        layer_pgm.LINEAR(X=x_center, Y=y_center)  # move to reference point for galvo scanner
        layer_pgm.add_programm(layer)

        # Store layer program file
        layer_pgm_path = path / "programs" / "layers" / f"{name}.{layer_id:03d}.txt"
        layer_pgm.write(layer_pgm_path)
        layer_pgm_paths.append(str(layer_pgm_path))

        # Add layer program to structure program
        structure_pgm.add_programm(layer_pgm)

    # Store structure program file
    structure_pgm_path = path / "programs" / f"{name}.full.txt"
    structure_pgm.write(structure_pgm_path)

    # Structure configuration
    structure_config = {
        "name": name,
        "center_x": structure_center_absolute_um["X"],
        "center_y": structure_center_absolute_um["Y"],
        "center_z": structure_center_absolute_um["Z"],
        "structure": structure.to_json(),
        "program_file": str(structure_pgm_path),
        "layer_files": layer_pgm_paths,
    }

    # Plot structure to image file
    log.info(f"Plotting {name}")
    movements = read_file(structure_pgm_path)
    plot_movements(movements)
    plt.savefig(path / "programs" / f"{name}.png")
    plt.close()

    # Done
    return layer_pgm_paths, structure_config


def print_structure(
        system,
        pgm_files_list: list[Path],
        x: float,  # um
        y: float,  # um
        name: str,
        *,
        change_power: Optional[float] = None
):
    system.log.info(f"Printing {name}")
    structure_center_absolute_mm = {"X": x / 1000, "Y": y / 1000}

    if change_power is not None and change_power < 1:  # safety reasons - not to much power ToDo(hrobben): change in future
        system.controller.power(change_power)

    measure(system, structure_center_absolute_mm, f"{name}_before", save_folder=path)
    t1 = time.time()
    for layer_id, layer_pgm_path in enumerate(pgm_files_list):
        try:
            task = system.a3200_new.run_program_as_task(layer_pgm_path, task_id=1)
            task.wait_to_finish()
            task.finish()
            measure(system, structure_center_absolute_mm, layer_pgm_path.name.replace(".txt", ""), save_folder=path)
        except AerotechError as e:
            logger.error(f"Program failed for {name}: {e}")
    t2 = time.time()
    logger.info(f"Making {name} took {t2 - t1:.2f}s")
    measure(system, structure_center_absolute_mm, f"{name}_after", save_folder=path)


def main(logger, path):
    user = "Hannes"
    objective = "Zeiss 20x"

    logger.info("Initialize system object...")
    with (System(user, objective, logger, **args) as system):
        logger.info("Initialize plane object...")

        # Size of (oval) resin drop
        # TODO: Determine automatically
        right_edge = [-600, 10850]
        left_edge = [200, 26900]
        front_edge = [-6500, 17750]
        far_edge = [6400, 19550]
        edges = np.asarray([right_edge, left_edge, far_edge, front_edge])

        # Configure experiment
        grid_center = Point2D(0, 21000)
        experiment_configuration = ExperimentConfiguration(
            resin_corner_bl=np.min(edges, axis=0),  # um
            resin_corner_tr=np.max(edges, axis=0),  # um
            fov_size=500,
            margin=200,
            padding=100,
            absolute_grid_center=grid_center.as_tuple(),
            grid=(8, 3),  # (4, 7) # Rows, Cols
        )
        plane_fit_points = experiment_configuration.sample_points_for_plane_fitting(n_mid_points=5)
        logger.info(experiment_configuration)

        # Set laser power
        system.controller.power(0.7)

        # Setup system for drawing
        a3200_new = system.a3200_new
        a3200_new.api(DefaultSetup())

        # Visualize experiment
        experiment_configuration.plot(plane_fit_points)
        plt.savefig(path / "experiment_configuration.png")
        plt.show()

        # Get substrate surface plane
        if not messagebox.askyesno(message="Run plane fitting?"): return
        plane_fit_function = find_and_log_plane(
            system,
            path,
            plane_coordinates=plane_fit_points,
            drop_direction=DropDirection.DOWN,
            force=False
        )

        # Global coordinate system
        coordinate_system_grid_to_absolute = CoordinateSystem(
            offset_x=experiment_configuration.absolute_grid_center[0],
            offset_y=experiment_configuration.absolute_grid_center[1],
            z_function=plane_fit_function,
            drop_direction=DropDirection.DOWN,
            unit=Unit.um
        )

        # Optical path length for DHM
        if not messagebox.askyesno(message="Run OPL motor scan?"): return
        image_center = coordinate_system_grid_to_absolute.convert({"X": 0, "Y": 0, "Z": 0})
        a3200_new.api.LINEAR(**image_center, F=2)  # Slower, as we also move in z direction and it is scary
        m0 = 3847.0
        m0 = find_and_log_opl(system, grid_center, path, m0=m0, force=False)
        system.dhm.device.MotorPos = m0

        # TODO: Make full image of whole scene
        # measure(system, image_center, "before", save_folder=path)

        # Acceleration rates of stages and galvanometer
        accel_x_mm = float(
            a3200_new.api.AXISSTATUS(SingleAxis.X, AxisStatusDataItem.AccelerationRate).replace(",", "."))
        accel_a_mm = float(
            a3200_new.api.AXISSTATUS(SingleAxis.A, AxisStatusDataItem.AccelerationRate).replace(",", "."))
        accel_x_um = accel_x_mm / Unit.um.value
        accel_a_um = accel_a_mm / Unit.um.value

        # Writing speeds
        low_speed_um = 1000
        high_speed_um = 5000

        # List of drawable objects of corners and structures
        structures = corner_list(
            Point3D(0, 0, -2),
            corner_width=50,
            corner_length=300,
            height=7,
            hatch_size=0.5,
            slice_height=0.75,
            F=high_speed_um)
        # structures = structure_building(low_speed_um, accel_x_um, high_speed_um, accel_a_um)

        # Build corner and structure programs
        if not messagebox.askyesno(message="Create corner and structure programs?"): return
        structure_programs = []
        structure_configs = []
        structure_id = 0
        for name, printing_axes, structure in structures:
            system.log.info(f"Creating program for {name}: {structure}")
            if re.match("corner_[tb][lr]", name):
                position_str = name[-2:]
                x, y = experiment_configuration.corner_location(position_str).as_tuple()
            else:
                x, y = experiment_configuration.structure_location(structure_id).as_tuple()
                structure_id += 1

            paths, config = structure_program(
                system.log,
                x, y,
                structure, name, printing_axes,
                plane_fit_function)
            structure_programs.append(paths)
            structure_configs.append(config)
        structure_configs_path = path / "structures.json"
        structure_configs_path.write_text(json.dumps(structure_configs, indent=4))

        # Print corners and structures
        if not messagebox.askyesno(message="Print corners and structures?"): return
        for structure_config in structure_configs:
            layer_pgm_paths = [Path(p) for p in structure_config["layer_files"][::-1]]
            if re.match("parameter_power_3_[xa]", structure_config["name"]):
                print_structure(
                    system,
                    layer_pgm_paths,
                    x=structure_config["center_x"],
                    y=structure_config["center_y"],
                    name=structure_config["name"],
                    change_power=0.3
                )
            elif re.match("parameter_power_5_[xa]", structure_config["name"]):
                print_structure(
                    system,
                    layer_pgm_paths,
                    x=structure_config["center_x"],
                    y=structure_config["center_y"],
                    name=structure_config["name"],
                    change_power=0.5
                )
            else:
                print_structure(
                    system,
                    layer_pgm_paths,
                    x=structure_config["center_x"],
                    y=structure_config["center_y"],
                    name=structure_config["name"]
                )

        # TODO: Make full image of whole scene
        # measure(system, image_center, "after", save_folder=path)


if __name__ == '__main__':
    # path = Path(mkdir(f".output/dhm_paper/{datetime.datetime.now():%Y%m%d_%H%M%S}", clean=False))
    # path = Path(mkdir(f".output/dhm_paper/{datetime.datetime.now():%Y%m%d}_parameter", clean=False))
    path = Path(mkdir(f".output/dhm_paper/20240618_parameter", clean=False))
    logger = getLogger(logfile=f"{path}/console.log")

    main(logger, path)
