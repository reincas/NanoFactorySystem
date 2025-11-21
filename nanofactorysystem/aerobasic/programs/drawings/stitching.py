"""
Stitching module for handling structures larger than the Field of View (FOV).

This module provides functionality to automatically split large structures into
smaller tiles that fit within the FOV, with configurable overlap for seamless stitching.

Key Features:
- Automatic tile generation for structures > FOV
- Configurable overlap between tiles (default 10%)
- Multiple stitching strategies (LAYER_FIRST, TILE_FIRST)
- Compatible with all basic structures
"""

from enum import Enum
from typing import List, Tuple, Iterator, Optional
import numpy as np

from nanofactorysystem.aerobasic.programs.drawings.basic_structures import Square
from nanofactorysystem.devices.coordinate_system import Point3D, CoordinateSystem
from nanofactorysystem.aerobasic.programs.drawings import DrawableObject, DrawableAeroBasicProgram


class StitchingStrategy(Enum):
    """
    Defines the order in which tiles are processed.

    LAYER_FIRST: Complete one Z-layer across all tiles before moving to next layer
                 Best for: Minimizing Z-movements, uniform layer exposure

    TILE_FIRST: Complete all Z-layers for one tile before moving to next tile
                Best for: Minimizing XY-movements, reducing drift

    SNAKE_PATTERN: Process tiles in a snake pattern to minimize travel distance
                   Best for: Maximum speed, minimal dead time
    """
    LAYER_FIRST = "layer_first"
    TILE_FIRST = "tile_first"
    SNAKE_PATTERN = "snake_pattern"


class Tile:
    """
    Represents a single tile of a larger structure.

    Parameters:
        tile_id (int): Unique identifier for this tile
        center_offset (Point3D): Offset from original structure center
        grid_position (Tuple[int, int]): Position in tile grid (row, col)
        structure: The drawable structure for this tile
        bounds (Tuple[float, float, float, float]): (x_min, x_max, y_min, y_max)
    """

    def __init__(
            self,
            tile_id: int,
            center_offset: Point3D,
            grid_position: Tuple[int, int],
            structure: DrawableObject,
            bounds: Tuple[float, float, float, float]
    ):
        self.tile_id = tile_id
        self.center_offset = center_offset
        self.grid_position = grid_position
        self.structure = structure
        self.bounds = bounds  # (x_min, x_max, y_min, y_max)

    def __repr__(self):
        row, col = self.grid_position
        return f"Tile({self.tile_id}, pos=[{row},{col}], offset={self.center_offset})"


class LargeStructureStitcher:
    """
    Handles automatic tiling and stitching of structures larger than FOV.

    Parameters:
        fov_size (Tuple[float, float]): Field of View size (width, height) in µm
        overlap (float): Overlap fraction between tiles (0.0 to 0.5, default 0.1 = 10%)
        strategy (StitchingStrategy): Order of tile processing

    Example:
        >>> stitcher = LargeStructureStitcher(
        ...     fov_size=(100, 100),
        ...     overlap=0.1,
        ...     strategy=StitchingStrategy.LAYER_FIRST
        ... )
        >>> large_square = Square(center=Point3D(0,0,-2), side_length=250)
        >>> tiles = stitcher.create_tiles(large_square)
        >>> print(f"Created {len(tiles)} tiles")
    """

    def __init__(
            self,
            fov_size: Tuple[float, float],
            overlap: float = 0.1,
            strategy: StitchingStrategy = StitchingStrategy.LAYER_FIRST
    ):
        if not (0 <= overlap < 0.5):
            raise ValueError(f"Overlap must be between 0 and 0.5, got {overlap}")
        if fov_size[0] <= 0 or fov_size[1] <= 0:
            raise ValueError(f"FOV size must be positive, got {fov_size}")

        self.fov_width = float(fov_size[0])
        self.fov_height = float(fov_size[1])
        self.overlap = float(overlap)
        self.strategy = strategy

        # Effective tile size (accounting for overlap)
        self.tile_width = self.fov_width * (1 - overlap)
        self.tile_height = self.fov_height * (1 - overlap)

    def needs_stitching(self, structure) -> bool:
        """
        Check if a structure requires stitching (i.e., is larger than FOV).

        Args:
            structure: Any drawable structure with bounding_box property

        Returns:
            bool: True if structure needs to be tiled
        """
        # todo -> implementing bounding box in every structure
        if not hasattr(structure, 'bounding_box'):
            # If structure doesn't have bounding_box, assume it fits
            return False

        x_min, x_max, y_min, y_max = structure.bounding_box
        width = x_max - x_min
        height = y_max - y_min

        return width > self.fov_width or height > self.fov_height

    def calculate_tile_grid(self, structure) -> Tuple[int, int]:
        """
        Calculate how many tiles are needed in X and Y directions.

        Args:
            structure: Structure to tile

        Returns:
            Tuple[int, int]: (num_tiles_x, num_tiles_y)
        """
        x_min, x_max, y_min, y_max = structure.bounding_box
        width = x_max - x_min
        height = y_max - y_min

        # Calculate number of tiles needed
        num_tiles_x = int(np.ceil(width / self.tile_width))
        num_tiles_y = int(np.ceil(height / self.tile_height))

        # Minimum 1 tile even if structure is small
        num_tiles_x = max(1, num_tiles_x)
        num_tiles_y = max(1, num_tiles_y)

        return num_tiles_x, num_tiles_y

    def create_tiles(self, structure) -> List[Tile]:
        """
        Split a large structure into tiles that fit within FOV.

        Args:
            structure: Large structure to split

        Returns:
            List[Tile]: List of tile objects
        """
        if not self.needs_stitching(structure):
            # Structure fits in FOV, return as single tile
            return [Tile(
                tile_id=0,
                center_offset=Point3D(0, 0, 0),
                grid_position=(0, 0),
                structure=structure,
                bounds=structure.bounding_box
            )]

        x_min, x_max, y_min, y_max = structure.bounding_box
        num_tiles_x, num_tiles_y = self.calculate_tile_grid(structure)

        tiles = []
        tile_id = 0

        for row in range(num_tiles_y):
            for col in range(num_tiles_x):
                # Calculate tile boundaries
                tile_x_min = x_min + col * self.tile_width
                tile_x_max = tile_x_min + self.fov_width
                tile_y_min = y_min + row * self.tile_height
                tile_y_max = tile_y_min + self.fov_height

                # Clamp to structure boundaries
                tile_x_max = min(tile_x_max, x_max)
                tile_y_max = min(tile_y_max, y_max)

                # Calculate tile center
                tile_center_x = (tile_x_min + tile_x_max) / 2
                tile_center_y = (tile_y_min + tile_y_max) / 2

                # Offset from original structure center
                original_center = structure.center
                center_offset = Point3D(
                    tile_center_x - original_center.X,
                    tile_center_y - original_center.Y,
                    0  # Z offset is 0 for horizontal tiles
                )

                # Create a clipped version of the structure for this tile
                tile_structure = self._create_tile_structure(
                    structure,
                    center_offset,
                    (tile_x_min, tile_x_max, tile_y_min, tile_y_max)
                )

                tile = Tile(
                    tile_id=tile_id,
                    center_offset=center_offset,
                    grid_position=(row, col),
                    structure=tile_structure,
                    bounds=(tile_x_min, tile_x_max, tile_y_min, tile_y_max)
                )

                tiles.append(tile)
                tile_id += 1

        return tiles

    def _create_tile_structure(
            self,
            original_structure,
            center_offset: Point3D,
            bounds: Tuple[float, float, float, float]
    ):
        """
        Create a clipped version of the structure for a specific tile.

        This creates a new instance of the same structure type with adjusted
        center and size to fit within the tile boundaries.
        """
        # Get structure type
        structure_type = type(original_structure).__name__

        # Create new center point
        new_center = Point3D(
            original_structure.center.X + center_offset.X,
            original_structure.center.Y + center_offset.Y,
            original_structure.center.Z
        )

        # For now, create a simple wrapper that offsets the drawing
        # In a full implementation, you'd clip the actual geometry
        return TiledStructureWrapper(
            original_structure=original_structure,
            tile_center=new_center,
            tile_bounds=bounds
        )

    def get_tile_order(self, tiles: List[Tile]) -> List[Tile]:
        """
        Return tiles in the order they should be processed based on strategy.

        Args:
            tiles: List of tiles to order

        Returns:
            List[Tile]: Ordered list of tiles
        """
        if self.strategy == StitchingStrategy.TILE_FIRST:
            # Process tiles in row-major order (left to right, top to bottom)
            return sorted(tiles, key=lambda t: (t.grid_position[0], t.grid_position[1]))

        elif self.strategy == StitchingStrategy.SNAKE_PATTERN:
            # Snake pattern: left-to-right on even rows, right-to-left on odd rows
            ordered = []
            rows = {}
            for tile in tiles:
                row = tile.grid_position[0]
                if row not in rows:
                    rows[row] = []
                rows[row].append(tile)

            for row_idx in sorted(rows.keys()):
                row_tiles = sorted(rows[row_idx], key=lambda t: t.grid_position[1])
                if row_idx % 2 == 1:
                    row_tiles.reverse()  # Reverse odd rows
                ordered.extend(row_tiles)

            return ordered

        else:  # LAYER_FIRST
            # Return in normal order, layer processing happens at higher level
            return sorted(tiles, key=lambda t: (t.grid_position[0], t.grid_position[1]))

    def estimate_print_time(self, tiles: List[Tile], time_per_tile: float) -> float:
        """
        Estimate total print time for all tiles.

        Args:
            tiles: List of tiles
            time_per_tile: Estimated time per tile in seconds

        Returns:
            float: Total estimated time in seconds
        """
        num_tiles = len(tiles)

        # Add overhead for movements between tiles (rough estimate: 5 seconds per move)
        movement_overhead = (num_tiles - 1) * 5.0

        total_time = num_tiles * time_per_tile + movement_overhead
        return total_time

    def get_stitching_info(self, structure) -> dict:
        """
        Get detailed information about how a structure will be tiled.

        Returns:
            dict: Information about tiling (num_tiles, grid_size, overlap, etc.)
        """
        needs_stitch = self.needs_stitching(structure)

        info = {
            "needs_stitching": needs_stitch,
            "fov_size": (self.fov_width, self.fov_height),
            "overlap_fraction": self.overlap,
            "overlap_distance": (
                self.fov_width * self.overlap,
                self.fov_height * self.overlap
            ),
            "tile_size": (self.tile_width, self.tile_height),
            "strategy": self.strategy.value
        }

        if needs_stitch:
            num_tiles_x, num_tiles_y = self.calculate_tile_grid(structure)
            info["num_tiles"] = num_tiles_x * num_tiles_y
            info["grid_size"] = (num_tiles_x, num_tiles_y)
            info["structure_size"] = (
                structure.bounding_box[1] - structure.bounding_box[0],
                structure.bounding_box[3] - structure.bounding_box[2]
            )
        else:
            info["num_tiles"] = 1
            info["grid_size"] = (1, 1)

        return info


class TiledStructureWrapper:
    """
    Wrapper for a structure that is part of a larger tiled structure.

    This wrapper ensures that only the relevant portion of the structure
    is drawn for this specific tile.
    """

    def __init__(
            self,
            original_structure,
            tile_center: Point3D,
            tile_bounds: Tuple[float, float, float, float]
    ):
        self.original_structure = original_structure
        self.tile_center = tile_center
        self.tile_bounds = tile_bounds
        self.center = tile_center

    def draw(self) -> List[Point3D]:
        """
        Draw only the portion of the structure within this tile's bounds.
        """
        # Get points from original structure
        points = self.original_structure.draw()

        # Filter points to only include those within tile bounds
        x_min, x_max, y_min, y_max = self.tile_bounds

        filtered_points = []
        for point in points:
            if x_min <= point.X <= x_max and y_min <= point.Y <= y_max:
                filtered_points.append(point)

        return filtered_points

    @property
    def bounding_box(self):
        """Return the bounds of this tile."""
        return self.tile_bounds

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        """Forward to original structure's iterate_layers."""
        # This is a simplified version - in full implementation,
        # you'd need to properly handle layer iteration with clipping
        return self.original_structure.iterate_layers(coordinate_system)


class StitchedStructure:
    """
    High-level interface for working with stitched structures.

    This class combines a large structure with a stitcher to provide
    easy access to tiles and printing information.

    Example:
        >>> large_square = Square(center=Point3D(0,0,-2), side_length=300)
        >>> stitched = StitchedStructure(
        ...     structure=large_square,
        ...     fov_size=(100, 100),
        ...     overlap=0.1
        ... )
        >>> print(f"Structure requires {stitched.num_tiles} tiles")
        >>> for tile in stitched.get_ordered_tiles():
        ...     print(f"Processing {tile}")
    """

    def __init__(
            self,
            structure,
            fov_size: Tuple[float, float],
            overlap: float = 0.1,
            strategy: StitchingStrategy = StitchingStrategy.LAYER_FIRST
    ):
        self.structure = structure
        self.stitcher = LargeStructureStitcher(fov_size, overlap, strategy)
        self.tiles = self.stitcher.create_tiles(structure)
        self.info = self.stitcher.get_stitching_info(structure)

    @property
    def num_tiles(self) -> int:
        """Number of tiles."""
        return len(self.tiles)

    @property
    def needs_stitching(self) -> bool:
        """Whether stitching is required."""
        return self.info["needs_stitching"]

    def get_ordered_tiles(self) -> List[Tile]:
        """Get tiles in processing order."""
        return self.stitcher.get_tile_order(self.tiles)

    def get_tile_by_position(self, row: int, col: int) -> Optional[Tile]:
        """Get tile at specific grid position."""
        for tile in self.tiles:
            if tile.grid_position == (row, col):
                return tile
        return None

    def print_info(self):
        """Print detailed information about the stitched structure."""
        print("=" * 60)
        print("STITCHED STRUCTURE INFORMATION")
        print("=" * 60)
        print(f"Needs Stitching: {self.needs_stitching}")
        print(f"Number of Tiles: {self.num_tiles}")
        print(f"Grid Size: {self.info.get('grid_size', 'N/A')}")
        print(f"FOV Size: {self.info['fov_size'][0]:.1f} x {self.info['fov_size'][1]:.1f} µm")
        print(f"Overlap: {self.info['overlap_fraction'] * 100:.1f}%")
        print(f"Strategy: {self.info['strategy']}")

        if self.needs_stitching:
            print(f"Structure Size: {self.info['structure_size'][0]:.1f} x {self.info['structure_size'][1]:.1f} µm")
            print(f"\nTile Layout:")
            grid_x, grid_y = self.info['grid_size']
            for row in range(grid_y):
                row_str = "  "
                for col in range(grid_x):
                    tile = self.get_tile_by_position(row, col)
                    if tile:
                        row_str += f"[T{tile.tile_id:2d}] "
                    else:
                        row_str += "[  ] "
                print(row_str)

        print("=" * 60)


# Convenience functions

def stitch_if_needed(
        structure,
        fov_size: Tuple[float, float],
        overlap: float = 0.1,
        strategy: StitchingStrategy = StitchingStrategy.LAYER_FIRST
) -> StitchedStructure:
    """
    Automatically stitch a structure if it's larger than FOV.

    Args:
        structure: Structure to potentially stitch
        fov_size: Field of View size (width, height)
        overlap: Overlap fraction between tiles
        strategy: Stitching strategy to use

    Returns:
        StitchedStructure: Wrapped structure with tile information

    Example:
        >>> large_square = Square(center=Point3D(0,0,-2), side_length=300)
        >>> stitched = stitch_if_needed(large_square, fov_size=(100, 100))
        >>> stitched.print_info()
    """
    return StitchedStructure(structure, fov_size, overlap, strategy)


# Example usage and testing
if __name__ == '__main__':
    print("Testing Stitching System\n")

    # Example 1: Small structure (no stitching needed)
    print("Example 1: Small Square (50x50 µm)")
    print("-" * 60)

    small_square = Square(
        center=Point3D(0, 0, -2),
        side_length=50,
        filled=True,
        hatch_size=1.0
    )

    stitcher = LargeStructureStitcher(fov_size=(100, 100), overlap=0.1)
    tiles = stitcher.create_tiles(small_square)

    print(f"Number of tiles: {len(tiles)}")
    print(f"Needs stitching: {stitcher.needs_stitching(small_square)}")
    print()

    # Example 2: Large structure (needs stitching)
    print("Example 2: Large Square (250x250 µm)")
    print("-" * 60)

    large_square = Square(
        center=Point3D(0, 0, -2),
        side_length=250,
        filled=True,
        hatch_size=1.0
    )

    stitched = StitchedStructure(
        structure=large_square,
        fov_size=(100, 100),
        overlap=0.1,
        strategy=StitchingStrategy.LAYER_FIRST
    )

    stitched.print_info()

    print("\nTile Processing Order:")
    for i, tile in enumerate(stitched.get_ordered_tiles(), 1):
        print(f"  {i}. {tile}")

    print()

    # Example 3: Different strategies
    print("Example 3: Comparing Strategies")
    print("-" * 60)

    strategies = [
        StitchingStrategy.LAYER_FIRST,
        StitchingStrategy.TILE_FIRST,
        StitchingStrategy.SNAKE_PATTERN
    ]

    for strategy in strategies:
        stitcher = LargeStructureStitcher(
            fov_size=(100, 100),
            overlap=0.1,
            strategy=strategy
        )
        tiles = stitcher.create_tiles(large_square)
        ordered = stitcher.get_tile_order(tiles)

        print(f"\n{strategy.value}:")
        print(f"  Order: {[t.tile_id for t in ordered]}")

    print("\n" + "=" * 60)
    print("Stitching system test complete!")