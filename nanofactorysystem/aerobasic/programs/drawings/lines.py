import math
from abc import ABC
from enum import Enum
from typing import Optional, Literal, Iterator

import numpy as np
import qrcode

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

    def center_point(self) -> Point3D:
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

    def center_point(self) -> Point3D:
        return Point3D(self.x, (self.lines[0][0] + self.lines[-1][1]) / 2, self.z)


class ZLines(_Lines):
    line_axis = SingleAxis.Z

    def __init__(
            self,
            x: float,
            y: float,
            lines: list[tuple[float, float]],
            *,
            velocity: float,
            acceleration: float
    ):
        super().__init__(lines, {"X": x, "Y": y}, velocity=velocity, acceleration=acceleration)
        self.x = x
        self.y = y

    def center_point(self) -> Point3D:
        return Point3D(self.x, self.y, (self.lines[0][0] + self.lines[-1][1]) / 2)

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
                p1_mark = corner_center + (p1_raw - Point2D(0, 2*width)).rotate2D(rotation_rad)
                p2a_mark = corner_center + (p2_raw - Point2D(0, 2*width)).rotate2D(rotation_rad)
                p2b_mark = corner_center + (p2_raw - Point2D(2*width, 0)).rotate2D(rotation_rad)
                p3_mark = corner_center + (p3_raw - Point2D(2*width, 0)).rotate2D(rotation_rad)
                p1_mark, p2a_mark, p2b_mark, p3_mark = [p1_mark, p2a_mark, p2b_mark, p3_mark][::order]
                lines_mark.append([p1_mark.as_dict(), p2a_mark.as_dict()])
                lines_mark.append([p2b_mark.as_dict(), p3_mark.as_dict()])
            order *= -1
        lines += lines_mark
        return PolyLines(lines, F=F, E=E)


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
    Z = "Z"

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
            acceleration: float
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


class QrErrorCorrection(Enum):
    L = 0
    M = 1
    Q = 2
    H = 3


class QRCode(DrawableObject):
    def __init__(
            self,
            center: Point3D,
            text: str,
            *,
            version: Optional[int] = None,
            error_correction: Optional[QrErrorCorrection] = None,
            pixel_pitch: float,
            base_height: float,
            anchor_height: float,
            pixel_height: float,
            hatch_size: float,
            slice_size: float,
            horizontal_velocity: float,
            horizontal_acceleration: float,
            vertical_velocity: float,
            vertical_acceleration: float,
    ):
        super().__init__()
        self.center = center
        self.text = str(text)
        assert version is None or (1 <= version <= 40)
        self.version = version
        self.error_correction = error_correction or QrErrorCorrection.M
        self.pixel_pitch = float(pixel_pitch)
        self.base_height = float(base_height)
        self.anchor_height = float(anchor_height)
        self.pixel_height = float(pixel_height)

        self.hatch_size = hatch_size
        self.slice_size = slice_size
        self.horizontal_velocity = horizontal_velocity
        self.horizontal_acceleration = horizontal_acceleration
        self.vertical_velocity = vertical_velocity
        self.vertical_acceleration = vertical_acceleration

        if self.error_correction == QrErrorCorrection.L:
            corr = qrcode.constants.ERROR_CORRECT_L
        elif self.error_correction == QrErrorCorrection.M:
            corr = qrcode.constants.ERROR_CORRECT_M
        elif self.error_correction == QrErrorCorrection.Q:
            corr = qrcode.constants.ERROR_CORRECT_Q
        elif self.error_correction == QrErrorCorrection.H:
            corr = qrcode.constants.ERROR_CORRECT_H
        else:
            raise ValueError(f"Unknown error correction {self.error_correction}!")
        qr = qrcode.QRCode(version=self.version, error_correction=corr)
        qr.add_data(self.text)
        qr.make(fit=self.version is None)
        self.data = np.array(qr.modules, dtype=bool)

        self.n_layer = round(self.base_height / self.slice_size) + 1
        self.slice_size_opt = self.base_height / (self.n_layer - 1)

    @property
    def structure_length(self) -> float:
        return self.pixel_pitch * (self.data.shape[1] + 2)

    @property
    def structure_width(self) -> float:
        return self.pixel_pitch * (self.data.shape[0] + 2)

    @property
    def structure_height(self) -> float:
        return self.base_height + self.pixel_height

    @property
    def center_point(self) -> Point2D:
        return self.center

    def layer_to_z(self, layer_id: int) -> float:

        assert layer_id >= 0 and layer_id < self.n_layer
        if layer_id == self.n_layer-1:
            return self.base_height - self.anchor_height + (self.anchor_height + self.pixel_height)/2
        return self.slice_size_opt * layer_id

    def pixel_program(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:

        """
        Special layer. Draw a vertical line for each True pixel. Note: drawing must take place in the
        same direction (negative z direction in global coordinate system) for all lines to minimise
        disturbing effects of exposed resin.
        """

        program = DrawableAeroBasicProgram(coordinate_system)

        # TODO(RC) Take DropDirection into account
        # Note: z is relative to substrate surface
        z_start = self.base_height + self.pixel_height
        z_end = self.base_height - self.anchor_height
        lines = [[z_start, z_end]]

        h, w = self.data.shape
        order = 1
        for j in range(h):
            y = self.pixel_pitch * (j - (w - 1) / 2)
            for i in range(w)[::order]:
                x = self.pixel_pitch * (i - (w - 1) / 2)
                if self.data[j, i]:
                    line = ZLines(
                        x=x,
                        y=y,
                        lines=lines,
                        velocity=self.vertical_velocity,
                        acceleration=self.vertical_acceleration)
                    program.add_programm(line.draw_on(coordinate_system))
            order *= -1
        return program

    def layer_program(self, coordinate_system: CoordinateSystem, layer_id: int) -> DrawableAeroBasicProgram:

        assert layer_id >= 0 and layer_id < self.n_layer
        if layer_id == self.n_layer - 1:
            return self.pixel_program(coordinate_system)

        program = DrawableAeroBasicProgram(coordinate_system)
        z = self.layer_to_z(layer_id)
        hatching_direction = [HatchingDirection.X, HatchingDirection.Y][layer_id % 2]

        if hatching_direction == HatchingDirection.X:
            line_program = XLines
        elif hatching_direction == HatchingDirection.Y:
            line_program = YLines
        else:
            raise ValueError(f"HatchingDirection not found: {self.hatching_direction}")

        size = self.structure_length
        n_hatch = round(size / self.hatch_size) + 1
        hatch_size_opt = size / (n_hatch - 1)
        order = 1
        for i in range(n_hatch):
            line_position = hatch_size_opt * (i - n_hatch/2 + 0.5)
            line_start = size / 2
            lines = [[-line_start, line_start][::order]]
            line = line_program(
                line_position,
                z=z,
                lines=lines,
                velocity=self.horizontal_velocity,
                acceleration=self.horizontal_acceleration)
            program.add_programm(line.draw_on(coordinate_system))
            order *= -1
        return program

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)
        for layer_id in range(self.n_layer):
            yield self.layer_program(coordinate_system, layer_id)
        return program
