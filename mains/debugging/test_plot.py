import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from nanofactorysystem.aerobasic.programs.drawings import DrawableObject, DrawableAeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.circle import DrawableCircle, FilledCircle2D, FilledCircleFactory
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point3D, Point2D


class AsphericalLens(DrawableObject):
    def __init__(self,
                 center,
                 radius_of_curvature,
                 slice_size,
                 conic_constant_k,
                 alpha,
                 max_x,
                 max_y,
                 circle_object_factory=FilledCircle2D,
                 hatch_size,
                 velocity):
        super().__init__()
        self.circle_object_factory = circle_object_factory
        self.hatch_size = hatch_size
        self.velocity = velocity
        self.k = conic_constant_k
        self.alpha = alpha

        self.center = center
        self.radius_of_curvature = radius_of_curvature
        self.N = int(np.ceil(radius_of_curvature / slice_size))
        self.slice_size = slice_size

        self.max_x = max_x
        self.max_y = max_y

    @property
    def center_point(self):
        return self.center

    def sag(self, x, y):
        """
        Function to calculate the sag of the aspherical lens.
        """
        r = np.sqrt(x ** 2 + y ** 2)
        term1 = r ** 2 / (self.radius_of_curvature * (
                1 + np.sqrt(1 - (1 + self.k) * (r ** 2 / self.radius_of_curvature ** 2))))
        term2 = self.alpha * r ** 4
        return term1 + term2

    def slice_at_height(self, z, num_points=100):
        """
        Calculate the x and y coordinates for a given height z,
        within the specified maximum x and y dimensions.
        """
        x = np.linspace(-self.max_x / 2, self.max_x / 2, num_points)
        y = np.linspace(-self.max_y / 2, self.max_y / 2, num_points)
        X, Y = np.meshgrid(x, y)

        term1 = (X ** 2 + Y ** 2) / (self.radius_of_curvature * (
                1 + np.sqrt(1 - (1 + self.k) * ((X ** 2 + Y ** 2) / self.radius_of_curvature ** 2))))
        term2 = self.alpha * (X ** 2 + Y ** 2) ** 2
        calculated_z = term1 + term2

        valid_indices = np.where(np.abs(calculated_z - z) < 1e-6)
        return X[valid_indices], Y[valid_indices]

    def visualize_lens(self, num_points=100):
        """
        Visualize the aspherical lens in a 3D plot.
        """
        x = np.linspace(-self.max_x / 2, self.max_x / 2, num_points)
        y = np.linspace(-self.max_y / 2, self.max_y / 2, num_points)
        X, Y = np.meshgrid(x, y)
        Z = self.sag(X, Y)

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(X, Y, Z, cmap='viridis')

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Sag (Z)')
        ax.set_title('Aspherical Lens Surface')

        plt.show()


# Example usage
center = Point2D(0, 0)
radius_of_curvature = 50.0
slice_size = 1.0
conic_constant_k = -1.0
alpha = 0.5
max_x = 20.0
max_y = 20.0
hatch_size = 0.1
velocity = 1.0

lens = AsphericalLens(center, radius_of_curvature, slice_size, conic_constant_k, alpha, max_x, max_y,
                      hatch_size=hatch_size, velocity=velocity)
lens.visualize_lens(num_points=100)
