import math
from typing import Optional

import numpy as np

from nanofactorysystem.aerobasic import GalvoLaserOverrideMode
from nanofactorysystem.aerobasic.programs.drawings import DrawableAeroBasicProgram
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Coordinate, Point3D, Point2D


class SingleLine(DrawableAeroBasicProgram):
    def __init__(
            self,
            start: Coordinate,
            end: Coordinate,
            *,
            F: Optional[float] = None,
            E: Optional[float] = None,
            coordinate_system: CoordinateSystem = CoordinateSystem()
    ):
        super().__init__(coordinate_system=coordinate_system)

        self.LINEAR(*start, F=F, E=E)
        self.GALVO_LASER_OVERRIDE(mode=GalvoLaserOverrideMode.ON)
        self.LINEAR(*end, F=F, E=E)
        self.GALVO_LASER_OVERRIDE(mode=GalvoLaserOverrideMode.OFF)


class PolyLine(DrawableAeroBasicProgram):
    def __init__(
            self,
            line: list[Coordinate],
            *,
            F: Optional[float] = None,
            E: Optional[float] = None,
            coordinate_system: CoordinateSystem = CoordinateSystem()
    ):
        super().__init__(coordinate_system=coordinate_system)

        self.LINEAR(**line[0], F=F, E=E)
        self.GALVO_LASER_OVERRIDE(mode=GalvoLaserOverrideMode.ON)
        for point in line[1:]:
            self.LINEAR(**point, F=F, E=E)
        self.GALVO_LASER_OVERRIDE(mode=GalvoLaserOverrideMode.OFF)


class PolyLines(DrawableAeroBasicProgram):
    def __init__(
            self,
            lines: list[list[Coordinate]],
            *,
            F: Optional[float] = None,
            E: Optional[float] = None,
            coordinate_system: CoordinateSystem = CoordinateSystem()
    ):
        super().__init__(coordinate_system=coordinate_system)

        for i, line in enumerate(lines):
            # Start
            self.comment(f"\n[Polyline] - Draw line {i}:")
            poly_line = PolyLine(line, F=F, E=E, coordinate_system=coordinate_system)
            self.add_programm(poly_line)


class Corner(DrawableAeroBasicProgram):
    def __init__(
            self,
            corner_center: Point2D | Point3D,
            length: float,
            width: float,
            height: float,
            hatch_size: float = 0.5,
            layer_height: float = 0.75,
            rotation_degree: float = 0,
            *,
            F: Optional[float] = None,
            E: Optional[float] = None,
            coordinate_system: CoordinateSystem
    ):
        """
                     Length
        \\-----------------   |
        |\\----------------   |
        ||X----------------  Width
        |||\\--------------   |
        ||||\\-------------   |
        |||||
        |||||
        |||||

        :param corner_center: Marked with X
        :param length: Length of corner
        :param width: Width of corner
        :param hatch_size: Distance between lines
        :param rotation_degree: Rotation of corner in degree
        :param F: Velocity used for Linear commands
        :param E: Velocity used for Linear commands
        :param coordinate_system: Used coordinate system
        """
        super().__init__(coordinate_system)
        self.corner_center = corner_center

        n = round(width / hatch_size) + 1
        hatch_corrected = width / (n - 1)

        rotation_rad = rotation_degree / 180 * math.pi
        center_offset = (length - width) / 2
        self.center_point = corner_center + Point2D(center_offset, center_offset).rotate2D(rotation_rad)
        change_start = False
        for z in np.arange(0, height, layer_height):
            poly_lines = self.single_layer(
                corner_center + Point3D(0, 0, z),
                length,
                width,
                n,
                hatch_corrected,
                change_start=change_start,
                E=E,
                F=F,
                rotation_rad=rotation_rad
            )
            change_start = not change_start
            self.add_programm(poly_lines)

    def single_layer(
            self,
            corner_center: Point2D | Point3D,
            length: float,
            width: float,
            n: int,
            hatch: float,
            *,
            change_start: bool = False,
            E: Optional[float] = None,
            F: Optional[float] = None,
            rotation_rad: float = 0
    ) -> PolyLines:
        lines = []
        for i in range(n):
            center_diagonal = -(i - n / 2) * hatch
            offset = length - width / 2

            center_diagonal = Point2D(center_diagonal, center_diagonal)
            offset = Point2D(offset, offset)

            p1 = corner_center + Point2D(X=offset.X, Y=center_diagonal.Y).rotate2D(rotation_rad)
            p2 = corner_center + Point2D(X=center_diagonal.X, Y=center_diagonal.Y).rotate2D(rotation_rad)
            p3 = corner_center + Point2D(X=center_diagonal.X, Y=offset.Y).rotate2D(rotation_rad)

            if (i + change_start) % 2 == 0:
                lines.append([p1.as_dict(), p2.as_dict(), p3.as_dict()])
            else:
                lines.append([p3.as_dict(), p2.as_dict(), p1.as_dict()])
        return PolyLines(lines, F=F, E=E, coordinate_system=self.coordinate_system)


class CornerRectangle(DrawableAeroBasicProgram):
    def __init__(
            self,
            center: Point2D | Point3D,
            rectangle_width: float,
            rectangle_height: float,
            corner_length: float,
            corner_width: float,
            height: float,
            layer_height: float = 0.75,
            hatch_size: float = 0.5,
            # rotation_degree: float,
            *,
            F: Optional[float] = None,
            E: Optional[float] = None,
            coordinate_system: CoordinateSystem
    ):
        super().__init__(coordinate_system)
        tl_corner = Corner(
            center + Point2D(-rectangle_width / 2, -rectangle_height / 2),
            length=corner_length,
            width=corner_width,
            height=height,
            layer_height=layer_height,
            hatch_size=hatch_size,
            rotation_degree=0,
            E=E,
            F=F,
            coordinate_system=coordinate_system
        )
        tr_corner = Corner(
            center + Point2D(rectangle_width / 2, -rectangle_height / 2),
            length=corner_length,
            width=corner_width,
            height=height,
            layer_height=layer_height,
            hatch_size=hatch_size,
            rotation_degree=90,
            E=E,
            F=F,
            coordinate_system=coordinate_system
        )
        bl_corner = Corner(
            center + Point2D(-rectangle_width / 2, rectangle_height / 2),
            length=corner_length,
            width=corner_width,
            height=height,
            layer_height=layer_height,
            hatch_size=hatch_size,
            rotation_degree=270,
            E=E,
            F=F,
            coordinate_system=coordinate_system
        )
        br_corner = Corner(
            center + Point2D(rectangle_width / 2, rectangle_height / 2),
            length=corner_length,
            width=corner_width,
            height=height,
            layer_height=layer_height,
            hatch_size=hatch_size,
            rotation_degree=180,
            E=E,
            F=F,
            coordinate_system=coordinate_system
        )

        self.comment("\nDrawing Top Left corner")
        self.add_programm(tl_corner)
        self.comment("\nDrawing Top Right corner")
        self.add_programm(tr_corner)
        self.comment("\nDrawing Bottom Right corner")
        self.add_programm(br_corner)
        self.comment("\nDrawing Bottom Left corner")
        self.add_programm(bl_corner)
