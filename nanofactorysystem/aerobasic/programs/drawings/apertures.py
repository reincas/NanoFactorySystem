"""
Apertures Module
================
Standalone aperture (boundary) functions for 2PP fabrication.

Can be used with ANY drawable structure:
- HeightFunctionStructures (Gratings, Lenses)
- Rectangle3D
- Stair
- Custom structures

Apertures define the region where a structure exists.
Return True inside the aperture, False outside.

Usage:
    from nanofactorysystem.aerobasic.programs.drawings.apertures import Apertures
    
    # With any structure that supports apertures
    structure = SomeStructure(
        ...,
        aperture=Apertures.circular(radius=50)
    )
    
    # Direct usage for masking
    mask = Apertures.circular(radius=50)(X, Y)

Author: Hannes Robben / Claude
Date: 2025
"""

from typing import Callable, Tuple, Optional
import numpy as np


class Apertures:
    """
    Collection of aperture (boundary) functions.
    
    All functions return a callable mask = f(X, Y) that works with numpy arrays.
    
    Available apertures:
    - circular: Circle
    - rectangular: Rectangle
    - elliptical: Ellipse (with rotation)
    - annular: Ring (donut)
    - sector: Pie slice
    - polygon: Arbitrary polygon
    - none: No boundary (everything inside)
    
    Combining apertures:
    - combine_and: Intersection of apertures
    - combine_or: Union of apertures
    - invert: Inside becomes outside
    
    Usage:
        aperture = Apertures.circular(radius=50, cx=0, cy=0)
        mask = aperture(X, Y)  # Boolean array
    """
    
    @staticmethod
    def circular(
        radius: float,
        cx: float = 0.0,
        cy: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Circular aperture.
        
        Args:
            radius: Circle radius
            cx, cy: Center position (default: origin)
            
        Returns:
            Aperture function f(X, Y) -> bool array
        """
        def f(X, Y):
            return (X - cx) ** 2 + (Y - cy) ** 2 <= radius ** 2
        
        return f
    
    @staticmethod
    def rectangular(
        width: float,
        height: float,
        cx: float = 0.0,
        cy: float = 0.0,
        angle_deg: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Rectangular aperture with optional rotation.
        
        Args:
            width: Rectangle width (X extent)
            height: Rectangle height (Y extent)
            cx, cy: Center position
            angle_deg: Rotation angle in degrees
            
        Returns:
            Aperture function f(X, Y) -> bool array
        """
        if angle_deg == 0.0:
            def f(X, Y):
                return (np.abs(X - cx) <= width / 2) & (np.abs(Y - cy) <= height / 2)
        else:
            theta = np.deg2rad(angle_deg)
            cos_t, sin_t = np.cos(theta), np.sin(theta)
            
            def f(X, Y):
                dx = X - cx
                dy = Y - cy
                x_rot = dx * cos_t + dy * sin_t
                y_rot = -dx * sin_t + dy * cos_t
                return (np.abs(x_rot) <= width / 2) & (np.abs(y_rot) <= height / 2)
        
        return f
    
    @staticmethod
    def elliptical(
        a: float,
        b: float,
        cx: float = 0.0,
        cy: float = 0.0,
        angle_deg: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Elliptical aperture.
        
        Args:
            a: Semi-major axis
            b: Semi-minor axis
            cx, cy: Center position
            angle_deg: Rotation angle in degrees
            
        Returns:
            Aperture function f(X, Y) -> bool array
        """
        theta = np.deg2rad(angle_deg)
        cos_t, sin_t = np.cos(theta), np.sin(theta)
        
        def f(X, Y):
            dx = X - cx
            dy = Y - cy
            x_rot = dx * cos_t + dy * sin_t
            y_rot = -dx * sin_t + dy * cos_t
            return (x_rot / a) ** 2 + (y_rot / b) ** 2 <= 1
        
        return f
    
    @staticmethod
    def annular(
        inner_radius: float,
        outer_radius: float,
        cx: float = 0.0,
        cy: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Annular (ring/donut) aperture.
        
        Args:
            inner_radius: Inner circle radius (hole)
            outer_radius: Outer circle radius
            cx, cy: Center position
            
        Returns:
            Aperture function f(X, Y) -> bool array
        """
        def f(X, Y):
            r2 = (X - cx) ** 2 + (Y - cy) ** 2
            return (r2 >= inner_radius ** 2) & (r2 <= outer_radius ** 2)
        
        return f
    
    @staticmethod
    def sector(
        radius: float,
        start_angle_deg: float,
        end_angle_deg: float,
        cx: float = 0.0,
        cy: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Circular sector (pie slice) aperture.
        
        Args:
            radius: Sector radius
            start_angle_deg: Start angle in degrees
            end_angle_deg: End angle in degrees
            cx, cy: Center position
            
        Returns:
            Aperture function f(X, Y) -> bool array
        """
        start_rad = np.deg2rad(start_angle_deg)
        end_rad = np.deg2rad(end_angle_deg)
        
        def f(X, Y):
            r2 = (X - cx) ** 2 + (Y - cy) ** 2
            angle = np.arctan2(Y - cy, X - cx)
            
            # Handle angle wrapping
            if start_rad <= end_rad:
                angle_ok = (angle >= start_rad) & (angle <= end_rad)
            else:
                angle_ok = (angle >= start_rad) | (angle <= end_rad)
            
            return (r2 <= radius ** 2) & angle_ok
        
        return f
    
    @staticmethod
    def polygon(
        vertices: np.ndarray,
        cx: float = 0.0,
        cy: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Arbitrary polygon aperture using ray casting.
        
        Args:
            vertices: Nx2 array of polygon vertices
            cx, cy: Offset to apply to vertices
            
        Returns:
            Aperture function f(X, Y) -> bool array
        """
        from matplotlib.path import Path
        
        verts = np.array(vertices) + np.array([cx, cy])
        path = Path(verts)
        
        def f(X, Y):
            points = np.column_stack([X.ravel(), Y.ravel()])
            return path.contains_points(points).reshape(X.shape)
        
        return f
    
    @staticmethod
    def regular_polygon(
        n_sides: int,
        radius: float,
        cx: float = 0.0,
        cy: float = 0.0,
        rotation_deg: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Regular polygon aperture (triangle, square, pentagon, hexagon, ...).
        
        Args:
            n_sides: Number of sides (3=triangle, 4=square, 6=hexagon, ...)
            radius: Distance from center to vertices
            cx, cy: Center position
            rotation_deg: Rotation angle in degrees
            
        Returns:
            Aperture function f(X, Y) -> bool array
        """
        angles = np.linspace(0, 2*np.pi, n_sides, endpoint=False)
        angles += np.deg2rad(rotation_deg)
        
        vertices = np.column_stack([
            radius * np.cos(angles),
            radius * np.sin(angles)
        ])
        
        return Apertures.polygon(vertices, cx, cy)
    
    @staticmethod
    def none() -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        No aperture (everything is inside).
        
        Returns:
            Aperture function that always returns True
        """
        def f(X, Y):
            return np.ones_like(X, dtype=bool)
        
        return f
    
    # =========================================================================
    # COMBINING APERTURES
    # =========================================================================
    
    @staticmethod
    def combine_and(
        *apertures: Callable
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Combine apertures with AND (intersection).
        
        Result is inside only where ALL apertures are inside.
        
        Args:
            *apertures: Aperture functions to combine
            
        Returns:
            Combined aperture function
            
        Example:
            # Circle with rectangular cutout
            ap = Apertures.combine_and(
                Apertures.circular(radius=50),
                Apertures.invert(Apertures.rectangular(20, 20))
            )
        """
        def f(X, Y):
            result = apertures[0](X, Y)
            for ap in apertures[1:]:
                result = result & ap(X, Y)
            return result
        
        return f
    
    @staticmethod
    def combine_or(
        *apertures: Callable
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Combine apertures with OR (union).
        
        Result is inside where ANY aperture is inside.
        
        Args:
            *apertures: Aperture functions to combine
            
        Returns:
            Combined aperture function
            
        Example:
            # Two circles
            ap = Apertures.combine_or(
                Apertures.circular(radius=30, cx=-20),
                Apertures.circular(radius=30, cx=20)
            )
        """
        def f(X, Y):
            result = apertures[0](X, Y)
            for ap in apertures[1:]:
                result = result | ap(X, Y)
            return result
        
        return f
    
    @staticmethod
    def invert(
        aperture: Callable
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Invert an aperture (inside becomes outside).
        
        Args:
            aperture: Aperture function to invert
            
        Returns:
            Inverted aperture function
        """
        def f(X, Y):
            return ~aperture(X, Y)
        
        return f
    
    @staticmethod
    def subtract(
        aperture1: Callable,
        aperture2: Callable
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Subtract aperture2 from aperture1.
        
        Equivalent to: combine_and(aperture1, invert(aperture2))
        
        Args:
            aperture1: Base aperture
            aperture2: Aperture to subtract
            
        Returns:
            Difference aperture function
            
        Example:
            # Circle with hole
            ap = Apertures.subtract(
                Apertures.circular(radius=50),
                Apertures.circular(radius=20)
            )
        """
        def f(X, Y):
            return aperture1(X, Y) & ~aperture2(X, Y)
        
        return f


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def apply_aperture(
    data: np.ndarray,
    aperture: Callable,
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    fill_value: float = np.nan
) -> np.ndarray:
    """
    Apply an aperture to a 2D data array.
    
    Args:
        data: 2D numpy array
        aperture: Aperture function
        x_range: (x_min, x_max) coordinate range
        y_range: (y_min, y_max) coordinate range
        fill_value: Value to use outside aperture (default: NaN)
        
    Returns:
        Masked data array
    """
    ny, nx = data.shape
    xs = np.linspace(x_range[0], x_range[1], nx)
    ys = np.linspace(y_range[0], y_range[1], ny)
    X, Y = np.meshgrid(xs, ys)
    
    mask = aperture(X, Y)
    result = data.copy()
    result[~mask] = fill_value
    
    return result


# =============================================================================
# EXAMPLE / TEST
# =============================================================================

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    
    print("Apertures Module Test")
    print("=" * 60)
    
    # Create test grid
    x = np.linspace(-10, 10, 200)
    y = np.linspace(-10, 10, 200)
    X, Y = np.meshgrid(x, y)
    
    # Test apertures
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    
    apertures = [
        ("Circular", Apertures.circular(radius=5)),
        ("Rectangular", Apertures.rectangular(width=12, height=8)),
        ("Elliptical (30°)", Apertures.elliptical(a=7, b=4, angle_deg=30)),
        ("Annular", Apertures.annular(inner_radius=3, outer_radius=7)),
        ("Sector", Apertures.sector(radius=7, start_angle_deg=-45, end_angle_deg=45)),
        ("Hexagon", Apertures.regular_polygon(n_sides=6, radius=6)),
        ("Circle - Rect", Apertures.subtract(
            Apertures.circular(radius=8),
            Apertures.rectangular(width=6, height=6)
        )),
        ("Two Circles", Apertures.combine_or(
            Apertures.circular(radius=4, cx=-3),
            Apertures.circular(radius=4, cx=3)
        )),
    ]
    
    for ax, (name, ap) in zip(axes.flat, apertures):
        mask = ap(X, Y)
        ax.imshow(mask, extent=[-10, 10, -10, 10], origin='lower', cmap='gray')
        ax.set_title(name)
        ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig('apertures_standalone_test.png', dpi=150)
    print("Saved: apertures_standalone_test.png")
