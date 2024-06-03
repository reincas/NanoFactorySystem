import abc
import warnings
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

from nanofactorysystem.devices.coordinate_system import Point3D

LASER_ON_PLOT_STYLE = {
    "c": "blue"
}
LASER_OFF_PLOT_STYLE = {
    "c": "red",
    "alpha": 0.2
}


class Movement(abc.ABC):
    def __init__(self, *, laser_on: bool):
        self.laser_on = laser_on

    def get_ax(self, ax: Optional[plt.Axes]) -> plt.Axes:
        if ax is None:
            return plt.gca()
        return ax

    @abc.abstractmethod
    def plot(self, ax: Optional[plt.Axes] = None, **plot_kwargs):
        pass


class LinearMovement(Movement):
    def __init__(self, start: Point3D, end: Point3D, *, laser_on: bool):
        super().__init__(laser_on=laser_on)
        self.start = start
        self.end = end

    def plot(self, ax: Optional[plt.Axes] = None, **plot_kwargs):
        ax = self.get_ax(ax)
        args = [
            (self.start.X, self.end.X),
            (self.start.Y, self.end.Y),
            (self.start.Z, self.end.Z),
        ]
        if self.laser_on:
            ax.plot(*args, **LASER_ON_PLOT_STYLE, **plot_kwargs)
        else:
            ax.plot(*args, **LASER_OFF_PLOT_STYLE, **plot_kwargs)


class ClockwiseMovement(Movement):
    def __init__(self, center: Point3D, start: Point3D, end: Point3D, *, laser_on: bool):
        super().__init__(laser_on=laser_on)
        self.center = center
        self.start = start
        self.end = end

    def plot(self, ax: Optional[plt.Axes] = None, **plot_kwargs):
        ax = self.get_ax(ax)

        radius = np.sqrt((self.start.X - self.center.X) ** 2 + (self.start.Y - self.center.Y) ** 2)
        print(radius)

        # Compute angles for start and end points relative to the center
        start_angle = np.arctan2(self.start.Y - self.center.Y, self.start.X - self.center.X)
        end_angle = np.arctan2(self.end.Y - self.center.Y, self.end.X - self.center.X)

        # Ensure that the angles are in a clockwise direction
        if start_angle <= end_angle:
            start_angle += 2 * np.pi

        # Generate points on the arc
        theta = np.linspace(start_angle, end_angle, 100)
        arc_x = self.center.X + radius * np.cos(theta)
        arc_y = self.center.Y + radius * np.sin(theta)
        arc_z = np.linspace(self.start.Z, self.end.Z, len(arc_x))

        # Plot the arc
        if self.laser_on:
            ax.plot(arc_x, arc_y, arc_z, **LASER_ON_PLOT_STYLE, **plot_kwargs)
        else:
            ax.plot(arc_x, arc_y, arc_z, **LASER_OFF_PLOT_STYLE, **plot_kwargs)


class CounterclockwiseMovement(Movement):
    def __init__(self, center: Point3D, start: Point3D, end: Point3D, *, laser_on: bool):
        super().__init__(laser_on=laser_on)
        self.center = center
        self.start = start
        self.end = end

    def plot(self, ax: Optional[plt.Axes] = None, **plot_kwargs):
        ax = self.get_ax(ax)
        # Compute the radius from the center to the start point
        radius = np.sqrt((self.start.X - self.center.X) ** 2 + (self.start.Y - self.center.Y) ** 2)

        # Compute angles for start and end points relative to the center
        start_angle = np.arctan2(self.start.Y - self.center.Y, self.start.X - self.center.X)
        end_angle = np.arctan2(self.end.Y - self.center.Y, self.end.X - self.center.X)

        # Ensure that the angles are in a counterclockwise direction
        if start_angle >= end_angle:
            end_angle += 2 * np.pi

        # Generate points on the arc
        theta = np.linspace(start_angle, end_angle, 100)
        arc_x = self.center.X + radius * np.cos(theta)
        arc_y = self.center.Y + radius * np.sin(theta)
        arc_z = np.linspace(self.start.Z, self.end.Z, len(arc_x))

        # Plot the arc
        if self.laser_on:
            ax.plot(arc_x, arc_y, arc_z, **LASER_ON_PLOT_STYLE, **plot_kwargs)
        else:
            ax.plot(arc_x, arc_y, arc_z, **LASER_OFF_PLOT_STYLE, **plot_kwargs)


def read_file(path) -> list[Movement]:
    path = Path(path)
    movements = []

    laser_on = False
    x, y, z = 0, 0, 0
    for line in path.read_text().split("\n"):
        # TODO: Laser power auslesen
        new_x, new_y, new_z = x, y, z
        if line.startswith("'"):
            # Skip comment
            continue
        elif "GALVO LASEROVERRIDE A ON" in line:
            laser_on = True
        elif "GALVO LASEROVERRIDE A OFF" in line:
            laser_on = False
        elif line.startswith("LINEAR"):
            op, *args = line.strip().split(" ")

            for arg in args:
                pos = float(arg[1:])
                ax = arg[0]

                if ax == "X":
                    new_x = pos
                elif ax == "Y":
                    new_y = pos
                elif ax == "Z":
                    new_z = pos
                elif ax == "F":
                    continue
                else:
                    raise RuntimeError(f"Did not recognize axis: {ax}")
            if x != 0 and y != 0:
                movements.append(LinearMovement(Point3D(x, y, z), Point3D(new_x, new_y, new_z), laser_on=laser_on))

        elif line.startswith("CW") or line.startswith("CCW"):
            op, *args = line.strip().split(" ")
            new_x, new_y, new_z = x, y, z
            circle_center = Point3D(x, y, z)
            axes = []
            for arg in args:
                pos = float(arg[1:])
                ax = arg[0]

                if ax == "X":
                    new_x = pos
                    axes.append("X")
                elif ax == "Y":
                    new_y = pos
                    axes.append("Y")
                elif ax == "Z":
                    new_z = pos
                    axes.append("Z")
                elif ax == "I":
                    # First axis
                    setattr(circle_center, axes[0], pos)
                elif ax == "J":
                    # Second axis
                    setattr(circle_center, axes[1], pos)
                elif ax == "F":
                    continue  # Speed doesnt matter atm
                elif ax == "R":
                    warnings.warn("Circle with radius not yet implemented")
                else:
                    raise RuntimeError(f"Did not recognize axis: {ax}")
            if op == "CW":
                movements.append(
                    ClockwiseMovement(
                        circle_center,
                        Point3D(x, y, z),
                        Point3D(new_x, new_y, new_z),
                        laser_on=laser_on
                    )
                )
            elif op == "CCW":
                movements.append(
                    CounterclockwiseMovement(
                        circle_center,
                        Point3D(x, y, z),
                        Point3D(new_x, new_y, new_z),
                        laser_on=laser_on
                    )
                )
            else:
                raise RuntimeError("Something bad happened...")
        x, y, z = new_x, new_y, new_z

    return movements


def plot_movements(movements, *, use_mu_m=True):
    # TODO: Laser power als Farbe
    fig = plt.figure()
    ax1 = fig.add_subplot(121, projection='3d')
    ax2 = fig.add_subplot(122, projection='3d')

    for movement in movements:
        movement.plot(ax1)
        movement.plot(ax2, linewidth=1)

    mm_to_um_formatter = FuncFormatter(lambda x, pos: f"{x * 1000:.1f}")
    for ax in [ax1, ax2]:
        if use_mu_m:
            ax.xaxis.set_major_formatter(mm_to_um_formatter)
            ax.yaxis.set_major_formatter(mm_to_um_formatter)
            ax.zaxis.set_major_formatter(mm_to_um_formatter)
            unit = "$\mu$m"
        else:
            unit = "mm"

        ax.set_xlabel(f"X [{unit}]")
        ax.set_ylabel(f"Y [{unit}]")
        ax.set_zlabel(f"Z [{unit}]")
        # TODO: Does not work
        # ax.xaxis.get_major_formatter().set_scientific(False)
        # ax.yaxis.get_major_formatter().set_scientific(False)
        # ax.zaxis.get_major_formatter().set_scientific(False)
    ax1.set_title("Real scale")
    ax2.set_title("Uneven scale")

    def on_move(event):
        if event.inaxes == ax1:
            azim, elev = ax1.azim, ax1.elev
            ax2.view_init(elev=elev, azim=azim)
        elif event.inaxes == ax2:
            azim, elev = ax2.azim, ax2.elev
            ax1.view_init(elev=elev, azim=azim)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect('motion_notify_event', on_move)

    fig.canvas.draw()
    xs, ys, zs = ax1.get_xlim(), ax1.get_ylim(), ax1.get_zlim()
    ax1.set_box_aspect((np.ptp(xs), np.ptp(ys), np.ptp(zs)))
    ax2.set_box_aspect((1, 1, 1))

    return fig
