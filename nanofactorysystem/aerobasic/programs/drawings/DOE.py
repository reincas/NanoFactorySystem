import numpy as np
from typing import Iterator

from nanofactorysystem.aerobasic.programs.drawings import DrawableObject, DrawableAeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.lines import HatchingDirection, Rectangle3D
from nanofactorysystem.devices.coordinate_system import Point2D, Point3D, CoordinateSystem


class Simple_DOE(DrawableObject):
    def __init__(self,
                 center: Point2D | Point3D,
                 rows: int,
                 columns: int,
                 z_profile,
                 pixel_size,
                 *,
                 hatch_size: float,
                 slice_size: float,
                 velocity: float,
                 acceleration: float
                 ):
        super().__init__()
        self.center = center
        self.z_profile = np.asarray(z_profile)
        self.rows = int(rows)
        self.columns = int(columns)
        try:
            (self.rows, self.columns) == self.z_profile.shape
        except Exception as e:
            print(f"Error {e} while comparing shape of height profile {self.z_profile.shape} and specified rows"
                  f"and columns ({rows, columns})")

        self.hatch_size = hatch_size
        self.slice_size = slice_size
        self.velocity = velocity
        self.acceleration = acceleration

        self.feature_size = pixel_size

    @property
    def center_point(self) -> Point2D:
        return self.center

    @property
    def structure_length(self) -> float:
        # length = x-direction
        return self.feature_size * self.z_profile.shape[0]

    @property
    def structure_width(self) -> float:
        # width = y-direction
        return self.feature_size * self.z_profile.shape[1]

    @property
    def max_structure_height(self) -> float:
        return np.max(self.z_profile)

    @property
    def min_structure_height(self) -> float:
        return np.min(self.z_profile)

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        """
        Very basic implementation of a DOE structure printed with Rectangles one by one.
        Future version should deliver layer by layer across all pixels.
        ToDo(HR) algorithm
        """
        program = DrawableAeroBasicProgram(coordinate_system)
        for i in range(self.rows):
            # iterating over rows
            x_offset = self.feature_size * (i - np.ceil(self.rows/2))

            for j in range(self.columns):
                height = self.z_profile[i][j]
                y_offset = self.feature_size * (j - np.ceil(self.columns/2))
                slice_size_opt = height / round(height/ self.slice_size)

                DOE_pixel = Rectangle3D(
                    center=self.center + Point3D(X=x_offset, Y=y_offset, Z=0),
                    width=self.feature_size,
                    length=self.feature_size,
                    height=height,
                    hatch_size=self.hatch_size,
                    slice_size=slice_size_opt,
                    velocity=self.velocity,
                    acceleration=self.acceleration
                )
                yield from DOE_pixel.iterate_layers(coordinate_system)
        return program
