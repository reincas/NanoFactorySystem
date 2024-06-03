from enum import Enum
from typing import Optional

import numpy as np

from nanofactorysystem.aerobasic import SingleAxis, GalvoLaserOverrideMode
from nanofactorysystem.aerobasic.programs.drawings import DrawableAeroBasicProgram
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point3D, Point2D


class CircleDirection(Enum):
    Clockwise = "CW"
    Counterclockwise = "CCW"


class Circle2D(DrawableAeroBasicProgram):
    def __init__(
            self,
            center: Point2D | Point3D,
            radius: float,
            *,
            velocity: Optional[float] = None,
            circle_direction: CircleDirection = CircleDirection.Clockwise,
            coordinate_system: CoordinateSystem = CoordinateSystem()
    ):
        super().__init__(coordinate_system=coordinate_system)
        self.center = center

        self.start_point = self.center + Point2D(X=radius, Y=0)
        self.comment(f"\nDraw circle with radius {radius} at {center}")
        self.LINEAR(**self.start_point.as_dict())
        kwargs = {
            "axis1": SingleAxis.X,
            "axis2": SingleAxis.Y,
            "axis1_endpoint": self.start_point.X,
            "axis2_endpoint": self.start_point.Y,
            "axis1_center": self.center.X,
            "axis2_center": self.center.Y,
            "velocity": velocity

        }
        self.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.ON)
        if circle_direction == CircleDirection.Clockwise:
            self.CW(**kwargs)
        elif circle_direction == CircleDirection.Counterclockwise:
            self.CCW(**kwargs)
        else:
            raise ValueError(f"Could not identify circle direction {circle_direction}")
        self.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.OFF)


class FilledCircle2D(DrawableAeroBasicProgram):
    def __init__(
            self,
            center: Point2D | Point3D,
            radius_start: float,
            radius_end: float = 0,
            *,
            hatch_size: float,
            velocity: Optional[float] = None,
            circle_direction: CircleDirection = CircleDirection.Clockwise,
            coordinate_system: CoordinateSystem = CoordinateSystem()
    ):
        super().__init__(coordinate_system=coordinate_system)

        # Flip sign if
        if (radius_end - radius_start) / hatch_size < 0:
            hatch_size = -hatch_size

        for r in np.arange(radius_start, radius_end, hatch_size):
            circle = Circle2D(
                center=center,
                radius=r,
                velocity=velocity,
                circle_direction=circle_direction,
                coordinate_system=self.coordinate_system
            )
            self.add_programm(circle)
