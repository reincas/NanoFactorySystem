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
    """
    Prints n_lines parallel lines along the draw_axis, with geometrically
    decreasing spacing (from max_dist to min_dist) to characterize the
    minimum resolvable feature size of the 2PP system.

    Geometry (draw_axis='x'):
        Lines run along X.
        Spacing varies along Y: large gaps on the outside, small gaps in the center
        — or monotonically from max_dist → min_dist, left to right.

    Parameters
    ----------
    center : Point3D
        Center of the test structure.
    fov : float | list | tuple
        Field of view in µm. Used to validate that the structure fits.
    min_dist : float
        Minimum line spacing in µm (e.g. 0.05 µm = 50 nm).
    max_dist : float
        Maximum line spacing in µm (e.g. 5 µm).
    n_lines : int
        Number of printed lines. There will be (n_lines - 1) gaps between them.
    length : float
        Length of each line along the draw_axis in µm.
    height : float
        Structural height in µm (number of slices = height / slice_size + 1).
    draw_axis : 'x' | 'y'
        Axis along which lines are written. Spacing varies in the perpendicular axis.
    """

    def __init__(
            self,
            center: Point3D,
            fov: float | list | tuple,
            min_dist: float,
            max_dist: float,
            n_lines: int = 20,
            length: float = 50.0,   # µm
            height: float = 3.0,    # µm
            draw_axis: Literal['x', 'y'] = 'x',
            *,
            slice_size: float,
            velocity: float,
            acceleration: float
    ):
        super().__init__()
        self.center = center

        if isinstance(fov, (list, tuple)) and len(fov) == 2:
            self.fov = tuple(fov)
        elif isinstance(fov, (int, float)):
            self.fov = (float(fov), float(fov))
        else:
            raise TypeError("fov must be a float or a 2-element list/tuple.")

        if n_lines < 2:
            raise ValueError("n_lines must be at least 2 (need at least one gap).")
        if min_dist <= 0 or max_dist <= 0:
            raise ValueError("min_dist and max_dist must be positive.")
        if min_dist >= max_dist:
            raise ValueError("min_dist must be smaller than max_dist.")

        self.min_dist = min_dist
        self.max_dist = max_dist
        self.n_lines = n_lines
        self.length = length
        self.height = height
        self.draw_axis = draw_axis.lower()

        self.slice_size = slice_size
        self.velocity = velocity
        self.acceleration = acceleration

        self._distances: Optional[np.ndarray] = None
        self._center_points: Optional[list[float]] = None

        # FOV validation
        self._validate_fov()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def distances(self) -> np.ndarray:
        """
        (n_lines - 1) gap sizes between consecutive lines,
        spaced geometrically from max_dist down to min_dist.

        Printing order: large gaps first (easy to resolve),
        shrinking toward min_dist (hard to resolve).
        """
        if self._distances is None:
            # n_lines lines → n_lines - 1 gaps
            # Reversed so we go from large → small (coarse → fine)
            self._distances = np.geomspace(self.max_dist, self.min_dist, self.n_lines - 1)
        return self._distances

    @property
    def total_span(self) -> float:
        """Total extent of the line array in the perpendicular axis (µm)."""
        return float(np.sum(self.distances))

    @property
    def center_point(self) -> Point3D:
        return self.center

    @property
    def center_points(self) -> list[float]:
        """
        Positions of all n_lines along the perpendicular axis,
        centered around the structure center.
        """
        if self._center_points is None:
            origin = self._perp_center() - self.total_span / 2
            points = [origin]
            for d in self.distances:
                points.append(points[-1] + d)
            self._center_points = points
        return self._center_points

    @property
    def number_of_lines(self) -> int:
        return self.n_lines

    @property
    def max_distance(self) -> float:
        return self.max_dist

    @property
    def min_distance(self) -> float:
        return self.min_dist

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _perp_center(self) -> float:
        """Center coordinate in the axis perpendicular to draw_axis."""
        if self.draw_axis == 'x':
            return self.center.Y
        elif self.draw_axis == 'y':
            return self.center.X
        else:
            raise ValueError(f"Invalid draw_axis: '{self.draw_axis}'. Must be 'x' or 'y'.")

    def _line_start(self) -> float:
        """Start coordinate of a line along draw_axis."""
        if self.draw_axis == 'x':
            return self.center.X - self.length / 2
        else:
            return self.center.Y - self.length / 2

    def _validate_fov(self):
        """Warn if the structure exceeds the FOV."""
        fov_perp = self.fov[1] if self.draw_axis == 'x' else self.fov[0]
        total = np.sum(np.geomspace(self.max_dist, self.min_dist, self.n_lines - 1))
        if total > fov_perp:
            raise ValueError(
                f"Total structure span ({total:.2f} µm) exceeds FOV "
                f"({fov_perp:.2f} µm) in the perpendicular axis. "
                f"Reduce n_lines, max_dist, or increase fov."
            )

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _single_layer(
            self,
            coordinate_system: CoordinateSystem,
            z: float,
            line_program,
            line_start: float,
    ) -> DrawableAeroBasicProgram:
        """Draw all lines for one Z-layer, alternating scan direction."""
        program = DrawableAeroBasicProgram(coordinate_system)
        order = 1
        for cp in self.center_points:
            # Alternate scan direction: left→right, then right→left
            lines = [[line_start, line_start + self.length][::order]]
            line = line_program(
                cp,
                z=z,
                lines=lines,
                velocity=self.velocity,
                acceleration=self.acceleration,
            )
            program.add_programm(line.draw_on(coordinate_system))
            order *= -1
        return program

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        """Yield one DrawableAeroBasicProgram per Z-slice."""
        if self.height == 0:
            return

        n_layer = abs(round(self.height / self.slice_size)) + 1
        slice_size_opt = self.height / (n_layer - 1) if n_layer > 1 else 0.0

        if self.draw_axis == 'x':
            line_program = XLines
        elif self.draw_axis == 'y':
            line_program = YLines
        else:
            raise ValueError(f"Invalid draw_axis: '{self.draw_axis}'.")

        line_start = self._line_start()

        for i in range(n_layer):
            z = self.center.Z + i * slice_size_opt
            layer_program = self._single_layer(
                coordinate_system=coordinate_system,
                z=z,
                line_program=line_program,
                line_start=line_start,
            )
            program = DrawableAeroBasicProgram(coordinate_system)
            program.LINEAR(Z=z)
            program.add_programm(layer_program)
            yield program