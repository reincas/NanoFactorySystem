"""
TileAwareSlicer Module
======================
Slicing engine that works on a per-tile basis for efficient large-structure fabrication.

Uses standalone modules:
- hatch_generator.py
- laser_segments.py

Author: Hannes Robben / Claude
Date: 2025
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable, Dict, Any
import numpy as np

# Import from standalone modules
from ..laser_segments import LaserSegment
from ..hatch_generator import HatchGenerator, HatchConfig


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class SlicerConfig:
    """Configuration for the tile-aware slicer"""
    
    # Layer parameters
    slice_size: float                   # Distance between Z layers
    
    # Hatching parameters  
    hatch_size: float                   # Distance between hatch lines
    hatch_angle_deg: float = 0.0        # Base hatch angle
    alternating_hatch: bool = True      # Alternate hatch angle each layer
    hatch_angle_increment: float = 90.0 # Angle increment when alternating
    
    # Motion parameters
    velocity: float = 10000.0           # Writing velocity (µm/s)
    acceleration: float = 100000.0      # Acceleration (µm/s²)
    
    # Grid resolution for mask generation
    grid_resolution: int = 500          # Points per dimension for evaluation
    
    # Polygon extraction
    min_polygon_area: int = 10          # Minimum polygon area in pixels
    
    # Optimization
    optimize_hatch_count: bool = True   # Adjust hatch_size for even line count


@dataclass
class SliceResult:
    """Result of slicing a single layer"""
    z_level: float
    z_absolute: float  # Z level in absolute coordinates (includes base_z)
    segments: List[LaserSegment]
    hatch_angle: float
    tile_index: Optional[Tuple[int, int]] = None
    
    @property
    def n_segments(self) -> int:
        return len(self.segments)
    
    @property
    def is_empty(self) -> bool:
        return len(self.segments) == 0


@dataclass 
class TileSliceResult:
    """Complete slicing result for a single tile"""
    tile_index: Tuple[int, int]
    tile_center: Tuple[float, float]  # Absolute center for stage positioning
    structure_bounds: Dict[str, float]  # Relative bounds within tile
    slices: List[SliceResult]
    
    @property
    def n_layers(self) -> int:
        return len(self.slices)
    
    @property
    def n_total_segments(self) -> int:
        return sum(s.n_segments for s in self.slices)


# =============================================================================
# TILE-AWARE SLICER
# =============================================================================

class TileAwareSlicer:
    """
    Slicing engine that processes structures on a per-tile basis.
    
    Workflow:
    1. Receive tile info from TileManager
    2. For each tile:
       a. Create evaluation grid for structure bounds (NOT full tile)
       b. Evaluate height function
       c. Apply aperture
       d. For each Z-level:
          - Generate mask (z >= z_level)
          - Extract polygons from mask
          - Generate hatch segments
          - Apply clipping to structure bounds
    3. Return SliceResults for each tile/layer combination
    
    Important: Works in TILE-RELATIVE coordinates!
    """
    
    def __init__(self, config: SlicerConfig):
        self.config = config
    
    def slice_tile(
        self,
        tile_info: Dict[str, Any],
        height_func: Callable[[np.ndarray, np.ndarray], np.ndarray],
        z_min: float,
        z_max: float,
        base_z: float = 0.0,
        aperture: Optional[Callable[[np.ndarray, np.ndarray], np.ndarray]] = None
    ) -> TileSliceResult:
        """
        Slice a single tile through all Z-levels.
        
        Args:
            tile_info: Tile dictionary from TileManager.get_tile_dict()
            height_func: Function z = f(X, Y) for height evaluation
            z_min: Minimum Z value of structure
            z_max: Maximum Z value of structure
            base_z: Base Z offset
            aperture: Optional aperture function
            
        Returns:
            TileSliceResult containing all layers for this tile
        """
        cfg = self.config
        
        # Extract tile info
        tile_index = tile_info['index']
        tile_center = tuple(tile_info['center_tile'])
        bounds = tile_info['structure_bounds_relative']
        
        x_min, x_max = bounds['x_min'], bounds['x_max']
        y_min, y_max = bounds['y_min'], bounds['y_max']
        
        # Create evaluation grid
        xs = np.linspace(x_min, x_max, cfg.grid_resolution)
        ys = np.linspace(y_min, y_max, cfg.grid_resolution)
        X, Y = np.meshgrid(xs, ys)
        
        # Evaluate height function
        Z = height_func(X, Y)
        
        # Apply aperture if provided
        if aperture is not None:
            aperture_mask = aperture(X, Y)
            Z = np.where(aperture_mask, Z, np.nan)
        
        # Calculate Z-levels
        n_slices = max(1, round((z_max - z_min) / cfg.slice_size))
        z_levels = np.linspace(z_min, z_max, n_slices + 1)
        
        # Process each Z-level
        slices = []
        for i, z_level in enumerate(z_levels):
            # Calculate hatch angle
            if cfg.alternating_hatch:
                hatch_angle = cfg.hatch_angle_deg + i * cfg.hatch_angle_increment
            else:
                hatch_angle = cfg.hatch_angle_deg
            
            # Generate mask
            mask = (Z >= z_level) & ~np.isnan(Z)
            
            # Create HatchGenerator for this layer
            hatch_config = HatchConfig(
                hatch_size=cfg.hatch_size,
                hatch_angle_deg=hatch_angle,
                optimize_line_count=cfg.optimize_hatch_count,
                clip_bounds=(x_min, x_max, y_min, y_max)
            )
            hatch_gen = HatchGenerator(hatch_config)
            
            # Generate segments from mask
            z_absolute = base_z + z_level
            segments = hatch_gen.hatch_from_mask(
                mask=mask,
                x_range=(x_min, x_max),
                y_range=(y_min, y_max),
                z_level=z_absolute,
                min_area=cfg.min_polygon_area
            )
            
            slices.append(SliceResult(
                z_level=z_level,
                z_absolute=z_absolute,
                segments=segments,
                hatch_angle=hatch_angle,
                tile_index=tile_index
            ))
        
        return TileSliceResult(
            tile_index=tile_index,
            tile_center=tile_center,
            structure_bounds=bounds,
            slices=slices
        )
    
    def slice_all_tiles(
        self,
        tiles: List[Dict[str, Any]],
        height_func: Callable,
        z_min: float,
        z_max: float,
        base_z: float = 0.0,
        aperture: Optional[Callable] = None
    ) -> List[TileSliceResult]:
        """
        Slice all tiles from a TileManager.
        """
        results = []
        for tile_info in tiles:
            result = self.slice_tile(
                tile_info=tile_info,
                height_func=height_func,
                z_min=z_min,
                z_max=z_max,
                base_z=base_z,
                aperture=aperture
            )
            results.append(result)
        return results
    
    def slice_single_tile_mode(
        self,
        x_range: Tuple[float, float],
        y_range: Tuple[float, float],
        height_func: Callable,
        z_min: float,
        z_max: float,
        base_z: float = 0.0,
        aperture: Optional[Callable] = None
    ) -> TileSliceResult:
        """
        Slice for single-tile mode (no stitching needed).
        """
        x_min, x_max = x_range
        y_min, y_max = y_range
        
        virtual_tile = {
            'index': (0, 0),
            'center_tile': np.array([(x_min + x_max) / 2, (y_min + y_max) / 2]),
            'structure_bounds_relative': {
                'x_min': -(x_max - x_min) / 2,
                'x_max': (x_max - x_min) / 2,
                'y_min': -(y_max - y_min) / 2,
                'y_max': (y_max - y_min) / 2
            }
        }
        
        cx, cy = (x_min + x_max) / 2, (y_min + y_max) / 2
        
        def height_func_relative(X, Y):
            return height_func(X + cx, Y + cy)
        
        if aperture is not None:
            def aperture_relative(X, Y):
                return aperture(X + cx, Y + cy)
        else:
            aperture_relative = None
        
        return self.slice_tile(
            tile_info=virtual_tile,
            height_func=height_func_relative,
            z_min=z_min,
            z_max=z_max,
            base_z=base_z,
            aperture=aperture_relative
        )
