import math
from abc import ABC
from enum import Enum
from typing import Optional, Literal

import numpy as np

from nanofactorysystem.aerobasic import GalvoLaserOverrideMode, SingleAxis
from nanofactorysystem.aerobasic.programs.drawings import DrawableAeroBasicProgram, DrawableObject
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Coordinate, Point3D, Point2D


class SingleLine(DrawableObject):
    def __init__(
            self,
            start: Coordinate,
            end: Coordinate,
            *,
            F: Optional[float] = None,
            E: Optional[float] = None,
    ):
        super().__init__()
        self.start = start
        self.end = end
        self.F = F
        self.E = E

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)

        program.LINEAR(*self.start, F=self.F, E=self.E)
        program.GALVO_LASER_OVERRIDE(mode=GalvoLaserOverrideMode.ON)
        program.LINEAR(*self.end, F=self.F, E=self.E)
        program.GALVO_LASER_OVERRIDE(mode=GalvoLaserOverrideMode.OFF)
        return program


class _Lines(DrawableObject, ABC):
    line_axis: SingleAxis

    def __init__(
            self,
            lines: list[tuple[float, float]],
            secondary_position: dict[str, float],
            *,
            velocity: float,
            acceleration: float
    ):
        super().__init__()
        self._validate_lines(lines)
        self.lines = lines
        self.secondary_position = secondary_position
        self.velocity = velocity
        self.acceleration = acceleration

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

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)

        # Go to start for acceleration
        acceleration_distance = (self.velocity ** 2) / (2 * self.acceleration)
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

        return program


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

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)

        program.LINEAR(**self.line[0], F=self.F, E=self.E)
        program.GALVO_LASER_OVERRIDE(mode=GalvoLaserOverrideMode.ON)
        for point in self.line[1:]:
            program.LINEAR(**point, F=self.F, E=self.E)
        program.GALVO_LASER_OVERRIDE(mode=GalvoLaserOverrideMode.OFF)
        return program


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

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)
        for i, line in enumerate(self.lines):
            # Start
            program.comment(f"\n[Polyline] - Draw line {i}:")
            poly_line = PolyLine(line, F=self.F, E=self.E)
            program.add_programm(poly_line.draw_on(coordinate_system))

        return program


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

    @property
    def center_point(self) -> Point2D:
        center_offset = (self.length - self.width) / 2
        return self.corner_center + Point2D(center_offset, center_offset).rotate2D(self.rotation_rad)

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)
        n = round(self.width / self.hatch_size) + 1
        hatch_corrected = self.width / (n - 1)

        change_start = False
        for z in np.arange(0, self.height, self.slice_size):
            poly_lines = self.single_layer(
                self.corner_center + Point3D(0, 0, z),
                self.length,
                self.width,
                n,
                hatch_corrected,
                change_start=change_start,
                E=self.E,
                F=self.F,
                rotation_rad=self.rotation_rad
            )
            change_start = not change_start
            program.add_programm(poly_lines.draw_on(coordinate_system))

        return program

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
        return PolyLines(lines, F=F, E=E)


class CornerRectangle(DrawableObject):
    def __init__(
            self,
            center: Point2D | Point3D,
            rectangle_width: float,
            rectangle_height: float,
            corner_length: float,
            corner_width: float,
            height: float,
            slice_height: float = 0.75,
            hatch_size: float = 0.5,
            # rotation_degree: float,
            *,
            F: Optional[float] = None,
            E: Optional[float] = None,
    ):
        super().__init__()
        self.center = center
        self.rectangle_width = rectangle_width
        self.rectangle_height = rectangle_height
        self.corner_length = corner_length
        self.corner_width = corner_width
        self.height = height
        self.slice_size = slice_height
        self.hatch_size = hatch_size
        self.F = F
        self.E = E

        self.tl_corner = Corner(
            center + Point2D(-rectangle_width / 2, -rectangle_height / 2),
            length=corner_length,
            width=corner_width,
            height=height,
            slice_size=slice_height,
            hatch_size=hatch_size,
            rotation_degree=0,
            E=E,
            F=F,
        )
        self.tr_corner = Corner(
            center + Point2D(rectangle_width / 2, -rectangle_height / 2),
            length=corner_length,
            width=corner_width,
            height=height,
            slice_size=slice_height,
            hatch_size=hatch_size,
            rotation_degree=90,
            E=E,
            F=F,
        )
        self.bl_corner = Corner(
            center + Point2D(-rectangle_width / 2, rectangle_height / 2),
            length=corner_length,
            width=corner_width,
            height=height,
            slice_size=slice_height,
            hatch_size=hatch_size,
            rotation_degree=270,
            E=E,
            F=F,
        )
        self.br_corner = Corner(
            center + Point2D(rectangle_width / 2, rectangle_height / 2),
            length=corner_length,
            width=corner_width,
            height=height,
            slice_size=slice_height,
            hatch_size=hatch_size,
            rotation_degree=180,
            E=E,
            F=F,
        )

    @property
    def center_point(self) -> Point2D:
        return self.center

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)

        program.comment("\nDrawing Top Left corner")
        program.add_programm(self.tl_corner.draw_on(coordinate_system))
        program.comment("\nDrawing Top Right corner")
        program.add_programm(self.tr_corner.draw_on(coordinate_system))
        program.comment("\nDrawing Bottom Right corner")
        program.add_programm(self.br_corner.draw_on(coordinate_system))
        program.comment("\nDrawing Bottom Left corner")
        program.add_programm(self.bl_corner.draw_on(coordinate_system))
        return program


class Rectangle2DHannes(DrawableObject):
    def __init__(
            self,
            bottom_left: Point2D | Point3D,
            width: float,
            length: float,
            *,
            hatch_size: float,
            velocity: float,
            acceleration: float
    ):
        super().__init__()
        self.bottom_left = bottom_left
        self.width = width
        self.length = length

        self.hatch_size = hatch_size
        self.velocity = velocity
        self.acceleration = acceleration
        self.end_point_layer = None
        self.opposite_end_position = False  # False - top | True - bottom

        self.starting_point = None
        self.hatching_direction = None

    # ToDo Mehtoden überschreiben und Rectangle 3D umschreiben mit rectangle 2D :)

    @property
    def center_point(self) -> Point2D:
        return self.bottom_left + Point2D(self.width / 2, self.length / 2)

    def calc_points_layer(
            self,
            hatching_direction: int,
            *,
            starting_point: Optional[Point2D | Point3D] = None
    ) -> (list, bool):
        """
        Converts a Rectangle (defined by starting Point and width/ height) to a list of points.

        slicing direction 0 = horizontal - x-direction -> length
        slicing direction 1 = vertical - y-direction -> width
        """
        # Todo für schräge rectangle usw überarbeiten
        if not isinstance(self.bottom_left, Point3D):
            self.bottom_left = Point3D(X=self.bottom_left.X, Y=self.bottom_left.Y, Z=0)

        point_list = []  # for saving the points - startpoint and endpoint in each row of the list

        if hatching_direction == 0:  # x-direction
            a = np.array((self.length, 0, 0))
            b = np.array((0, self.width, 0))
            N = abs(int(np.ceil(b[1] / self.hatch_size)))  # number of hatching lines
        elif hatching_direction == 1:  # vertical - width = a
            a = np.array((0, self.width, 0))
            b = np.array((self.length, 0, 0))
            N = abs(int(np.ceil(b[0] / self.hatch_size)))  # number of hatching lines
            # a *= -1
            # b *= -1
        else:
            raise NotImplementedError(
                f"No Implementation for slicing direction {hatching_direction}. Please use slicing direction 0 for "
                f"horizontal slicing and slicing direction 1 for vertical slicing.")
        if N < 0:
            pass
        if N % 2 == 0:
            self.opposite_end_position = True
        hatch_size_opt = b / N  # optimised hatch size

        for i in range(N + 1):
            if not point_list:
                if starting_point is None:
                    point_start = self.bottom_left
                else:
                    if not isinstance(starting_point, Point3D):
                        starting_point = Point3D(*starting_point)
                    point_start = starting_point
            else:
                point_start = point_list[-1][1] + Point3D(*hatch_size_opt)  # adding hatching

            adding = a * (-1) ** (i % 2)
            point_end = point_start + Point3D(*adding)
            point_list.append((point_start, point_end))

        self.end_point_layer = point_end
        return point_list

    def draw_on(
            self,
            coordinate_system: CoordinateSystem,
    ) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)
        if self.starting_point is not None:
            layer = self.calc_points_layer(hatching_direction=self.hatching_direction,
                                           starting_point=self.starting_point)
        else:
            layer = self.calc_points_layer(hatching_direction=self.hatching_direction)

        for lines in layer:  # 2 points per layer
            starting_point = lines[0]
            end_point = lines[1]

            if self.hatching_direction == 0:  # x-direction of slicing
                printing_line = [[starting_point.X, end_point.X]]
                Lines = XLines(y=starting_point.Y, z=starting_point.Z, lines=printing_line,
                               velocity=self.velocity, acceleration=self.acceleration)
            else:  # y-direction of slicing
                printing_line = [[starting_point.Y, end_point.Y]]
                Lines = YLines(x=starting_point.X, z=starting_point.Z, lines=printing_line,
                               velocity=self.velocity, acceleration=self.acceleration)
            prog = Lines.draw_on(coordinate_system=coordinate_system)
            program.add_programm(prog)

        return program


class Rectangle3DHannes(DrawableObject):
    def __init__(
            self,
            bottom_left: Point2D | Point3D,
            width: float,
            length: float,
            structure_height: float,
            *,
            hatch_size: float,
            slice_size: float,
            velocity: float,
            acceleration: float,
    ):
        super().__init__()
        self.bottom_left = bottom_left
        self.width = width
        self.length = length
        self.height = structure_height

        self.hatch_size = hatch_size
        self.slice_size = slice_size
        self.velocity = velocity
        self.acceleration = acceleration

    @property
    def center_point(self) -> Point3D:
        return self.bottom_left + Point3D(self.width / 2, self.length / 2, self.height / 2)

    # def slicing_layers(self) -> list:
    #     N = np.ceil(self.height / self.slice_size)  # number of layers for slicing
    #     slice_size_opt = self.height / N  # optimised layer height
    #     i = 0  # running variable
    #     a = None  # starting point for slicing layer
    #     points_structure = []  # list of all points layer by layer
    #
    #     for i in range(N):
    #         layer = self.calc_points_layer(i % 2, starting_point=a)
    #         points_structure.append(layer)
    #         a = points_structure[-1][-1][1] + i * slice_size_opt
    #     return points_structure

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)

        n_layer = int(np.ceil(self.height / self.slice_size)) + 1  # number of layers for slicing
        slice_size_opt = self.height / (n_layer - 1)  # optimised layer height
        starting_point = self.bottom_left  # starting point for slicing layer

        # initialisation of first layer Rectangle
        rect = Rectangle2DHannes(
            starting_point,
            width=self.width,
            length=self.length,
            hatch_size=self.hatch_size,
            velocity=self.velocity,
            acceleration=self.acceleration
        )

        for i in range(n_layer):  # N + 1 layer for whole structure
            # slicing of the layer by Rectangle2D
            rect.hatching_direction = i % 2
            rect.starting_point = starting_point
            prog = rect.draw_on(coordinate_system)
            program.add_programm(prog)

            # Calculate rectangle for next layer
            starting_point = rect.end_point_layer + Point3D(X=0, Y=0, Z=slice_size_opt)

            if rect.opposite_end_position:
                rect.width *= -1
                rect.length *= -1
            else:
                if (i + 1) % 2 == 0:
                    rect.length *= -1
                else:
                    rect.width *= -1

        return program



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

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)
        point = self.position.as_dict()
        point["Z"] = self.z_min
        program.LINEAR(**point, F=self.F)
        program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.ON)
        point["Z"] = self.z_max
        program.LINEAR(**point, F=self.F)
        program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.OFF)
        return program


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

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
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

        n_layer = round(hatching_length / self.hatch_size) + 1
        hatch_size_opt = hatching_length / (n_layer - 1)

        order = 1
        for i in range(n_layer):
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

        return program


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

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
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

            program.add_programm(rectangle.draw_on(coordinate_system))
            hatching_direction = hatching_direction.flip()

        return program


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

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
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
            program.add_programm(socket.draw_on(coordinate_system))

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

            program.add_programm(step_rectangle.draw_on(coordinate_system))

        return program
