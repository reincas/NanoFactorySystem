"""
Height Functions Module
=======================
Standalone module containing mathematical height functions for DOE structures.

These are pure mathematical functions z = f(x, y) that can be used with:
- HeightFunctionStructure classes (Gratings, Lenses)
- Custom structures
- Visualization
- Analysis

For aperture/boundary functions, see: apertures.py

Usage:
    from nanofactorysystem.aerobasic.programs.drawings.height_functions import HeightFunctions
    
    height_func = HeightFunctions.sinusoidal(period=10, height=2)
    Z = height_func(X, Y)  # Works with numpy meshgrid

Author: Hannes Robben
Date: 2025
"""

from typing import Callable, Tuple, Optional
import numpy as np


class HeightFunctions:
    """
    Collection of standard height functions for gratings and DOEs.
    
    All functions return a callable z = f(X, Y) that works with numpy arrays.
    
    Coordinate convention:
    - Functions are defined relative to structure center (0, 0)
    - Grating_63 angle rotates the grating pattern
    - Z values are typically in range [z0, z0 + height]
    
    Available functions:
    - sinusoidal: Sine wave grating
    - binary_grating: Step/square grating
    - blazed_grating: Sawtooth grating
    - triangular_grating: Triangle wave
    - crossed_gratings: 2D crossed pattern
    - fresnel_lens: Radial Fresnel phase
    - vortex: Spiral phase plate
    - constant: Flat surface
    - from_array: Interpolated from 2D array (for STL, etc.)
    
    Combining functions:
    - combine_add: Sum of functions
    - combine_max: Maximum of functions
    - combine_multiply: Product of functions
    
    Usage:
        height_func = HeightFunctions.sinusoidal(
            period=2.0,
            height=1.0,
            angle_deg=30.0,
            z0=0.0
        )
        
        Z = height_func(X, Y)  # Works with meshgrid arrays
    """
    
    @staticmethod
    def sinusoidal(
        period: float,
        height: float,
        angle_deg: float = 0.0,
        z0: float = 0.0,
        phase_deg: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Sinusoidal grating.
        
        z(s) = z0 + (height/2) * (1 + sin(2π * s/period + phase))
        where s = x*cos(θ) + y*sin(θ)
        
        Args:
            period: Grating_63 period (same units as X, Y)
            height: Peak-to-peak height
            angle_deg: Grating_63 rotation angle in degrees
            z0: Minimum Z value (base)
            phase_deg: Phase offset in degrees [0, 360)
            
        Returns:
            Height function f(X, Y) -> Z
        """
        theta = np.deg2rad(angle_deg)
        phase_rad = np.deg2rad(phase_deg)
        
        def f(X, Y):
            s = X * np.cos(theta) + Y * np.sin(theta)
            return z0 + (height / 2) * (1 + np.sin(2 * np.pi * s / period + phase_rad))
        
        return f
    
    @staticmethod
    def binary_grating(
        period: float,
        height: float,
        duty_cycle: float = 0.5,
        angle_deg: float = 0.0,
        z0: float = 0.0,
        phase_deg: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Binary (step) grating.
        
        z(s) = z0 + height  if (s mod period) / period < duty_cycle
        z(s) = z0           otherwise
        
        Args:
            period: Grating_63 period
            height: Step height
            duty_cycle: Fraction of period that is "high" (0 to 1)
            angle_deg: Grating_63 rotation angle
            z0: Base Z value
            phase_deg: Phase offset in degrees
            
        Returns:
            Height function f(X, Y) -> Z
        """
        theta = np.deg2rad(angle_deg)
        phase_frac = phase_deg / 360.0
        
        def f(X, Y):
            s = X * np.cos(theta) + Y * np.sin(theta)
            frac = np.mod(s / period + phase_frac, 1.0)
            return z0 + height * (frac < duty_cycle).astype(float)
        
        return f
    
    @staticmethod
    def blazed_grating(
        period: float,
        height: float,
        angle_deg: float = 0.0,
        z0: float = 0.0,
        phase_deg: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Blazed (sawtooth) grating.
        
        z(s) = z0 + height * (s mod period) / period
        
        Args:
            period: Grating_63 period
            height: Maximum height (ramp amplitude)
            angle_deg: Grating_63 rotation angle
            z0: Base Z value
            phase_deg: Phase offset in degrees
            
        Returns:
            Height function f(X, Y) -> Z
        """
        theta = np.deg2rad(angle_deg)
        phase_frac = phase_deg / 360.0
        
        def f(X, Y):
            s = X * np.cos(theta) + Y * np.sin(theta)
            return z0 + height * np.mod(s / period + phase_frac, 1.0)
        
        return f
    
    @staticmethod
    def triangular_grating(
        period: float,
        height: float,
        angle_deg: float = 0.0,
        z0: float = 0.0,
        phase_deg: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Symmetric triangular grating.
        
        z(s) = z0 + height * (1 - 2 * |frac - 0.5|)
        where frac = (s mod period) / period
        
        Args:
            period: Grating_63 period
            height: Peak height
            angle_deg: Grating_63 rotation angle
            z0: Base Z value
            phase_deg: Phase offset in degrees
            
        Returns:
            Height function f(X, Y) -> Z
        """
        theta = np.deg2rad(angle_deg)
        phase_frac = phase_deg / 360.0
        
        def f(X, Y):
            s = X * np.cos(theta) + Y * np.sin(theta)
            frac = np.mod(s / period + phase_frac, 1.0)
            return z0 + height * (1 - 2 * np.abs(frac - 0.5))
        
        return f
    
    @staticmethod
    def crossed_gratings(
        period1: float,
        period2: float,
        height: float,
        angle1_deg: float = 0.0,
        angle2_deg: float = 90.0,
        z0: float = 0.0,
        phase1_deg: float = 0.0,
        phase2_deg: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Crossed (2D) grating - superposition of two sinusoidal gratings.
        
        z = z0 + (height/2) * (sin(s1) + sin(s2)) / 2
        
        Args:
            period1, period2: Periods of the two gratings
            height: Total height variation
            angle1_deg, angle2_deg: Rotation angles
            z0: Base Z value
            phase1_deg, phase2_deg: Phase offsets
            
        Returns:
            Height function f(X, Y) -> Z
        """
        theta1 = np.deg2rad(angle1_deg)
        theta2 = np.deg2rad(angle2_deg)
        phase1 = np.deg2rad(phase1_deg)
        phase2 = np.deg2rad(phase2_deg)
        
        def f(X, Y):
            s1 = X * np.cos(theta1) + Y * np.sin(theta1)
            s2 = X * np.cos(theta2) + Y * np.sin(theta2)
            z1 = np.sin(2 * np.pi * s1 / period1 + phase1)
            z2 = np.sin(2 * np.pi * s2 / period2 + phase2)
            return z0 + height * (1 + (z1 + z2) / 2) / 2
        
        return f
    
    @staticmethod
    def fresnel_lens(
        focal_length: float,
        wavelength: float,
        height: float,
        cx: float = 0.0,
        cy: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Fresnel lens (radial phase profile).
        
        phase(r) = π * r² / (λ * f)
        z = height * (phase mod 2π) / 2π
        
        Args:
            focal_length: Focal length
            wavelength: Design wavelength
            height: Maximum height (one phase wrap)
            cx, cy: Center position
            
        Returns:
            Height function f(X, Y) -> Z
        """
        def f(X, Y):
            r2 = (X - cx) ** 2 + (Y - cy) ** 2
            phase = np.pi * r2 / (wavelength * focal_length)
            return height * np.mod(phase, 2 * np.pi) / (2 * np.pi)
        
        return f
    
    @staticmethod
    def vortex(
        charge: int,
        height: float,
        cx: float = 0.0,
        cy: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Optical vortex (spiral phase plate).
        
        z = height * (charge * atan2(y, x) mod 2π) / 2π
        
        Args:
            charge: Topological charge (integer)
            height: Maximum height (one phase wrap)
            cx, cy: Center position
            
        Returns:
            Height function f(X, Y) -> Z
        """
        def f(X, Y):
            phi = np.arctan2(Y - cy, X - cx)  # Range: [-π, π]
            phase = charge * phi
            # Normalize to [0, 2π] then to [0, height]
            return height * np.mod(phase, 2 * np.pi) / (2 * np.pi)
        
        return f
    
    @staticmethod
    def axicon(
        cone_angle_deg: float,
        height: float,
        cx: float = 0.0,
        cy: float = 0.0
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Axicon (conical lens).
        
        z = height * (1 - r / r_max) for r < r_max
        
        Args:
            cone_angle_deg: Cone half-angle in degrees
            height: Maximum height at center
            cx, cy: Center position
            
        Returns:
            Height function f(X, Y) -> Z
        """
        def f(X, Y):
            r = np.sqrt((X - cx)**2 + (Y - cy)**2)
            # Linear decrease from center
            slope = np.tan(np.deg2rad(cone_angle_deg))
            return np.maximum(0, height - r * slope)
        
        return f
    
    @staticmethod
    def constant(height: float) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Constant height (flat surface).
        
        Args:
            height: Z value everywhere
            
        Returns:
            Height function f(X, Y) -> Z
        """
        def f(X, Y):
            return np.full_like(X, height, dtype=float)
        
        return f
    
    @staticmethod
    def from_array(
        z_array: np.ndarray,
        x_range: Tuple[float, float],
        y_range: Tuple[float, float],
        method: str = 'linear'
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Height function from 2D array with interpolation.
        
        Useful for:
        - STL file imports
        - Measured surface data
        - Computed profiles
        
        Args:
            z_array: 2D array of Z values
            x_range: (x_min, x_max) coordinate range
            y_range: (y_min, y_max) coordinate range
            method: Interpolation method ('linear' or 'nearest')
            
        Returns:
            Height function f(X, Y) -> Z
        """
        from scipy import interpolate
        
        ny, nx = z_array.shape
        xs = np.linspace(x_range[0], x_range[1], nx)
        ys = np.linspace(y_range[0], y_range[1], ny)
        
        if method == 'linear':
            interp = interpolate.RegularGridInterpolator(
                (ys, xs), z_array, method='linear', bounds_error=False, fill_value=np.nan
            )
        else:
            interp = interpolate.RegularGridInterpolator(
                (ys, xs), z_array, method='nearest', bounds_error=False, fill_value=np.nan
            )
        
        def f(X, Y):
            points = np.column_stack([Y.ravel(), X.ravel()])
            return interp(points).reshape(X.shape)
        
        return f
    
    # =========================================================================
    # COMBINING FUNCTIONS
    # =========================================================================
    
    @staticmethod
    def combine_add(
        *funcs: Callable
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Combine multiple height functions by addition.
        
        Args:
            *funcs: Height functions to add
            
        Returns:
            Combined height function
        """
        def f(X, Y):
            result = np.zeros_like(X, dtype=float)
            for func in funcs:
                result += func(X, Y)
            return result
        
        return f
    
    @staticmethod
    def combine_max(
        *funcs: Callable
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Combine multiple height functions by taking maximum.
        
        Args:
            *funcs: Height functions to combine
            
        Returns:
            Combined height function
        """
        def f(X, Y):
            result = funcs[0](X, Y)
            for func in funcs[1:]:
                result = np.maximum(result, func(X, Y))
            return result
        
        return f
    
    @staticmethod
    def combine_min(
        *funcs: Callable
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Combine multiple height functions by taking minimum.
        
        Args:
            *funcs: Height functions to combine
            
        Returns:
            Combined height function
        """
        def f(X, Y):
            result = funcs[0](X, Y)
            for func in funcs[1:]:
                result = np.minimum(result, func(X, Y))
            return result
        
        return f
    
    @staticmethod
    def combine_multiply(
        *funcs: Callable
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Combine multiple height functions by multiplication.
        
        Args:
            *funcs: Height functions to multiply
            
        Returns:
            Combined height function
        """
        def f(X, Y):
            result = funcs[0](X, Y)
            for func in funcs[1:]:
                result *= func(X, Y)
            return result
        
        return f
    
    @staticmethod
    def offset(
        func: Callable,
        z_offset: float
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Add constant offset to height function.
        
        Args:
            func: Base height function
            z_offset: Offset to add
            
        Returns:
            Offset height function
        """
        def f(X, Y):
            return func(X, Y) + z_offset
        
        return f
    
    @staticmethod
    def scale(
        func: Callable,
        z_scale: float
    ) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """
        Scale height function.
        
        Args:
            func: Base height function
            z_scale: Scale factor
            
        Returns:
            Scaled height function
        """
        def f(X, Y):
            return func(X, Y) * z_scale
        
        return f


# =============================================================================
# EXAMPLE / TEST
# =============================================================================

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    
    print("Height Functions Module Test")
    print("=" * 60)
    
    # Create test grid
    x = np.linspace(-10, 10, 200)
    y = np.linspace(-10, 10, 200)
    X, Y = np.meshgrid(x, y)
    
    # Test height functions
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    
    funcs = [
        ("Sinusoidal", HeightFunctions.sinusoidal(period=3, height=1)),
        ("Binary", HeightFunctions.binary_grating(period=3, height=1, duty_cycle=0.4)),
        ("Blazed", HeightFunctions.blazed_grating(period=3, height=1)),
        ("Triangular", HeightFunctions.triangular_grating(period=3, height=1)),
        ("Crossed", HeightFunctions.crossed_gratings(period1=3, period2=3, height=1)),
        ("Fresnel", HeightFunctions.fresnel_lens(focal_length=100, wavelength=0.5, height=1)),
        ("Vortex", HeightFunctions.vortex(charge=2, height=1)),
        ("Axicon", HeightFunctions.axicon(cone_angle_deg=5, height=2)),
    ]
    
    for ax, (name, func) in zip(axes.flat, funcs):
        Z = func(X, Y)
        im = ax.imshow(Z, extent=[-10, 10, -10, 10], origin='lower', cmap='viridis')
        ax.set_title(name)
        plt.colorbar(im, ax=ax)
    
    plt.tight_layout()
    plt.savefig('height_functions_test.png', dpi=150)
    print("Saved: height_functions_test.png")
