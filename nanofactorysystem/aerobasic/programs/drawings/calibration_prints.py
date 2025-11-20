import math
from abc import ABC
from enum import Enum
from typing import Optional, Literal, Iterator
import numpy as np

from nanofactorysystem.aerobasic import GalvoLaserOverrideMode, SingleAxis
from nanofactorysystem.aerobasic.programs.drawings import DrawableAeroBasicProgram, DrawableObject
from nanofactorysystem.aerobasic.programs.drawings.lines import XLines, YLines
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Coordinate, Point3D, Point2D


class Distance_Test(DrawableObject):
    def __init__(
            self,
            center: Point3D,
            fov: float | list | tuple,  # field of view range -> minimal 100µm x 100µm (63x Objective)
            min_dist: float,  # minimal distance between lines -> 50 nm
            max_dist: float,  # maximal distance between lines -> 5 µm
            n_lines: int = 20,
            length: float = 50.0,  # µm
            height: float = 3.0,  # µm
            draw_axis: Literal['x', 'y'] = 'x',
            *,
            slice_size: float,
            velocity: float,
            acceleration: float
    ):
        super().__init__()
        self.center = center
        if isinstance(fov, list) and len(fov) == 2:
            self.fov = (fov[0], fov[1])
        elif isinstance(fov, tuple) and len(fov) == 2:
            self.fov = fov
        elif isinstance(fov, float):
            self.fov = (fov, fov)
        else:
            raise TypeError("fov must be list or tuple with length of 2 or a float number.")

        self.min_dist = min_dist
        self.max_dist = max_dist
        self.n_lines = n_lines
        self.length = length
        self.height = height
        self.draw_axis = draw_axis

        self.slice_size = slice_size
        self.velocity = velocity
        self.acceleration = acceleration

        self._distances = None
    @property
    def number_of_lines(self) -> float:
        return self.n_lines
    @property
    def max_distance(self) -> float:
        return self.max_dist
    @property
    def min_distance(self) -> float:
        return self.min_dist
    @property
    def distances(self):
        if self._distances is None:
            self._distances = np.geomspace(self.min_dist, self.max_dist, self.n_lines)
            return self._distances
        else:
            return self._distances

    # @distances.setter
    # def distances(self, value):
    #     self._distances = value

    @property
    def center_point(self) -> Point2D:
        return self.center

    def single_layer(self,
                     coordinate_system: CoordinateSystem,
                     center: Point3D,
                     center_points: list[float],
                     line_program: DrawableAeroBasicProgram,
                     line_start: float
                     ) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)
        order = 1
        for i in range(len(center_points)):
            lines = [
                [line_start, line_start + self.length][::order]
            ]
            line = line_program(
                center_points[i],
                z=center.Z,
                lines=lines,
                velocity=self.velocity,
                acceleration=self.acceleration,
            )
            program.add_programm(line.draw_on(coordinate_system))
            order *= -1

        return program

    # def get_lines(self,
    #               z_position,
    #               ) -> list[Point2D]:
    #     if self.draw_axis.lower() == "x":
    #         lines = XLines(
    #             y=0,
    #             z=0,
    #         lines: list[tuple[float, float]],
    #
    #         )
    #         # center_points -> Y-coordinate because in x-direction will be printed
    #         center_points = [self.center.Y - np.sum(self.distances) / 2]
    #         for i in range(len(self.distances)):
    #             center_points.append(center_points[-1] + self.distances[i])
    #         line_start = self.center.X - self.length / 2
    #     elif self.draw_axis.lower() == "y":
    #         line_program = YLines
    #         # center_points -> X, because print direction is y-axis
    #         center_points = [self.center.X - np.sum(self.distances) / 2]
    #         for i in range(len(self.distances)):
    #             center_points.append(center_points[-1] + self.distances[i])
    #         line_start = self.center.Y - self.length / 2
    #     else:
    #         raise ValueError(f"Drawing axis not found: {self.draw_axis}")
    #
    #     if self.draw_axis.lower() == "x":
    #         center_points = [[self.center.as_tuple()[0], (self.center.as_tuple()[1] - np.sum(self.distances) / 2)]]
    #         for i in range(self.n_lines):
    #             center_points.append([center_points[-1][0], center_points[-1][1] + self.distances[i]])
    #         lines = []
    #         for x_center, y_center in center_points:
    #             lines.append([(x_center - self.length / 2, y_center), (x_center + self.length / 2, y_center)])
    #             line_program = XLines
    #
    #     order = 1
    #     for i in range(len(center_points)):
    #         lines = [
    #             [line_start, line_start + self.length][::order]
    #         ]
    #         line = line_program(
    #             center_points[i],
    #             z=center.Z,
    #             lines=lines,
    #             velocity=self.velocity,
    #             acceleration=self.acceleration,
    #         )
    #     if self.draw_axis.lower() == "x":
    #         line_program = XLines
    #         # center_points -> Y-coordinate because in x-direction will be printed
    #         center_points = [self.center.Y - np.sum(self.distances) / 2]
    #         for i in range(len(self.distances)):
    #             center_points.append(center_points[-1] + self.distances[i])
    #         line_start = self.center.X - self.length / 2

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)
        if self.height == 0:
            return program

        n_layer = abs(round(self.height / self.slice_size)) + 1
        slice_size_opt = self.height / (n_layer - 1)

        if self.draw_axis.lower() == "x":
            line_program = XLines
            # center_points -> Y-coordinate because in x-direction will be printed
            center_points = [self.center.Y - np.sum(self.distances) / 2]
            for i in range(len(self.distances)):
                center_points.append(center_points[-1] + self.distances[i])
            line_start = self.center.X - self.length / 2
        elif self.draw_axis.lower() == "y":
            line_program = YLines
            # center_points -> X, because print direction is y-axis
            center_points = [self.center.X - np.sum(self.distances) / 2]
            for i in range(len(self.distances)):
                center_points.append(center_points[-1] + self.distances[i])
            line_start = self.center.Y - self.length / 2
        else:
            raise ValueError(f"Drawing axis not found: {self.draw_axis}")

        order = 1  # todo no hatching but maybe different site for printing (left-right -> right-left)
        for i in range(n_layer):
            z_offset = i * slice_size_opt
            layer_program = self.single_layer(
                center=self.center + Point3D(0, 0, z_offset),
                coordinate_system=coordinate_system,
                center_points=center_points,
                line_program=line_program,
                line_start=line_start,
            )
            program = DrawableAeroBasicProgram(coordinate_system)
            program.LINEAR(Z=z_offset + self.center.Z)
            program.add_programm(layer_program)
            yield program
            # todo here change of order if possible anytime
