"""
HatchGenerator Module
=====================
Standalone module for generating hatch patterns in 2PP fabrication.

Can be used with ANY structure that needs hatching:
- HeightFunctionStructures (Gratings, Lenses)
- Rectangle3D with aperture
- Arbitrary polygon fills
- Future STL-based structures

Features:
- Serpentine (zig-zag) hatch patterns
- Arbitrary hatch angles
- Polygon clipping
- Optimized hatch_size for even line count

Usage:
    from nanofactorysystem.aerobasic.programs.drawings.hatch_generator import (
        HatchGenerator, HatchConfig
    )
    
    gen = HatchGenerator(HatchConfig(hatch_size=0.3, hatch_angle_deg=45))
    segments = gen.hatch_rectangle(-50, 50, -50, 50, z_level=0)

Author: Hannes Robben / Claude
Date: 2025
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable
import numpy as np

# Import LaserSegment from the standalone module
from .laser_segments import LaserSegment


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass 
class HatchConfig:
    """Configuration for hatch pattern generation"""
    hatch_size: float               # Distance between hatch lines
    hatch_angle_deg: float = 0.0    # Angle of hatch lines (0 = along X)
    
    # Optimization
    optimize_line_count: bool = True  # Adjust hatch_size for even line count
    min_segment_length: float = 1e-6  # Minimum segment length to include
    
    # Clipping bounds (optional)
    clip_bounds: Optional[Tuple[float, float, float, float]] = None  # (x_min, x_max, y_min, y_max)


# =============================================================================
# CORE HATCH ALGORITHMS
# =============================================================================

def _intersect_line_with_segment(
    p0: np.ndarray, 
    d: np.ndarray,
    a: np.ndarray, 
    b: np.ndarray
) -> Optional[float]:
    """
    Compute intersection of ray p0 + t*d with line segment a→b.
    
    Args:
        p0: Ray origin
        d: Ray direction
        a: Segment start
        b: Segment end
        
    Returns:
        Parameter t if intersection exists, None otherwise
    """
    v = b - a
    det = d[0] * (-v[1]) - d[1] * (-v[0])
    
    if abs(det) < 1e-12:
        return None
    
    rhs = a - p0
    t = (rhs[0] * (-v[1]) - rhs[1] * (-v[0])) / det
    s = (d[0] * rhs[1] - d[1] * rhs[0]) / det
    
    if 0 <= s <= 1:
        return t
    return None


def _hatch_polygon_2d(
    polygon: np.ndarray,
    hatch_angle_deg: float,
    hatch_distance: float,
    min_segment_length: float = 1e-6
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Generate hatch lines for a closed 2D polygon.
    
    Args:
        polygon: Nx2 array of polygon vertices (closed)
        hatch_angle_deg: Angle of hatch lines in degrees
        hatch_distance: Distance between hatch lines
        min_segment_length: Minimum segment length to include
        
    Returns:
        List of ((x1, y1), (x2, y2)) segment tuples
    """
    if len(polygon) < 3:
        return []
    
    # Hatch direction and normal
    theta = np.deg2rad(hatch_angle_deg)
    d = np.array([np.cos(theta), np.sin(theta)])  # Direction along hatch
    n = np.array([-d[1], d[0]])  # Normal to hatch (perpendicular)
    
    # Project all polygon points onto normal to find extent
    projections = polygon @ n
    proj_min = projections.min()
    proj_max = projections.max()
    
    # Generate hatch line offsets
    offsets = np.arange(proj_min, proj_max + hatch_distance, hatch_distance)
    
    # Build polygon edges
    n_vertices = len(polygon)
    edges = [(polygon[i], polygon[(i + 1) % n_vertices]) for i in range(n_vertices)]
    
    segments = []
    
    for offset in offsets:
        # Line at this offset: p0 + t * d, where p0 is on the offset line
        p0 = n * offset
        
        # Find all intersections with polygon edges
        intersections = []
        for a, b in edges:
            t = _intersect_line_with_segment(p0, d, a, b)
            if t is not None:
                intersections.append(t)
        
        if len(intersections) < 2:
            continue
        
        # Sort intersections
        intersections.sort()
        
        # Remove duplicates (can happen at vertices)
        filtered = [intersections[0]]
        for t in intersections[1:]:
            if abs(t - filtered[-1]) > 1e-9:
                filtered.append(t)
        intersections = filtered
        
        # Create segments from pairs of intersections (inside polygon)
        for i in range(0, len(intersections) - 1, 2):
            t0, t1 = intersections[i], intersections[i + 1]
            p_start = p0 + t0 * d
            p_end = p0 + t1 * d
            
            # Check minimum length
            if np.linalg.norm(p_end - p_start) > min_segment_length:
                segments.append((
                    (float(p_start[0]), float(p_start[1])),
                    (float(p_end[0]), float(p_end[1]))
                ))
    
    return segments


def _hatch_rectangle(
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    hatch_angle_deg: float,
    hatch_distance: float,
    optimize: bool = True
) -> Tuple[List[Tuple[Tuple[float, float], Tuple[float, float]]], float]:
    """
    Generate hatch lines for a rectangle with optional line count optimization.
    
    Args:
        x_min, x_max, y_min, y_max: Rectangle bounds
        hatch_angle_deg: Hatch angle in degrees
        hatch_distance: Desired hatch distance
        optimize: If True, adjust distance for even line count
        
    Returns:
        Tuple of (segments, actual_hatch_distance)
    """
    # Create rectangle polygon (closed)
    polygon = np.array([
        [x_min, y_min],
        [x_max, y_min],
        [x_max, y_max],
        [x_min, y_max],
        [x_min, y_min]  # Close
    ])
    
    # Calculate extent in normal direction
    theta = np.deg2rad(hatch_angle_deg)
    n = np.array([-np.sin(theta), np.cos(theta)])
    
    projections = polygon[:-1] @ n  # Don't include closing point twice
    extent = projections.max() - projections.min()
    
    # Optimize hatch distance for even line count
    if optimize and extent > hatch_distance:
        n_lines = max(2, round(extent / hatch_distance))
        # Ensure even number of lines for better serpentine
        if n_lines % 2 == 1:
            n_lines += 1
        actual_distance = extent / (n_lines - 1) if n_lines > 1 else hatch_distance
    else:
        actual_distance = hatch_distance
    
    segments = _hatch_polygon_2d(polygon, hatch_angle_deg, actual_distance)
    
    return segments, actual_distance


# =============================================================================
# HATCH GENERATOR CLASS
# =============================================================================

class HatchGenerator:
    """
    Generates optimized hatch patterns for various geometries.
    
    Designed to be extensible for:
    - Rectangles (current)
    - Arbitrary polygons (current)
    - Binary masks (current)
    - STL files (future)
    - Contour-based inputs (future)
    
    Usage:
        gen = HatchGenerator(HatchConfig(hatch_size=0.2, hatch_angle_deg=45))
        
        # For rectangle
        segments = gen.hatch_rectangle(-50, 50, -50, 50, z_level=0)
        
        # For polygon
        polygon = np.array([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]])
        segments = gen.hatch_polygon(polygon, z_level=0)
    """
    
    def __init__(self, config: HatchConfig):
        self.config = config
        self._actual_hatch_size: Optional[float] = None
    
    @property
    def actual_hatch_size(self) -> float:
        """Return the actual hatch size used (may differ from config if optimized)"""
        return self._actual_hatch_size or self.config.hatch_size
    
    def hatch_rectangle(
        self,
        x_min: float, x_max: float,
        y_min: float, y_max: float,
        z_level: float
    ) -> List[LaserSegment]:
        """
        Generate hatch pattern for a rectangle.
        
        Args:
            x_min, x_max, y_min, y_max: Rectangle bounds
            z_level: Z coordinate for all segments
            
        Returns:
            List of LaserSegment objects
        """
        segments_2d, actual_dist = _hatch_rectangle(
            x_min, x_max, y_min, y_max,
            self.config.hatch_angle_deg,
            self.config.hatch_size,
            self.config.optimize_line_count
        )
        
        self._actual_hatch_size = actual_dist
        
        # Convert to LaserSegments with Z
        return [
            LaserSegment(
                start=(s[0], s[1], z_level),
                end=(e[0], e[1], z_level)
            )
            for s, e in segments_2d
        ]
    
    def hatch_polygon(
        self,
        polygon: np.ndarray,
        z_level: float
    ) -> List[LaserSegment]:
        """
        Generate hatch pattern for a closed polygon.
        
        Args:
            polygon: Nx2 array of vertices (should be closed or will be auto-closed)
            z_level: Z coordinate for all segments
            
        Returns:
            List of LaserSegment objects
        """
        # Ensure polygon is closed
        poly = np.array(polygon)
        if len(poly) > 2 and not np.allclose(poly[0], poly[-1]):
            poly = np.vstack([poly, poly[0]])
        
        segments_2d = _hatch_polygon_2d(
            poly,
            self.config.hatch_angle_deg,
            self.config.hatch_size,
            self.config.min_segment_length
        )
        
        # Apply clipping if configured
        if self.config.clip_bounds is not None:
            segments_2d = self._clip_segments(segments_2d, self.config.clip_bounds)
        
        # Convert to LaserSegments with Z
        return [
            LaserSegment(
                start=(s[0], s[1], z_level),
                end=(e[0], e[1], z_level)
            )
            for s, e in segments_2d
        ]
    
    def hatch_polygons(
        self,
        polygons: List[np.ndarray],
        z_level: float
    ) -> List[LaserSegment]:
        """
        Generate hatch pattern for multiple polygons.
        
        Args:
            polygons: List of Nx2 polygon arrays
            z_level: Z coordinate for all segments
            
        Returns:
            Combined list of LaserSegment objects
        """
        all_segments = []
        for poly in polygons:
            all_segments.extend(self.hatch_polygon(poly, z_level))
        return all_segments
    
    def _clip_segments(
        self,
        segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        bounds: Tuple[float, float, float, float]
    ) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Clip segments to rectangular bounds using Cohen-Sutherland algorithm.
        
        Args:
            segments: List of 2D segment tuples
            bounds: (x_min, x_max, y_min, y_max)
            
        Returns:
            Clipped segments
        """
        x_min, x_max, y_min, y_max = bounds
        clipped = []
        
        for (x1, y1), (x2, y2) in segments:
            # Cohen-Sutherland outcodes
            def outcode(x, y):
                code = 0
                if x < x_min: code |= 1
                if x > x_max: code |= 2
                if y < y_min: code |= 4
                if y > y_max: code |= 8
                return code
            
            code1 = outcode(x1, y1)
            code2 = outcode(x2, y2)
            accept = False
            
            while True:
                if not (code1 | code2):
                    # Both inside
                    accept = True
                    break
                elif code1 & code2:
                    # Both outside same region
                    break
                else:
                    # Calculate intersection
                    code_out = code1 if code1 else code2
                    
                    if code_out & 8:  # Above
                        x = x1 + (x2 - x1) * (y_max - y1) / (y2 - y1)
                        y = y_max
                    elif code_out & 4:  # Below
                        x = x1 + (x2 - x1) * (y_min - y1) / (y2 - y1)
                        y = y_min
                    elif code_out & 2:  # Right
                        y = y1 + (y2 - y1) * (x_max - x1) / (x2 - x1)
                        x = x_max
                    elif code_out & 1:  # Left
                        y = y1 + (y2 - y1) * (x_min - x1) / (x2 - x1)
                        x = x_min
                    
                    if code_out == code1:
                        x1, y1 = x, y
                        code1 = outcode(x1, y1)
                    else:
                        x2, y2 = x, y
                        code2 = outcode(x2, y2)
            
            if accept:
                clipped.append(((x1, y1), (x2, y2)))
        
        return clipped
    
    def hatch_from_mask(
        self,
        mask: np.ndarray,
        x_range: Tuple[float, float],
        y_range: Tuple[float, float],
        z_level: float,
        min_area: int = 10
    ) -> List[LaserSegment]:
        """
        Generate hatch pattern from a binary mask.
        
        This is the entry point for height-function based slicing
        and aperture-masked structures.
        
        Args:
            mask: 2D boolean array (True = inside region)
            x_range: (x_min, x_max) for coordinate mapping
            y_range: (y_min, y_max) for coordinate mapping  
            z_level: Z coordinate for all segments
            min_area: Minimum region area in pixels to process
            
        Returns:
            List of LaserSegment objects
        """
        from skimage.measure import label, regionprops, find_contours
        
        # Find connected regions
        labels = label(mask.astype(np.uint8))
        regions = regionprops(labels)
        
        # Create coordinate arrays
        xs = np.linspace(x_range[0], x_range[1], mask.shape[1])
        ys = np.linspace(y_range[0], y_range[1], mask.shape[0])
        
        all_segments = []
        
        for region in regions:
            if region.area < min_area:
                continue
            
            # Create mask for just this region
            region_mask = (labels == region.label).astype(float)
            
            # Find contours
            contours = find_contours(region_mask, 0.5)
            
            for contour in contours:
                # Convert pixel coordinates to real coordinates
                poly = []
                for yi, xi in contour:
                    x_coord = x_range[0] + (x_range[1] - x_range[0]) * xi / (len(xs) - 1)
                    y_coord = y_range[0] + (y_range[1] - y_range[0]) * yi / (len(ys) - 1)
                    poly.append([x_coord, y_coord])
                
                poly = np.array(poly)
                
                # Close if needed
                if len(poly) > 2 and not np.allclose(poly[0], poly[-1]):
                    poly = np.vstack([poly, poly[0]])
                
                if len(poly) >= 4:
                    seg = self.hatch_polygon(poly, z_level)
                    all_segments.extend(seg)
        
        return all_segments
    
    def hatch_with_aperture(
        self,
        x_min: float, x_max: float,
        y_min: float, y_max: float,
        z_level: float,
        aperture: Callable[[np.ndarray, np.ndarray], np.ndarray],
        resolution: int = 500
    ) -> List[LaserSegment]:
        """
        Generate hatch pattern for a rectangle with an aperture applied.
        
        This is useful for Rectangle3D, Stair, etc. with apertures.
        
        Args:
            x_min, x_max, y_min, y_max: Rectangle bounds
            z_level: Z coordinate
            aperture: Aperture function from Apertures class
            resolution: Grid resolution for mask generation
            
        Returns:
            List of LaserSegment objects
        """
        # Create evaluation grid
        xs = np.linspace(x_min, x_max, resolution)
        ys = np.linspace(y_min, y_max, resolution)
        X, Y = np.meshgrid(xs, ys)
        
        # Apply aperture
        mask = aperture(X, Y)
        
        # Generate hatch from mask
        return self.hatch_from_mask(
            mask=mask,
            x_range=(x_min, x_max),
            y_range=(y_min, y_max),
            z_level=z_level
        )


# =============================================================================
# CONVENIENCE FUNCTIONS  
# =============================================================================

def create_serpentine_hatch(
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    z_level: float,
    hatch_size: float,
    hatch_angle_deg: float = 0.0
) -> List[LaserSegment]:
    """
    Quick function to create serpentine hatch for a rectangle.
    
    Returns segments already sorted in serpentine order.
    """
    config = HatchConfig(
        hatch_size=hatch_size,
        hatch_angle_deg=hatch_angle_deg,
        optimize_line_count=True
    )
    
    gen = HatchGenerator(config)
    return gen.hatch_rectangle(x_min, x_max, y_min, y_max, z_level)


# =============================================================================
# EXAMPLE / TEST
# =============================================================================

if __name__ == '__main__':
    print("HatchGenerator Module Test")
    print("=" * 60)
    
    # Test rectangle hatching
    config = HatchConfig(
        hatch_size=1.0,
        hatch_angle_deg=0.0,
        optimize_line_count=True
    )
    
    gen = HatchGenerator(config)
    
    segments = gen.hatch_rectangle(-5, 5, -5, 5, z_level=0)
    
    print(f"Rectangle hatch: {len(segments)} segments")
    print(f"Actual hatch size: {gen.actual_hatch_size}")
    
    for i, seg in enumerate(segments[:5]):
        print(f"  {i}: {seg}")
    
    print("\nPolygon hatch (circle approximation):")
    
    # Create circular polygon
    angles = np.linspace(0, 2*np.pi, 32)
    circle = np.column_stack([np.cos(angles) * 5, np.sin(angles) * 5])
    
    config45 = HatchConfig(hatch_size=0.5, hatch_angle_deg=45.0)
    gen45 = HatchGenerator(config45)
    
    circle_segments = gen45.hatch_polygon(circle, z_level=0)
    print(f"Circle hatch (45°): {len(circle_segments)} segments")
