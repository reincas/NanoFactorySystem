from typing import Type

import numpy as np

from nanofactorysystem.aerobasic.programs.drawings import DrawableObject, DrawableAeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.circle import DrawableCircle, FilledCircle2D, FilledCircleFactory
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point3D, Point2D


class SphericalLens(DrawableObject):

    def __init__(
            self,
            center: Point2D | Point3D,
            max_height,  # maximum thickness of lens
            radius_of_curvature: float,  # Radius of Curvature
            layer_height: float,  # ToDo(@all): einheiten müssen noch definiert werden
            *,
            circle_object_factory: FilledCircleFactory,
            hatch_size: float,
            velocity: float  # ToDo(@all): Einheiten bestimmen
    ):
        super().__init__()
        self.circle_object_factory = circle_object_factory
        self.hatch_size = hatch_size
        self.velocity = velocity

        self.center = center
        self.radius_of_curvature = radius_of_curvature
        self.layer_height = layer_height
        self.offset = self.radius_of_curvature - max_height
        self.max_height = max_height
        self.N = int(np.ceil(max_height / layer_height))

        # optimised hatching and slicing parameter
        # self.hatch_size_opt = # TODO(Hannes) Implementierung von hatch size optimised mit abhängigkeit von max_height und RoC
        self.slicing_height = self.max_height / self.N

    @property
    def center_point(self) -> Point2D:
        return self.center

    def draw_on(self, coordinate_system: CoordinateSystem):
        program = DrawableAeroBasicProgram(coordinate_system)

        if self.offset >= self.radius_of_curvature:
            raise Exception(
                f"Lens is not printable. Height of Offset ({self.offset}) exceeds the radius of curvature ({self.radius_of_curvature}).")

        for i in range(self.N + 1):
            z_i = i * self.slicing_height
            if (z_i + self.offset) <= self.radius_of_curvature:  # Ensure z_i does not exceed R
                r_i = np.sqrt(self.radius_of_curvature ** 2 - (z_i + self.offset) ** 2)
            else:
                r_i = 0  # If height exceeds R, radius is zero
                # TODO(dwoiwode): Müssen Kreise mit einem Radius = 0 gezeichnet werden? Oder kann dann abgebrochen werden?

            point = self.center + Point3D(X=0, Y=0, Z=z_i)
            layer = self.circle_object_factory(point, r_i, hatch_size=self.hatch_size)

            program.add_programm(layer.draw_on(coordinate_system))

        return program


class AsphericalLens(DrawableObject):

    def __init__(
            self,
            center: Point2D | Point3D,
            radius_of_curvature: float,  # Radius of Curvature
            layer_height: float,  # ToDo(@all): einheiten müssen noch definiert werden
            conic_constant_k: float,  # conic constant
            *,
            alpha: float,  # aspherical coefficient
            circle_object_factory: Type[DrawableCircle] = FilledCircle2D,
            hatch_size: float,
            velocity: float  # ToDo(@all): Einheiten bestimmen
    ):
        super().__init__()
        self.circle_object_factory = circle_object_factory
        self.hatch_size = hatch_size
        self.velocity = velocity
        self.k = conic_constant_k
        self.alpha = alpha

        self.center = center
        self.radius_of_curvature = radius_of_curvature
        self.N = int(np.ceil(radius_of_curvature / layer_height))
        self.layer_height = layer_height

    @property
    def center_point(self) -> Point2D:
        return self.center

    def sag(self, x: float, y: float) -> float:
        """
        Function to calculate the sag of the aspherical lens
        """
        r = np.sqrt(x**2 + y**2)
        term1 = r ** 2 / (self.radius_of_curvature * (
                    1 + np.sqrt(1 - (1 + self.k) * (r ** 2 / self.radius_of_curvature ** 2))))
        term2 = self.alpha * r ** 4
        return term1 + term2

    def slice_at_height(self, z: float, num_points: int = 100) -> np.ndarray:
        """
        Calculate the x and y coordinates for a given height z.
        """
        # Generate a range of radial distances
        r = np.linspace(0, np.sqrt(self.radius_of_curvature ** 2 - z), num_points)

        # Calculate the x and y values
        x = r
        y = np.zeros_like(r)  # For simplicity, we calculate along the x-axis

        # Adjust x and y values to the correct positions based on the sag equation
        term1 = r ** 2 / (self.radius_of_curvature * (
                1 + np.sqrt(1 - (1 + self.k) * (r ** 2 / self.radius_of_curvature ** 2))))
        term2 = self.alpha * r ** 4
        calculated_z = term1 + term2

        valid_indices = np.where(np.abs(calculated_z - z) < 1e-6)[0]
        return x[valid_indices], y[valid_indices]

    def draw_on(self, coordinate_system: CoordinateSystem):
        program = DrawableAeroBasicProgram(coordinate_system)


class Cylinder(DrawableObject):
    def __init__(
            self,
            center: Point2D | Point3D,
            radius: float,  # ToDO einheiten
            total_height: float,
            layer_height: float,  # ToDo(@all): einheiten müssen noch definiert werden
            *,
            circle_object_factory: FilledCircleFactory,
            hatch_size: float,
            velocity: float  # ToDo(@all): Einheiten bestimmen
    ):
        super().__init__()
        self.circle_object_factory = circle_object_factory
        self.hatch_size = hatch_size
        self.velocity = velocity

        self.center = center
        self.radius = radius
        self.layer_height = layer_height
        self.height = total_height
        # Number of layers to be printed
        self.N = int(np.ceil(self.height / self.layer_height))

    @property
    def center_point(self) -> Point2D:
        return self.center

    def draw_on(self, coordinate_system: CoordinateSystem):
        program = DrawableAeroBasicProgram(coordinate_system)

        for i in range(self.N + 1):
            z_i = i * self.layer_height
            point = self.center + Point3D(X=0, Y=0, Z=z_i)
            layer = self.circle_object_factory(point, self.radius, hatch_size=self.hatch_size)

            program.add_programm(layer.draw_on(coordinate_system))

        return program


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    lens = AsphericalLens(Point3D(X=0,Y=0,Z=0), 1030, 0.05,
                          -2.3, alpha=0, hatch_size=0.1, velocity=40000)
    # Define the range of x and y values
    x = np.arange(-300, 300, 1)
    y = np.arange(-300, 300, 1)
    X, Y = np.meshgrid(x, y)

    # Calculate the corresponding z values
    Z = lens.sag(X, Y)

    # Plot the surface
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(X, Y, Z, cmap='viridis')

    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    plt.show()
