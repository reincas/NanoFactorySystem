import math
from abc import ABC
from enum import Enum
from typing import Optional, Literal, Iterator

import numpy as np

from nanofactorysystem.aerobasic import GalvoLaserOverrideMode, SingleAxis
from nanofactorysystem.aerobasic.programs.drawings import DrawableAeroBasicProgram, DrawableObject
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Coordinate, Point3D, Point2D


class _Lines(DrawableObject, ABC):
    line_axis: SingleAxis

    def __init__(
            self,
            lines: list[tuple[float, float]],
            secondary_position: dict[str, float],
            *,
            velocity: float,
            acceleration: float,
            acceleration_distance_factor: float = 2
    ):
        super().__init__()
        self._validate_lines(lines)
        self.lines = lines
        self.secondary_position = secondary_position
        self.velocity = velocity
        self.acceleration = acceleration
        self.acceleration_distance_factor = acceleration_distance_factor

    @staticmethod
    def _direction(line_segment) -> Literal[1, -1]:
        return np.sign(line_segment[1] - line_segment[0])

    @staticmethod
    def _validate_lines(lines):
        """ Check whether lines are monoton ascending """
        direction = _Lines._direction(lines[0])
        for i, line in enumerate(lines[1:], start=1):
            if not _Lines._direction(line) == direction:
                raise ValueError(
                    f"Direction mismatch. "
                    f"Line {i} does not match with direction of line 0 ({lines[0]} vs {lines[i]}"
                )

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)

        # Go to start for acceleration
        acceleration_distance = self.acceleration_distance_factor * (self.velocity ** 2) / (2 * self.acceleration)
        start_value = self.lines[0][0] - self._direction(self.lines[0]) * acceleration_distance
        start_position = {self.line_axis.parameter_name: start_value, "F": self.velocity}
        start_position.update(self.secondary_position)
        program.LINEAR(**start_position)

        # Draw lines
        for line_start, line_end in self.lines:
            program.LINEAR(**{self.line_axis.parameter_name: line_start, "F": self.velocity})
            program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.ON)
            program.LINEAR(**{self.line_axis.parameter_name: line_end, "F": self.velocity})
            program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.OFF)

        # Go to end to decelerate
        end_value = self.lines[-1][1] + self._direction(self.lines[0]) * acceleration_distance
        end_position = {self.line_axis.parameter_name: end_value, "F": self.velocity}
        end_position.update(self.secondary_position)
        program.LINEAR(**end_position)

        yield program


class XLines(_Lines):
    line_axis = SingleAxis.X

    def __init__(
            self,
            y: float,
            z: float,
            lines: list[tuple[float, float]],
            *,
            velocity: float,
            acceleration: float
    ):
        super().__init__(lines, {"Y": y, "Z": z}, velocity=velocity, acceleration=acceleration)
        self.y = y
        self.z = z

    def center_point(self) -> Point2D:
        return Point3D((self.lines[0][0] + self.lines[-1][1]) / 2, self.y, self.z)


class YLines(_Lines):
    line_axis = SingleAxis.Y

    def __init__(
            self,
            x: float,
            z: float,
            lines: list[tuple[float, float]],
            *,
            velocity: float,
            acceleration: float
    ):
        super().__init__(lines, {"X": x, "Z": z}, velocity=velocity, acceleration=acceleration)
        self.x = x
        self.z = z

    def center_point(self) -> Point2D:
        return Point3D(self.x, (self.lines[0][0] + self.lines[-1][1]) / 2, self.z)


class PolyLine(DrawableObject):

    def __init__(
            self,
            line: list[Coordinate],
            *,
            F: Optional[float] = None,
            E: Optional[float] = None,
    ):
        super().__init__()
        self.line = line
        self.F = F
        self.E = E

    @property
    def center_point(self) -> Point2D:
        values = {k: [] for k in self.line[0]}
        for coordinate in self.line:
            for k, v in coordinate.items():
                values[k].append(v)
        min_coord = {k: np.min(v) for k, v in values}
        max_coord = {k: np.max(v) for k, v in values}

        center = {k: (min_coord[k] + max_coord[k]) / 2 for k in min_coord}
        try:
            return Point3D(**center)
        except:
            return Point2D(**center)

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)

        program.LINEAR(**self.line[0], F=self.F, E=self.E)
        program.GALVO_LASER_OVERRIDE(mode=GalvoLaserOverrideMode.ON)
        for point in self.line[1:]:
            program.LINEAR(**point, F=self.F, E=self.E)
        program.GALVO_LASER_OVERRIDE(mode=GalvoLaserOverrideMode.OFF)
        yield program


class PolyLines(DrawableObject):

    def __init__(
            self,
            lines: list[list[Coordinate]],
            *,
            F: Optional[float] = None,
            E: Optional[float] = None,
    ):
        super().__init__()
        self.lines = lines
        self.F = F
        self.E = E

    @property
    def center_point(self) -> Point2D:
        values = {k: [] for k in self.lines[0][0]}
        for line in self.lines:
            for coordinate in line:
                for k, v in coordinate.items():
                    values[k].append(v)
        min_coord = {k: np.min(v) for k, v in values}
        max_coord = {k: np.max(v) for k, v in values}

        center = {k: (min_coord[k] + max_coord[k]) / 2 for k in min_coord}
        try:
            return Point3D(**center)
        except:
            return Point2D(**center)

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)
        for i, line in enumerate(self.lines):
            # Start
            program.comment(f"\n[Polyline] - Draw line {i}:")
            poly_line = PolyLine(line, F=self.F, E=self.E)
            program.add_programm(poly_line.draw_on(coordinate_system))

        yield program


class Corner(DrawableObject):
    def __init__(
            self,
            corner_center: Point2D | Point3D,
            length: float,
            width: float,
            height: float,
            hatch_size: float = 0.5,
            slice_size: float = 0.75,
            rotation_degree: float = 0,
            *,
            F: Optional[float] = None,
            E: Optional[float] = None,
            mark: bool = False
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
        """
        super().__init__()
        self.corner_center = corner_center
        self.width = width
        self.hatch_size = hatch_size
        self.length = length
        self.rotation_degree = rotation_degree
        self.rotation_rad = rotation_degree / 180 * math.pi
        self.height = height
        self.slice_size = slice_size
        self.F = F
        self.E = E
        self.mark = mark

    @property
    def center_point(self) -> Point2D:
        center_offset = (self.length - self.width) / 2
        return self.corner_center + Point2D(center_offset, center_offset).rotate2D(self.rotation_rad)

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        n_hatch = round(self.width / self.hatch_size) + 1
        hatch_size_corrected = self.width / (n_hatch - 1)

        for z in np.arange(0, self.height, self.slice_size):
            program = DrawableAeroBasicProgram(coordinate_system)
            program.LINEAR(Z=z+self.corner_center.Z)
            poly_lines = self.single_layer(
                self.corner_center + Point3D(0, 0, z),
                self.length,
                self.width,
                n_hatch,
                hatch_size_corrected,
                E=self.E,
                F=self.F,
                mark=self.mark,
                rotation_rad=self.rotation_rad
            )
            program.add_programm(poly_lines.draw_on(coordinate_system))
            yield program

    # def single_layer_old(
    #         self,
    #         corner_center: Point2D | Point3D,
    #         length: float,
    #         width: float,
    #         n_hatch: int,
    #         hatch_size: float,
    #         *,
    #         E: Optional[float] = None,
    #         F: Optional[float] = None,
    #         rotation_rad: float = 0,
    #         mark: bool = False,
    # ) -> PolyLines:
    #     lines = []
    #     order = 1
    #     for i in range(n_hatch):
    #         center_diagonal = -(i - n_hatch / 2) * hatch_size
    #         offset = length - width / 2
    #         center_diagonal = Point2D(center_diagonal, center_diagonal)
    #         offset = Point2D(offset, offset)
    #         if mark:
    #             p1 = corner_center + Point2D(X=offset.X, Y=center_diagonal.Y).rotate2D(rotation_rad)
    #             p1a = corner_center + Point2D(X=offset.X - width, Y=center_diagonal.Y).rotate2D(rotation_rad)
    #             p1b = corner_center + Point2D(X=offset.X - 2 * width, Y=center_diagonal.Y).rotate2D(rotation_rad)
    #             p2 = corner_center + Point2D(X=center_diagonal.X, Y=center_diagonal.Y).rotate2D(rotation_rad)
    #             p3 = corner_center + Point2D(X=center_diagonal.X, Y=offset.Y).rotate2D(rotation_rad)
    #             if order > 0:
    #                 lines.append([p1.as_dict(), p1a.as_dict()])
    #                 lines.append([p1b.as_dict(), p2.as_dict(), p3.as_dict()])
    #             else:
    #                 lines.append([p3.as_dict(), p2.as_dict(), p1b.as_dict()])
    #                 lines.append([p1a.as_dict(), p1.as_dict()])
    #         else:
    #             p1 = corner_center + Point2D(X=offset.X, Y=center_diagonal.Y).rotate2D(rotation_rad)
    #             p2 = corner_center + Point2D(X=center_diagonal.X, Y=center_diagonal.Y).rotate2D(rotation_rad)
    #             p3 = corner_center + Point2D(X=center_diagonal.X, Y=offset.Y).rotate2D(rotation_rad)
    #             lines.append([p1.as_dict(), p2.as_dict(), p3.as_dict()][::order])
    #         order *= -1
    #     return PolyLines(lines, F=F, E=E)


    def single_layer(
            self,
            corner_center: Point2D | Point3D,
            length: float,
            width: float,
            n_hatch: int,
            hatch_size: float,
            *,
            E: Optional[float] = None,
            F: Optional[float] = None,
            rotation_rad: float = 0,
            mark: bool = False,
    ) -> PolyLines:
        lines = []
        lines_mark = []
        order = 1
        for i in range(n_hatch):
            center_diagonal = -(i - n_hatch / 2) * hatch_size
            offset = length - width / 2
            center_diagonal = Point2D(center_diagonal, center_diagonal)
            offset = Point2D(offset, offset)
            p1_raw = Point2D(X=offset.X, Y=center_diagonal.Y)
            p2_raw = Point2D(X=center_diagonal.X, Y=center_diagonal.Y)
            p3_raw = Point2D(X=center_diagonal.X, Y=offset.Y)
            p1 = corner_center + p1_raw.rotate2D(rotation_rad)
            p2 = corner_center + p2_raw.rotate2D(rotation_rad)
            p3 = corner_center + p3_raw.rotate2D(rotation_rad)
            p1, p2, p3 = [p1, p2, p3][::order]
            lines.append([p1.as_dict(), p2.as_dict(), p3.as_dict()])
            if mark:
                p1_mark = corner_center + (p1_raw + Point2D(0, 2*width)).rotate2D(rotation_rad)
                p2a_mark = corner_center + (p2_raw + Point2D(0, 2*width)).rotate2D(rotation_rad)
                p2b_mark = corner_center + (p2_raw + Point2D(2*width, 0)).rotate2D(rotation_rad)
                p3_mark = corner_center + (p3_raw + Point2D(2*width, 0)).rotate2D(rotation_rad)
                p1_mark, p2a_mark, p2b_mark, p3_mark = [p1_mark, p2a_mark, p2b_mark, p3_mark][::order]
                lines_mark.append([p1_mark.as_dict(), p2a_mark.as_dict()])
                lines_mark.append([p2b_mark.as_dict(), p3_mark.as_dict()])
            order *= -1
        lines += lines_mark
        return PolyLines(lines, F=F, E=E)


# class CornerRectangle(DrawableObject):
#     def __init__(
#             self,
#             center: Point2D | Point3D,
#             rectangle_width: float,
#             rectangle_height: float,
#             corner_length: float,
#             corner_width: float,
#             height: float,
#             slice_height: float = 0.75,
#             hatch_size: float = 0.5,
#             # rotation_degree: float,
#             *,
#             F: Optional[float] = None,
#             E: Optional[float] = None,
#     ):
#         super().__init__()
#         self.center = center
#         self.rectangle_width = rectangle_width
#         self.rectangle_height = rectangle_height
#         self.corner_length = corner_length
#         self.corner_width = corner_width
#         self.height = height
#         self.slice_size = slice_height
#         self.hatch_size = hatch_size
#         self.F = F
#         self.E = E
#
#         self.tl_corner = Corner(
#             center + Point2D(-rectangle_width / 2, -rectangle_height / 2),
#             length=corner_length,
#             width=corner_width,
#             height=height,
#             slice_size=slice_height,
#             hatch_size=hatch_size,
#             rotation_degree=0,
#             E=E,
#             F=F,
#         )
#         self.tr_corner = Corner(
#             center + Point2D(rectangle_width / 2, -rectangle_height / 2),
#             length=corner_length,
#             width=corner_width,
#             height=height,
#             slice_size=slice_height,
#             hatch_size=hatch_size,
#             rotation_degree=90,
#             E=E,
#             F=F,
#         )
#         self.bl_corner = Corner(
#             center + Point2D(-rectangle_width / 2, rectangle_height / 2),
#             length=corner_length,
#             width=corner_width,
#             height=height,
#             slice_size=slice_height,
#             hatch_size=hatch_size,
#             rotation_degree=270,
#             E=E,
#             F=F,
#         )
#         self.br_corner = Corner(
#             center + Point2D(rectangle_width / 2, rectangle_height / 2),
#             length=corner_length,
#             width=corner_width,
#             height=height,
#             slice_size=slice_height,
#             hatch_size=hatch_size,
#             rotation_degree=180,
#             E=E,
#             F=F,
#         )
#
#     @property
#     def center_point(self) -> Point2D:
#         return self.center
#
#     def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
#         program = DrawableAeroBasicProgram(coordinate_system)
#         program.comment("\nDrawing Top Left corner")
#         program.add_programm(self.tl_corner.draw_on(coordinate_system))
#         yield program
#
#         program = DrawableAeroBasicProgram(coordinate_system)
#         program.comment("\nDrawing Top Right corner")
#         program.add_programm(self.tr_corner.draw_on(coordinate_system))
#         yield program
#
#         program = DrawableAeroBasicProgram(coordinate_system)
#         program.comment("\nDrawing Bottom Right corner")
#         program.add_programm(self.br_corner.draw_on(coordinate_system))
#         yield program
#
#         program = DrawableAeroBasicProgram(coordinate_system)
#         program.comment("\nDrawing Bottom Left corner")
#         program.add_programm(self.bl_corner.draw_on(coordinate_system))
#         yield program
#

class VerticalLine(DrawableObject):
    def __init__(self, position: Point2D, z_min: float, z_max: float, *, F: Optional[float] = None):
        super().__init__()
        self.position = position
        self.z_min = z_min
        self.z_max = z_max
        self.F = F

    @property
    def center_point(self) -> Point2D:
        return self.position

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)
        point = self.position.as_dict()
        point["Z"] = self.z_min
        program.LINEAR(**point, F=self.F)
        program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.ON)
        point["Z"] = self.z_max
        program.LINEAR(**point, F=self.F)
        program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.OFF)
        yield program


class HatchingDirection(Enum):
    X = "X"
    Y = "Y"

    def flip(self):
        if self == HatchingDirection.X:
            return HatchingDirection.Y
        return HatchingDirection.X


class Rectangle2D(DrawableObject):

    def __init__(
            self,
            center: Point2D | Point3D,
            width: float,
            length: float,
            *,
            hatch_size: float,
            velocity: float,
            acceleration: float,
            hatching_direction: HatchingDirection
    ):
        super().__init__()
        self.center = center
        self.width = width
        self.length = length

        self.hatch_size = hatch_size
        self.velocity = velocity
        self.acceleration = acceleration
        self.hatching_direction = hatching_direction

    @property
    def center_point(self) -> Point2D:
        return self.center

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)
        bottom_left = self.center - Point2D(self.width / 2, self.length / 2)

        if self.hatching_direction == HatchingDirection.X:
            line_program = XLines
            hatching_start_position = bottom_left.X
            line_start = bottom_left.Y
            line_length = self.length
            hatching_length = self.width
        elif self.hatching_direction == HatchingDirection.Y:
            line_program = YLines
            hatching_start_position = bottom_left.Y
            line_start = bottom_left.X
            line_length = self.width
            hatching_length = self.length
        else:
            raise ValueError(f"HatchingDirection not found: {self.hatching_direction}")

        n_hatch = round(hatching_length / self.hatch_size) + 1
        hatch_size_opt = hatching_length / (n_hatch - 1)

        order = 1
        for i in range(n_hatch):
            line_position = hatching_start_position + i * hatch_size_opt
            lines = [
                [line_start, line_start + line_length][::order]
            ]
            line = line_program(
                line_position,
                z=self.center.Z,
                lines=lines,
                velocity=self.velocity,
                acceleration=self.acceleration
            )
            program.add_programm(line.draw_on(coordinate_system))
            order *= -1

        yield program


class Rectangle3D(DrawableObject):
    def __init__(
            self,
            center: Point2D | Point3D,
            width: float,
            length: float,
            height: float,
            *,
            hatch_size: float,
            slice_size: float,
            velocity: float,
            acceleration: float,
    ):
        super().__init__()
        self.center = center
        self.width = width
        self.length = length
        self.height = height

        self.hatch_size = hatch_size
        self.slice_size = slice_size
        self.velocity = velocity
        self.acceleration = acceleration

    @property
    def center_point(self) -> Point2D:
        return self.center

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)
        if self.height == 0:
            return program

        n_layer = abs(round(self.height / self.slice_size)) + 1
        slice_size_opt = self.height / (n_layer - 1)

        hatching_direction = HatchingDirection.X
        for i in range(n_layer):
            z_offset = i * slice_size_opt
            rectangle = Rectangle2D(
                center=self.center + Point3D(0, 0, z_offset),
                width=self.width,
                length=self.length,
                hatch_size=self.hatch_size,
                velocity=self.velocity,
                acceleration=self.acceleration,
                hatching_direction=hatching_direction
            )
            program = DrawableAeroBasicProgram(coordinate_system)
            program.LINEAR(Z=z_offset+self.center.Z)
            program.add_programm(rectangle.draw_on(coordinate_system))
            yield program
            hatching_direction = hatching_direction.flip()


class Stair(DrawableObject):
    def __init__(
            self,
            center: Point3D,
            n_steps: int,
            step_height: float,
            step_length: float,
            step_width: float,  # same as structure width
            socket_height: float = 0.0,
            *,
            hatch_size: float,
            slice_size: float,
            velocity: float,
            acceleration: float,
    ):
        super().__init__()
        self.center = center
        self.n_steps = n_steps
        self.step_height = step_height
        self.step_length = step_length
        self.step_width = step_width
        self.socket_height = socket_height

        self.hatch_size = hatch_size
        self.slice_size = slice_size
        self.velocity = velocity
        self.acceleration = acceleration

    @property
    def structure_length(self) -> float:
        return self.n_steps * self.step_length

    @property
    def structure_width(self) -> float:
        return self.step_width

    @property
    def structure_height(self) -> float:
        return self.n_steps * self.step_height + self.socket_height

    @property
    def center_point(self) -> Point2D:
        return self.center

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)
        # Add socket
        if self.socket_height > 0:
            socket = Rectangle3D(
                center=self.center,
                width=self.structure_width,
                length=self.structure_length,
                height=self.socket_height,
                hatch_size=self.hatch_size,
                slice_size=self.slice_size,
                velocity=self.velocity,
                acceleration=self.acceleration
            )
            yield from socket.iterate_layers(coordinate_system)

        # Add steps
        slice_size_opt = self.step_height / round(self.step_height / self.slice_size)
        for step in range(self.n_steps):
            z_step_offset = self.socket_height + step * self.step_height
            x_offset = (step / 2) * self.step_length

            step_rectangle = Rectangle3D(
                center=self.center + Point3D(0, -x_offset, z_step_offset),
                width=self.structure_width,
                length=self.structure_length - step * self.step_length,
                height=self.step_height,
                hatch_size=self.hatch_size,
                slice_size=slice_size_opt,
                velocity=self.velocity,
                acceleration=self.acceleration
            )

            yield from step_rectangle.iterate_layers(coordinate_system)

        return program
