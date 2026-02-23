"""
LaserSegments Module
====================
Standalone module for handling discontinuous laser paths in 2PP fabrication.

Can be used with ANY drawable structure that needs laser on/off control:
- HeightFunctionStructures (Gratings, Lenses)
- Rectangle3D with aperture
- Complex polygon fills
- Future STL-based structures

Unlike PolyLines (which keeps laser ON between all points), LaserSegments
handles individual line segments with laser OFF during travel moves.

Usage:
    from nanofactorysystem.aerobasic.programs.drawings.laser_segments import (
        LaserSegments, LaserSegmentsConfig, LaserSegment
    )
    
    segments = LaserSegments(
        segments=[LaserSegment((0,0,0), (10,0,0)), ...],
        config=LaserSegmentsConfig(velocity=10000, acceleration=100000)
    )

Author: Hannes Robben / Claude
Date: 2025
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Iterator, Dict, Union
from enum import Enum
import numpy as np

from nanofactorysystem.aerobasic import GalvoLaserOverrideMode
from nanofactorysystem.aerobasic.programs.drawings.base import DrawableAeroBasicProgram, DrawableObject
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point2D, Point3D


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class LaserSegment:
    """
    A single laser-on segment defined by start and end points.
    
    Attributes:
        start: Starting point (x, y, z)
        end: Ending point (x, y, z)
        
    The laser is ON while moving from start to end.
    """
    start: Tuple[float, float, float]
    end: Tuple[float, float, float]
    
    @property
    def start_2d(self) -> Tuple[float, float]:
        return (self.start[0], self.start[1])
    
    @property
    def end_2d(self) -> Tuple[float, float]:
        return (self.end[0], self.end[1])
    
    @property
    def z(self) -> float:
        """Z-level (assumes constant Z for segment)"""
        return self.start[2]
    
    @property
    def length(self) -> float:
        """Euclidean length of segment"""
        return np.sqrt(
            (self.end[0] - self.start[0])**2 +
            (self.end[1] - self.start[1])**2 +
            (self.end[2] - self.start[2])**2
        )
    
    @property
    def length_2d(self) -> float:
        """2D length (ignoring Z)"""
        return np.sqrt(
            (self.end[0] - self.start[0])**2 +
            (self.end[1] - self.start[1])**2
        )
    
    def reversed(self) -> 'LaserSegment':
        """Return segment with swapped start/end"""
        return LaserSegment(start=self.end, end=self.start)
    
    def distance_to_point(self, point: Tuple[float, float]) -> float:
        """Distance from segment's end to a 2D point"""
        return np.sqrt(
            (self.end[0] - point[0])**2 +
            (self.end[1] - point[1])**2
        )
    
    def __repr__(self) -> str:
        return f"LaserSegment({self.start} → {self.end})"


class SortingStrategy(Enum):
    """Strategy for ordering segments"""
    NONE = "none"                    # Keep original order
    SERPENTINE = "serpentine"        # Serpentine (zig-zag) pattern
    NEAREST_NEIGHBOR = "nearest"     # Greedy nearest neighbor
    

@dataclass
class LaserSegmentsConfig:
    """Configuration for LaserSegments behavior"""
    velocity: float                         # Writing velocity (µm/s)
    acceleration: float                     # Acceleration (µm/s²)
    travel_velocity: Optional[float] = None # Travel velocity (default: same as writing)
    
    # Acceleration distance handling
    use_acceleration_distance: bool = True
    acceleration_distance_factor: float = 2.0
    
    # Sorting
    sorting_strategy: SortingStrategy = SortingStrategy.SERPENTINE
    
    # FOV bounds for acceleration (optional)
    fov_bounds: Optional[Tuple[float, float, float, float]] = None  # (x_min, x_max, y_min, y_max)
    
    def __post_init__(self):
        if self.travel_velocity is None:
            self.travel_velocity = self.velocity


# =============================================================================
# LASER SEGMENTS CLASS
# =============================================================================

class LaserSegments(DrawableObject):
    """
    Collection of laser segments with optimized traversal.
    
    Key features:
    - Laser OFF during travel between segments
    - Serpentine/optimized ordering
    - Acceleration distance handling at FOV boundaries
    
    Usage:
        segments = LaserSegments(
            segments=[
                LaserSegment((0, 0, 0), (10, 0, 0)),
                LaserSegment((0, 1, 0), (10, 1, 0)),
            ],
            config=LaserSegmentsConfig(velocity=10000, acceleration=100000)
        )
        
        for program in segments.iterate_layers(coordinate_system):
            # Execute program...
    """
    
    def __init__(
        self,
        segments: List[LaserSegment],
        config: LaserSegmentsConfig
    ):
        super().__init__()
        self.segments = segments
        self.config = config
        self._sorted_segments: Optional[List[LaserSegment]] = None
    
    @property
    def center_point(self) -> Point2D:
        """Calculate center point of all segments"""
        if not self.segments:
            return Point2D(0, 0)
        
        all_x = []
        all_y = []
        for seg in self.segments:
            all_x.extend([seg.start[0], seg.end[0]])
            all_y.extend([seg.start[1], seg.end[1]])
        
        return Point2D(
            (min(all_x) + max(all_x)) / 2,
            (min(all_y) + max(all_y)) / 2
        )
    
    @property
    def z_level(self) -> float:
        """Get Z-level (assumes all segments at same Z)"""
        if not self.segments:
            return 0.0
        return self.segments[0].z
    
    @property 
    def bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box (x_min, x_max, y_min, y_max)"""
        if not self.segments:
            return (0, 0, 0, 0)
        
        all_x = []
        all_y = []
        for seg in self.segments:
            all_x.extend([seg.start[0], seg.end[0]])
            all_y.extend([seg.start[1], seg.end[1]])
        
        return (min(all_x), max(all_x), min(all_y), max(all_y))
    
    def _calculate_acceleration_distance(self) -> float:
        """Calculate acceleration distance based on velocity and acceleration"""
        if not self.config.use_acceleration_distance:
            return 0.0
        
        # d = factor * v² / (2 * a)
        return (
            self.config.acceleration_distance_factor * 
            self.config.velocity ** 2 / 
            (2 * self.config.acceleration)
        )
    
    def _sort_segments_serpentine(self) -> List[LaserSegment]:
        """
        Sort segments in serpentine pattern.
        
        Assumes segments are already grouped by hatch lines.
        Alternates direction each row for efficient traversal.
        """
        if not self.segments:
            return []
        
        # Group segments by their Y-coordinate (with tolerance)
        segments_by_row: Dict[float, List[LaserSegment]] = {}
        tolerance = 1e-6
        
        for seg in self.segments:
            # Use midpoint Y for grouping
            mid_y = (seg.start[1] + seg.end[1]) / 2
            
            # Find matching row
            matched = False
            for row_y in segments_by_row.keys():
                if abs(mid_y - row_y) < tolerance:
                    segments_by_row[row_y].append(seg)
                    matched = True
                    break
            
            if not matched:
                segments_by_row[mid_y] = [seg]
        
        # Sort rows by Y
        sorted_rows = sorted(segments_by_row.keys())
        
        result = []
        reverse_row = False
        
        for row_y in sorted_rows:
            row_segments = segments_by_row[row_y]
            
            # Sort segments in row by X of start point
            row_segments.sort(key=lambda s: s.start[0])
            
            if reverse_row:
                # Reverse both order and direction of each segment
                row_segments = [s.reversed() for s in reversed(row_segments)]
            
            result.extend(row_segments)
            reverse_row = not reverse_row
        
        return result
    
    def _sort_segments_nearest_neighbor(self) -> List[LaserSegment]:
        """
        Sort segments using greedy nearest-neighbor algorithm.
        
        Starts from (0, 0) and always picks the segment whose start
        is closest to the current position.
        """
        if not self.segments:
            return []
        
        remaining = list(self.segments)
        result = []
        current_pos = (0.0, 0.0)
        
        while remaining:
            # Find nearest segment (considering both orientations)
            best_seg = None
            best_dist = float('inf')
            best_reversed = False
            
            for seg in remaining:
                # Distance to start
                dist_start = np.sqrt(
                    (seg.start[0] - current_pos[0])**2 +
                    (seg.start[1] - current_pos[1])**2
                )
                # Distance to end (if we reverse)
                dist_end = np.sqrt(
                    (seg.end[0] - current_pos[0])**2 +
                    (seg.end[1] - current_pos[1])**2
                )
                
                if dist_start < best_dist:
                    best_dist = dist_start
                    best_seg = seg
                    best_reversed = False
                
                if dist_end < best_dist:
                    best_dist = dist_end
                    best_seg = seg
                    best_reversed = True
            
            remaining.remove(best_seg)
            
            if best_reversed:
                best_seg = best_seg.reversed()
            
            result.append(best_seg)
            current_pos = best_seg.end_2d
        
        return result
    
    def get_sorted_segments(self) -> List[LaserSegment]:
        """Get segments in optimized order based on sorting strategy"""
        if self._sorted_segments is not None:
            return self._sorted_segments
        
        if self.config.sorting_strategy == SortingStrategy.NONE:
            self._sorted_segments = self.segments
        elif self.config.sorting_strategy == SortingStrategy.SERPENTINE:
            self._sorted_segments = self._sort_segments_serpentine()
        elif self.config.sorting_strategy == SortingStrategy.NEAREST_NEIGHBOR:
            self._sorted_segments = self._sort_segments_nearest_neighbor()
        else:
            self._sorted_segments = self.segments
        
        return self._sorted_segments
    
    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        """
        Generate AeroBasic program for all segments.
        
        Workflow:
        1. Move to start of first segment (Laser OFF)
        2. For each segment:
           a. Move to start (Laser OFF, with acceleration distance if needed)
           b. Turn Laser ON
           c. Move to end
           d. Turn Laser OFF
        3. Add deceleration distance after last segment
        
        Yields single program containing all segments at this Z-level.
        """
        sorted_segments = self.get_sorted_segments()
        
        if not sorted_segments:
            return
        
        program = DrawableAeroBasicProgram(coordinate_system)
        accel_dist = self._calculate_acceleration_distance()
        
        # Process segments
        prev_end = None
        
        for i, segment in enumerate(sorted_segments):
            is_first = (i == 0)
            is_last = (i == len(sorted_segments) - 1)
            
            # Calculate direction vector for acceleration handling
            dx = segment.end[0] - segment.start[0]
            dy = segment.end[1] - segment.start[1]
            length = np.sqrt(dx**2 + dy**2)
            
            if length > 1e-9:
                dir_x = dx / length
                dir_y = dy / length
            else:
                dir_x, dir_y = 1.0, 0.0
            
            # Move to pre-start position (for acceleration)
            if accel_dist > 0 and is_first:
                pre_start_x = segment.start[0] - dir_x * accel_dist
                pre_start_y = segment.start[1] - dir_y * accel_dist
                program.LINEAR(
                    X=pre_start_x, Y=pre_start_y, Z=segment.z,
                    F=self.config.travel_velocity
                )
            elif prev_end is not None:
                # Just travel to start (Laser already OFF)
                program.LINEAR(
                    X=segment.start[0], Y=segment.start[1], Z=segment.z,
                    F=self.config.travel_velocity
                )
            else:
                # First segment, no accel distance
                program.LINEAR(
                    X=segment.start[0], Y=segment.start[1], Z=segment.z,
                    F=self.config.travel_velocity
                )
            
            # Approach start at writing velocity (if using accel distance)
            if accel_dist > 0:
                program.LINEAR(
                    X=segment.start[0], Y=segment.start[1],
                    F=self.config.velocity
                )
            
            # LASER ON
            program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.ON)
            
            # Write segment
            program.LINEAR(
                X=segment.end[0], Y=segment.end[1],
                F=self.config.velocity
            )
            
            # LASER OFF
            program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.OFF)
            
            # Post-end position (for deceleration on last segment)
            if accel_dist > 0 and is_last:
                post_end_x = segment.end[0] + dir_x * accel_dist
                post_end_y = segment.end[1] + dir_y * accel_dist
                program.LINEAR(
                    X=post_end_x, Y=post_end_y,
                    F=self.config.velocity
                )
            
            prev_end = segment.end
        
        yield program
    
    def __len__(self) -> int:
        return len(self.segments)
    
    def __repr__(self) -> str:
        return f"LaserSegments({len(self.segments)} segments at Z={self.z_level})"


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def segments_from_tuples(
    segment_tuples: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]],
    velocity: float,
    acceleration: float,
    sorting: SortingStrategy = SortingStrategy.SERPENTINE
) -> LaserSegments:
    """
    Create LaserSegments from list of (start, end) tuples.
    
    Args:
        segment_tuples: List of ((x1, y1, z1), (x2, y2, z2)) tuples
        velocity: Writing velocity
        acceleration: Acceleration rate
        sorting: Sorting strategy
        
    Returns:
        LaserSegments instance
    """
    segments = [
        LaserSegment(start=s, end=e)
        for s, e in segment_tuples
    ]
    
    config = LaserSegmentsConfig(
        velocity=velocity,
        acceleration=acceleration,
        sorting_strategy=sorting
    )
    
    return LaserSegments(segments=segments, config=config)


def segments_from_2d_with_z(
    segment_tuples_2d: List[Tuple[Tuple[float, float], Tuple[float, float]]],
    z_level: float,
    velocity: float,
    acceleration: float,
    sorting: SortingStrategy = SortingStrategy.SERPENTINE
) -> LaserSegments:
    """
    Create LaserSegments from 2D segments at given Z-level.
    
    Args:
        segment_tuples_2d: List of ((x1, y1), (x2, y2)) tuples
        z_level: Z coordinate for all segments
        velocity: Writing velocity
        acceleration: Acceleration rate
        sorting: Sorting strategy
        
    Returns:
        LaserSegments instance
    """
    segments = [
        LaserSegment(
            start=(s[0], s[1], z_level),
            end=(e[0], e[1], z_level)
        )
        for s, e in segment_tuples_2d
    ]
    
    config = LaserSegmentsConfig(
        velocity=velocity,
        acceleration=acceleration,
        sorting_strategy=sorting
    )
    
    return LaserSegments(segments=segments, config=config)


# =============================================================================
# EXAMPLE / TEST
# =============================================================================

if __name__ == '__main__':
    print("LaserSegments Module Test")
    print("=" * 60)
    
    # Create some test segments (simulating hatch lines)
    test_segments = [
        LaserSegment((0, 0, 0), (10, 0, 0)),
        LaserSegment((0, 1, 0), (10, 1, 0)),
        LaserSegment((0, 2, 0), (10, 2, 0)),
        LaserSegment((0, 3, 0), (10, 3, 0)),
    ]
    
    config = LaserSegmentsConfig(
        velocity=10000,
        acceleration=100000,
        sorting_strategy=SortingStrategy.SERPENTINE
    )
    
    ls = LaserSegments(segments=test_segments, config=config)
    
    print(f"Created: {ls}")
    print(f"Center: {ls.center_point}")
    print(f"Bounds: {ls.bounds}")
    
    print("\nSorted segments (serpentine):")
    for i, seg in enumerate(ls.get_sorted_segments()):
        print(f"  {i}: {seg}")
