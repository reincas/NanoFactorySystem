from dataclasses import dataclass

import numpy as np

from nanofactorysystem.devices.coordinate_system import Point3D, Point2D


class TileManager:
    def __init__(self,
                 structure_size: tuple | list,
                 fov: tuple | float | int,
                 usable_fraction: float,
                 center: Point2D | Point3D = Point3D(X=0, Y=0, Z=0)):
        """
        structure_size: tuple
        """
        self.center = center  # Note: really necessary?
        self.center_point = np.array((center.X, center.Y))  # x,y coordinate as array for calculations

        self.structure_size = np.array(structure_size)

        if isinstance(fov, tuple):
            self.fov = np.array(fov)
        elif isinstance(fov, float) or isinstance(fov, int):
            self.fov = np.array((float(fov), float(fov)))
        else:
            raise TypeError('fov must be tuple or float|int')

        if isinstance(usable_fraction, float):
            self.usable_fraction = np.array((usable_fraction, usable_fraction))
        elif isinstance(usable_fraction, int):
            self.usable_fraction = np.array((float(usable_fraction) / 100, float(usable_fraction) / 100))
        elif isinstance(usable_fraction, tuple):
            # todo check if entries of tuple are float
            self.usable_fraction = np.array(usable_fraction)
        else:
            raise TypeError("usable_fraction must be float, int or tuple(float,float).")

        self.fov_use = self.fov * self.usable_fraction

        self.n_tiles = None  # initialisation of number of tiles
        self.length_border_tiles = None  # initialisation of filling of border tiles
        self.offset_border_tiles = None  # initialisation of offset from center of border tiles

    def _create_direction_grid(self, n_x, n_y):
        # x-Werte: +1 am Anfang, -1 am Ende, 0 dazwischen
        x_vals = np.zeros(n_x)
        x_vals[0] = 1
        x_vals[-1] = -1

        # y-Werte: +1 oben, -1 unten, 0 dazwischen
        y_vals = np.zeros(n_y)
        y_vals[0] = 1
        y_vals[-1] = -1

        # Broadcasting: x über alle Zeilen, y über alle Spalten
        x_grid = np.broadcast_to(x_vals, (n_y, n_x))
        y_grid = np.broadcast_to(y_vals[:, np.newaxis], (n_y, n_x))

        return np.stack([x_grid, y_grid], axis=-1)

    def get_fov(self):
        return self.fov_use

    def get_usable_fraction(self):
        return self.usable_fraction

    def get_structure_size(self):
        return self.structure_size

    def needs_stitching(self) -> bool:
        """Check if structure needs stitching"""
        bool_array = self.structure_size > self.fov_use
        stitching = True if bool_array.any() == True else False
        return stitching

    def calc_parameters(self):  # -> List[TileBounds]:
        # number of structures
        self.n_tiles = np.ceil(self.structure_size / self.fov_use)  # (n_tiles_x, n_tiles_y)
        # length of filling of usable field of view at the border of tiles
        self.length_border_tiles = (self.structure_size - (self.n_tiles - 2) * self.fov_use) / 2
        # offset of the border tiles from center - correct sign of x and y coordinate has to put in manually
        self.offset_border_tiles = self.fov_use / 2 - self.length_border_tiles / 2

    def generate_tiles(self):
        """
        Example of subdivision of structure; C indicating default center_point
            ---------------------
            | 1 | 2 | 3 | 4 | 5 |
            ---------------------
            | 6 |   | C |   |   |
            ---------------------
            |11 |   |   |   |   |
            ---------------------

            -> boundaries of structure in regard to the tile center point is necessary
        """
        tiles = []
        start_point = self.center_point - (self.fov_use * (self.n_tiles - 1) / 2)
        factor_structure_point = self._create_direction_grid(self.n_tiles[0], self.n_tiles[1])
        # iteration over columns
        for j in range(int(self.n_tiles[1])):
            # iteration over rows
            for i in range(int(self.n_tiles[0])):
                # center point of the tile in reference to self.center_point(C - whole structure)
                center_point_tile = start_point + np.array((i, j)) * self.fov_use
                # center point of the structure in ref. to center point of tile therefore ref. to center_point of whole structure
                center_point_structure = center_point_tile + factor_structure_point[i][j] * self.offset_border_tiles
                offset_structure = factor_structure_point[i][j] * self.offset_border_tiles

                # boundaries of the structure with ref. to self.center_point
                # [x_min, x_max, y_min, y_max]
                boundaries_structure_absolut = [
                    center_point_structure[0] - self.length_border_tiles[0] / 2 if i == 0 else center_point_structure[
                                                                                                   0] - self.fov_use[
                                                                                                   0] / 2,
                    center_point_structure[0] + self.length_border_tiles[0] / 2 if i == 0 else center_point_structure[
                                                                                                   0] + self.fov_use[
                                                                                                   0] / 2,
                    center_point_structure[1] - self.length_border_tiles[1] / 2 if j == 0
                        else center_point_structure[1] - self.fov_use[1] / 2,
                    center_point_structure[1] + self.length_border_tiles[1] / 2 if i == 0 else center_point_structure[
                                                                                                   1] + self.fov_use[
                                                                                                   1] / 2]
                boundaries_structure_realtive_tile_center = [
                    offset_structure[0] - self.length_border_tiles[0] / 2 if i == 0 else offset_structure[
                                                                                                   0] - self.fov_use[
                                                                                                   0] / 2,
                    offset_structure[0] + self.length_border_tiles[0] / 2 if i == 0 else offset_structure[
                                                                                                   0] + self.fov_use[
                                                                                                   0] / 2,
                    offset_structure[1] - self.length_border_tiles[1] / 2 if j == 0
                        else offset_structure[1] - self.fov_use[1] / 2,
                    offset_structure[1] + self.length_border_tiles[1] / 2 if i == 0 else offset_structure[
                                                                                                   1] + self.fov_use[
                                                                                                   1] / 2]
                boundaries_tile = [
                    center_point_tile[0] - self.length_border_tiles[0] / 2 if i == 0 else center_point_tile[0] -
                                                                                          self.fov_use[0] / 2,
                    center_point_tile[0] + self.length_border_tiles[0] / 2 if i == 0 else center_point_tile[0] +
                                                                                          self.fov_use[0] / 2,
                    center_point_tile[1] - self.length_border_tiles[1] / 2 if i == 0 else center_point_tile[1] -
                                                                                          self.fov_use[1] / 2,
                    center_point_tile[1] + self.length_border_tiles[1] / 2 if i == 0 else center_point_tile[1] +
                                                                                          self.fov_use[1] / 2]




@dataclass
class Tile:
    """Bounds for a single tile"""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    center_x: float
    center_y: float

    @property
    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.x_min, self.x_max, self.y_min, self.y_max)


if __name__ == "__main__":
    pass
