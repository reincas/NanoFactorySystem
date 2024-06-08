import abc
from enum import Enum
from typing import Optional, Protocol

import numpy as np

from nanofactorysystem.aerobasic import SingleAxis, GalvoLaserOverrideMode, VelocityMode
from nanofactorysystem.aerobasic.programs.drawings import DrawableAeroBasicProgram, DrawableObject, DrawablePoint
from nanofactorysystem.aerobasic.programs.drawings.lines import YLines
from nanofactorysystem.aerobasic.utils.geometry import line_circle_intersection
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point3D, Point2D


class CircleDirection(Enum):
    Clockwise = "CW"
    Counterclockwise = "CCW"


class FilledCircleFactory(Protocol):
    def __call__(
            self,
            center: Point2D | Point3D,
            radius_start: float,
            *,
            radius_end: float = 0,
            hatch_size: float,
    ):
        pass


class Circle2D(DrawableObject):
    def __init__(
            self,
            center: Point2D | Point3D,
            radius: float,
            velocity: Optional[float] = None,
            circle_direction: CircleDirection = CircleDirection.Clockwise
    ):
        super().__init__()
        self.center = center
        self.radius = radius
        self.velocity = velocity
        self.circle_direction = circle_direction

    @property
    def center_point(self) -> Point2D:
        return self.center

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)
        start_point = self.center + Point2D(X=self.radius, Y=0)
        program.comment(f"\nDraw circle with radius {self.radius} at {self.center}")
        program.LINEAR(**start_point.as_dict())
        kwargs = {
            "axis1": SingleAxis.X,
            "axis2": SingleAxis.Y,
            "axis1_endpoint": start_point.X,
            "axis2_endpoint": start_point.Y,
            "axis1_center": self.center.X - start_point.X,
            "axis2_center": self.center.Y - start_point.Y,
            "velocity": self.velocity

        }
        program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.ON)
        if self.circle_direction == CircleDirection.Clockwise:
            program.CW(**kwargs)
        elif self.circle_direction == CircleDirection.Counterclockwise:
            program.CCW(**kwargs)
        else:
            raise ValueError(f"Could not identify circle direction {self.circle_direction}")
        program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.OFF)
        return program

class DrawableCircle(DrawableObject, abc.ABC):
    def __init__(
            self,
            center: Point2D | Point3D,
            radius_start: float,
            radius_end: float = 0,
            *,
            hatch_size: float,
    ):
        super().__init__()

        self.radius_start = radius_start
        self.radius_end = radius_end
        self.hatch_size = hatch_size
        self.center = center

    @property
    def center_point(self) -> Point2D:
        return self.center

    @classmethod
    @abc.abstractmethod
    def as_circle_factory(cls, *args) -> FilledCircleFactory:
        pass


class LineCircle2D(DrawableCircle):
    def __init__(
            self,
            center: Point2D | Point3D,
            radius_start: float,
            radius_end: float = 0,
            *,
            hatch_size: float,
            acceleration: float,
            velocity: float,
    ):
        super().__init__(
            center,
            radius_start,
            radius_end=radius_end,
            hatch_size=hatch_size,
        )
        self.acceleration = acceleration
        self.velocity = velocity

    @classmethod
    def as_circle_factory(cls, acceleration: float, velocity: float) -> FilledCircleFactory:
        def circle_factory(
                center: Point2D | Point3D,
                radius_start: float,
                *,
                radius_end: float = 0,
                hatch_size: float,
        ):
            return cls(
                center=center,
                radius_start=radius_start,
                radius_end=radius_end,
                hatch_size=hatch_size,
                velocity=velocity,
                acceleration=acceleration
            )

        return circle_factory

    def draw_on(self, coordinate_system: CoordinateSystem):
        """
        Draw circle
        """
        program = DrawableAeroBasicProgram(coordinate_system)

        if self.radius_end > self.radius_start:
            big_radius = self.radius_end
            small_radius = self.radius_start
        else:
            big_radius = self.radius_start
            small_radius = self.radius_end

        order = 1
        for x_offset in np.arange(-big_radius, big_radius, self.hatch_size):
            current_x = self.center.X - x_offset
            y1 = self.center.Y - big_radius
            y2 = self.center.Y + big_radius

            # Calculate intersection of outer radius
            n_outer, p_outer_1, p_outer_2 = line_circle_intersection(
                (current_x, y1),
                (current_x, y2),
                self.center.to_2d().as_tuple(),
                radius=big_radius
            )
            if n_outer == 1:
                # point_program = DrawablePoint(Point2D(*p_outer_1)).draw_on(coordinate_system)
                # program.add_programm(point_program)
                continue
            elif n_outer < 1:
                continue

            n_inner, p_inner_1, p_inner_2 = line_circle_intersection(
                (current_x, y1),
                (current_x, y2),
                self.center.to_2d().as_tuple(),
                radius=small_radius
            )

            if n_inner < 2:
                # No inner circle intersection or tangent (which is ignored)
                lines = [(p_outer_1[1], p_outer_2[1])[::order]]
            else:
                lines = [(p_outer_1[1], p_inner_1[1])[::order], (p_inner_2[1], p_outer_2[1])[::order]]

            y_lines = YLines(
                x=current_x,
                z=self.center.Z,
                lines=lines[::order],  # noqa
                velocity=self.velocity,
                acceleration=self.acceleration
            )
            program.add_programm(y_lines.draw_on(coordinate_system))
            order *= -1

        return program


class DrawableRoundCircle(DrawableCircle, abc.ABC):
    def __init__(
            self,
            center: Point2D | Point3D,
            radius_start: float,
            *,
            radius_end: float = 0,
            hatch_size: float,
            velocity: Optional[float] = None,
            circle_direction: CircleDirection = CircleDirection.Clockwise,
    ):
        super().__init__(center, radius_start, radius_end=radius_end, hatch_size=hatch_size)
        self.velocity = velocity
        self.circle_direction = circle_direction
        if not isinstance(circle_direction, CircleDirection):
            raise ValueError(f"Could not identify circle direction {circle_direction}")

        # Flip sign depending on inward/outward movement
        if (self.radius_end - self.radius_start) / self.hatch_size < 0:
            self.hatch_size = -self.hatch_size

    @classmethod
    def as_circle_factory(
            cls,
            velocity: Optional[float] = None,
            circle_direction: CircleDirection = CircleDirection.Clockwise
    ) -> FilledCircleFactory:
        def circle_factory(
                center: Point2D | Point3D,
                radius_start: float,
                *,
                radius_end: float = 0,
                hatch_size: float,
        ):
            return cls(
                center=center,
                radius_start=radius_start,
                radius_end=radius_end,
                hatch_size=hatch_size,
                velocity=velocity,
                circle_direction=circle_direction
            )

        return circle_factory


class FilledCircle2D(DrawableRoundCircle):
    def draw_on(self, coordinate_system: CoordinateSystem):
        program = DrawableAeroBasicProgram(coordinate_system)

        for r in np.arange(self.radius_start, self.radius_end, self.hatch_size):
            circle = Circle2D(
                center=self.center,
                radius=r,
                velocity=self.velocity,
                circle_direction=self.circle_direction,
            )
            program.add_programm(circle.draw_on(coordinate_system))

        return program


class Spiral2D(DrawableRoundCircle):
    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)
        if self.circle_direction == CircleDirection.Clockwise:
            circle_function = program.CW
        elif self.circle_direction == CircleDirection.Counterclockwise:
            circle_function = program.CCW
        else:
            raise RuntimeError(f"Should never be reached")

        start_point = self.center + Point2D(X=self.radius_start, Y=0)
        program.comment(f"\nDraw Spiral from radius {self.radius_start} to {self.radius_end} at {self.center}")
        program.LINEAR(**start_point.as_dict())

        program.VELOCITY(VelocityMode.ON)
        program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.ON)

        # Draw full start circle
        if self.radius_start != 0:
            kwargs = {
                "axis1": SingleAxis.X,
                "axis2": SingleAxis.Y,
                "axis1_endpoint": start_point.X,
                "axis2_endpoint": start_point.Y,
                "axis1_center": self.center.X - start_point.X,
                "axis2_center": self.center.Y - start_point.Y,
                "velocity": self.velocity
            }
            program.comment(f"\nFull circle with radius {self.radius_start}")
            circle_function(**kwargs)
        else:
            # Printing Point in the middle of the spiral
            program.comment(f"\nDraw single point in the middle")
            program.add_programm(DrawablePoint(self.center).draw_on(coordinate_system))

        # Spiral
        for radius in np.arange(self.radius_start, self.radius_end, self.hatch_size):
            start_point = self.center + Point2D(X=radius, Y=0)
            # First half circle to the other side
            program.comment(f"\nDraw two half circles to get a spiral from {radius} to {radius + self.hatch_size}")
            kwargs = {
                "axis1": SingleAxis.X,
                "axis2": SingleAxis.Y,
                "axis1_endpoint": start_point.X - radius * 2 + self.hatch_size / 2,
                "axis2_endpoint": start_point.Y,
                "axis1_center": -radius + self.hatch_size / 2,
                "axis2_center": 0,
                "velocity": self.velocity,
            }
            circle_function(**kwargs)

            # Second half circle to the start side with self.hatch_size difference
            kwargs = {
                "axis1": SingleAxis.X,
                "axis2": SingleAxis.Y,
                "axis1_endpoint": start_point.X + self.hatch_size,
                "axis2_endpoint": start_point.Y,
                "axis1_center": radius,
                "axis2_center": 0,
                "velocity": self.velocity,
            }
            circle_function(**kwargs)

        if self.radius_end != 0:
            kwargs = {
                "axis1": SingleAxis.X,
                "axis2": SingleAxis.Y,
                "axis1_endpoint": start_point.X,
                "axis2_endpoint": start_point.Y,
                "axis1_center": self.center.X - start_point.X,
                "axis2_center": self.center.Y - start_point.Y,
                "velocity": self.velocity
            }
            program.comment(f"\nFull circle at end with radius {self.radius_end}")
            circle_function(**kwargs)

        else:
            # Printing Point in the middle of the spiral
            program.comment(f"\nDraw single point in the middle")
            program.add_programm(DrawablePoint(self.center).draw_on(coordinate_system))

        return program


