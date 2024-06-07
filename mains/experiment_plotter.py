from dataclasses import dataclass
from typing import Iterator

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, Rectangle


@dataclass
class ExperimentConfiguration:
    resin_corner_tr: np.ndarray  # 2D
    resin_corner_bl: np.ndarray  # 2D

    fov_size: float
    margin: float
    padding: float
    grid_center: tuple[float, float]
    grid: tuple[int, int]

    def iter_experiment_locations(self) -> Iterator[tuple[float, float]]:
        for i in range(self.grid[0]):
            for j in range(self.grid[1]):
                rect_x = self.rectangle_tl[0] + self.margin + j * (self.fov_size + self.padding)
                rect_y = self.rectangle_tl[1] + self.margin + i * (self.fov_size + self.padding)
                yield rect_x + self.fov_size / 2, rect_y + self.fov_size / 2

    def __post_init__(self):
        self.resin_corner_tr = np.asarray(self.resin_corner_tr)
        self.resin_corner_bl = np.asarray(self.resin_corner_bl)

    @property
    def center_point(self) -> np.ndarray:
        return (self.resin_corner_bl + self.resin_corner_tr) / 2

    @property
    def resin_size(self) -> np.ndarray:
        return self.resin_corner_tr - self.resin_corner_bl

    @property
    def absolute_grid_center(self) -> tuple[float, float]:
        return self.grid_center[0] + self.center_point[0], self.grid_center[1] + self.center_point[1]

    @property
    def grid_width(self):
        return self.grid[1] * (self.fov_size + self.padding) - self.padding + 2 * self.margin

    @property
    def grid_height(self):
        return self.grid[0] * (self.fov_size + self.padding) - self.padding + 2 * self.margin

    @property
    def rectangle_tl(self):
        return self.center_point + self.grid_center - [self.grid_width / 2, self.grid_height / 2]

    @property
    def rectangle_br(self):
        return self.center_point + self.grid_center + [self.grid_width / 2, self.grid_height / 2]

    def plot(self, plane_fit_points=None):
        # Visualize experiment
        fig, ax = plt.subplots()
        assert isinstance(ax, plt.Axes)

        # Draw the ellipse
        ellipse = Ellipse(self.center_point, self.resin_size[0], self.resin_size[1], edgecolor='lightblue',
                          facecolor='lightblue', lw=2, label="Resin Drop")
        ax.add_patch(ellipse)

        # Draw the outer rectangle
        outer_rectangle = Rectangle(self.rectangle_tl, self.grid_width, self.grid_height, edgecolor='blue',
                                    facecolor='none', lw=2, label="Experiment Field")
        ax.add_patch(outer_rectangle)

        # Draw the grid of rectangles
        center_xs = []
        center_ys = []
        for i, (x, y) in enumerate(self.iter_experiment_locations()):
            x_tl = x - self.fov_size / 2
            y_tl = y - self.fov_size / 2
            rect = Rectangle(
                (x_tl, y_tl),
                width=self.fov_size,
                height=self.fov_size,
                edgecolor='green',
                facecolor='none',
                lw=1
            )
            ax.text(x_tl, y_tl, f"{i}", color="green")
            ax.add_patch(rect)
            center_xs.append(x)
            center_ys.append(y)

        ax.scatter(center_xs, center_ys, s=3, marker="x", color="green", label="Structures")

        if plane_fit_points is not None:
            ax.scatter(*zip(*plane_fit_points), s=3, marker=".", color="red", label="Plane Fitting Probe Points")

        # Set limits and aspect ratio
        ax.set_xlim(self.resin_corner_bl[0], self.resin_corner_tr[0])
        ax.set_ylim(self.resin_corner_bl[1], self.resin_corner_tr[1])
        ax.set_xlabel("X [um]")
        ax.set_ylabel("Y [um]")
        ax.set_aspect('equal')
        plt.legend()
        plt.tight_layout()


def sample_points_for_experiment_configuration(experiment_configuration: ExperimentConfiguration, n_mid_points: 2) -> \
        list[tuple[float, float]]:
    tl = experiment_configuration.rectangle_tl + experiment_configuration.margin / 2
    br = experiment_configuration.rectangle_br - experiment_configuration.margin / 2
    points = set()
    for x in np.linspace(tl[0], br[0], n_mid_points + 2):
        points.add((x, tl[1]))
        points.add((x, br[1]))

    for y in np.linspace(tl[1], br[1], n_mid_points + 2):
        points.add((tl[0], y))
        points.add((br[0], y))

    return list(points)


if __name__ == '__main__':
    experiment_configuration = ExperimentConfiguration(
        resin_corner_bl=np.asarray((-5700, 15000)),  # um
        resin_corner_tr=np.asarray((6700, 28100)),  # um
        fov_size=500,
        margin=200,
        padding=100,
        grid_center=(0, 5100),
        grid=(2, 3),  # Rows, Cols

    )

    plane_fit_points = sample_points_for_experiment_configuration(experiment_configuration, n_mid_points=2)

    # Visualize experiment
    experiment_configuration.plot(plane_fit_points)

    plt.show()
