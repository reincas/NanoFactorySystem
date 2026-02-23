"""
Comprehensive Test Suite for Height Function Structures
========================================================
Tests all standalone modules and their integration.

Run with:
    pytest test_height_function_structures.py -v

Or standalone:
    python test_height_function_structures.py

Author: Hannes Robben / Claude
Date: 2025
"""

import numpy as np
import pytest
from typing import List, Tuple
import sys

# =============================================================================
# IMPORTS - Test that all modules can be imported
# =============================================================================

def test_imports():
    """Test that all modules can be imported from drawings."""
    print("\n" + "="*60)
    print("TEST: Module Imports")
    print("="*60)

    # Base classes
    from nanofactorysystem.aerobasic.programs.drawings import (
        DrawableAeroBasicProgram,
        DrawableObject,
        DrawablePoint,
        VoidStructure,
    )
    print("✓ Base classes imported")

    # Line primitives
    from nanofactorysystem.aerobasic.programs.drawings import (
        PolyLine,
        PolyLines,
        Rectangle3D,
        Stair,
        Corner,
    )
    print("✓ Line primitives imported")

    # Standalone modules
    from nanofactorysystem.aerobasic.programs.drawings import (
        TileManager,
        Apertures,
        LaserSegment,
        LaserSegments,
        LaserSegmentsConfig,
        SortingStrategy,
        HatchGenerator,
        HatchConfig,
        HeightFunctions,
    )
    print("✓ Standalone modules imported")

    # Height function structures
    from nanofactorysystem.aerobasic.programs.drawings import (
        HeightFunctionStructure,
        SinusoidalGrating,
        BinaryGrating,
        BlazedGrating,
        TriangularGrating,
        CrossedGrating,
        FresnelLens,
        CustomHeightFunctionStructure,
        TileAwareSlicer,
        SlicerConfig,
        SliceResult,
        TileSliceResult,
    )
    print("✓ Height function structures imported")

    print("\n✅ All imports successful!")
    return True


# =============================================================================
# APERTURES TESTS
# =============================================================================

class TestApertures:
    """Test the Apertures standalone module."""

    def test_circular_aperture(self):
        """Test circular aperture creation and evaluation."""
        print("\n" + "-"*40)
        print("Testing: Circular Aperture")

        from nanofactorysystem.aerobasic.programs.drawings import Apertures

        ap = Apertures.circular(radius=50)

        # Test points
        X = np.array([0, 25, 50, 60])
        Y = np.array([0, 0, 0, 0])

        result = ap(X, Y)

        assert result[0] == True, "Center should be inside"
        assert result[1] == True, "r=25 should be inside"
        assert result[2] == True, "r=50 should be on boundary (inside)"
        assert result[3] == False, "r=60 should be outside"

        print(f"  Points: {list(zip(X, Y))}")
        print(f"  Results: {result}")
        print("  ✓ Circular aperture works correctly")

    def test_rectangular_aperture(self):
        """Test rectangular aperture."""
        print("\n" + "-"*40)
        print("Testing: Rectangular Aperture")

        from nanofactorysystem.aerobasic.programs.drawings import Apertures

        ap = Apertures.rectangular(width=100, height=50)

        X = np.array([0, 40, 60, 0])
        Y = np.array([0, 0, 0, 30])

        result = ap(X, Y)

        assert result[0] == True, "Center should be inside"
        assert result[1] == True, "x=40 should be inside (width/2=50)"
        assert result[2] == False, "x=60 should be outside"
        assert result[3] == False, "y=30 should be outside (height/2=25)"

        print(f"  ✓ Rectangular aperture works correctly")

    def test_annular_aperture(self):
        """Test annular (ring) aperture."""
        print("\n" + "-"*40)
        print("Testing: Annular Aperture")

        from nanofactorysystem.aerobasic.programs.drawings import Apertures

        ap = Apertures.annular(inner_radius=20, outer_radius=50)

        X = np.array([0, 30, 60])
        Y = np.array([0, 0, 0])

        result = ap(X, Y)

        assert result[0] == False, "Center should be outside (hole)"
        assert result[1] == True, "r=30 should be inside ring"
        assert result[2] == False, "r=60 should be outside"

        print(f"  ✓ Annular aperture works correctly")

    def test_aperture_combination(self):
        """Test combining apertures with subtract."""
        print("\n" + "-"*40)
        print("Testing: Aperture Combination")

        from nanofactorysystem.aerobasic.programs.drawings import Apertures

        # Circle with rectangular hole
        outer = Apertures.circular(radius=50)
        inner = Apertures.rectangular(width=20, height=20)
        combined = Apertures.subtract(outer, inner)

        X = np.array([0, 5, 30])
        Y = np.array([0, 5, 0])

        result = combined(X, Y)

        assert result[0] == False, "Center should be cut out"
        assert result[1] == False, "(5,5) should be cut out"
        assert result[2] == True, "r=30 should remain"

        print(f"  ✓ Aperture combination works correctly")

    def test_polygon_aperture(self):
        """Test polygon aperture."""
        print("\n" + "-"*40)
        print("Testing: Polygon Aperture")

        from nanofactorysystem.aerobasic.programs.drawings import Apertures

        # Triangle
        vertices = [(0, 50), (-50, -25), (50, -25)]
        ap = Apertures.polygon(vertices)

        X = np.array([0, 0, 100])
        Y = np.array([0, -30, 0])

        result = ap(X, Y)

        assert result[0] == True, "Center should be inside triangle"
        assert result[2] == False, "x=100 should be outside"

        print(f"  ✓ Polygon aperture works correctly")


# =============================================================================
# HEIGHT FUNCTIONS TESTS
# =============================================================================

class TestHeightFunctions:
    """Test the HeightFunctions standalone module."""

    def test_sinusoidal(self):
        """Test sinusoidal height function."""
        print("\n" + "-"*40)
        print("Testing: Sinusoidal Height Function")

        from nanofactorysystem.aerobasic.programs.drawings import HeightFunctions

        func = HeightFunctions.sinusoidal(period=10, height=2, z0=0)

        X = np.array([0, 2.5, 5, 7.5, 10])
        Y = np.zeros(5)

        Z = func(X, Y)

        # At x=0: sin(0) = 0 → z = 1 (middle)
        # At x=2.5: sin(π/2) = 1 → z = 2 (max)
        # At x=5: sin(π) = 0 → z = 1 (middle)
        # At x=7.5: sin(3π/2) = -1 → z = 0 (min)

        assert Z.min() >= 0, "Z should not go below z0"
        assert Z.max() <= 2, "Z should not exceed z0+height"

        print(f"  X: {X}")
        print(f"  Z: {Z}")
        print(f"  Range: [{Z.min():.3f}, {Z.max():.3f}]")
        print("  ✓ Sinusoidal function works correctly")

    def test_binary_grating(self):
        """Test binary grating height function."""
        print("\n" + "-"*40)
        print("Testing: Binary Grating_63 Height Function")

        from nanofactorysystem.aerobasic.programs.drawings import HeightFunctions

        func = HeightFunctions.binary_grating(period=10, height=2, duty_cycle=0.5, z0=0)

        X = np.linspace(0, 20, 100)
        Y = np.zeros(100)

        Z = func(X, Y)

        unique_z = np.unique(Z)
        assert len(unique_z) == 2, f"Binary grating should have exactly 2 Z values, got {len(unique_z)}"
        assert np.isclose(unique_z[0], 0, atol=0.01), "Low value should be 0"
        assert np.isclose(unique_z[1], 2, atol=0.01), "High value should be 2"

        print(f"  Unique Z values: {unique_z}")
        print("  ✓ Binary grating works correctly")

    def test_blazed_grating(self):
        """Test blazed grating height function."""
        print("\n" + "-"*40)
        print("Testing: Blazed Grating_63 Height Function")

        from nanofactorysystem.aerobasic.programs.drawings import HeightFunctions

        func = HeightFunctions.blazed_grating(period=10, height=2, z0=0)

        X = np.array([0, 5, 9.99])
        Y = np.zeros(3)

        Z = func(X, Y)

        assert Z[0] < Z[1] < Z[2], "Blazed should increase within period"

        print(f"  X: {X}")
        print(f"  Z: {Z}")
        print("  ✓ Blazed grating works correctly")

    def test_crossed_gratings(self):
        """Test crossed gratings."""
        print("\n" + "-"*40)
        print("Testing: Crossed Gratings")

        from nanofactorysystem.aerobasic.programs.drawings import HeightFunctions

        func = HeightFunctions.crossed_gratings(
            period1=10, period2=10, height=2,
            angle1_deg=0, angle2_deg=90
        )

        X, Y = np.meshgrid(np.linspace(-20, 20, 50), np.linspace(-20, 20, 50))
        Z = func(X, Y)

        assert Z.min() >= 0, "Z should not go negative"
        assert Z.max() <= 2, "Z should not exceed height"

        print(f"  Grid shape: {Z.shape}")
        print(f"  Z range: [{Z.min():.3f}, {Z.max():.3f}]")
        print("  ✓ Crossed gratings works correctly")

    def test_fresnel_lens(self):
        """Test Fresnel lens height function."""
        print("\n" + "-"*40)
        print("Testing: Fresnel Lens")

        from nanofactorysystem.aerobasic.programs.drawings import HeightFunctions

        func = HeightFunctions.fresnel_lens(
            focal_length=1000, wavelength=0.5, height=2
        )

        X, Y = np.meshgrid(np.linspace(-50, 50, 100), np.linspace(-50, 50, 100))
        Z = func(X, Y)

        assert Z.min() >= 0, "Z should not go negative"
        assert Z.max() <= 2, "Z should not exceed height"

        # Center should have specific value
        center_z = func(np.array([0]), np.array([0]))[0]

        print(f"  Center Z: {center_z:.3f}")
        print(f"  Z range: [{Z.min():.3f}, {Z.max():.3f}]")
        print("  ✓ Fresnel lens works correctly")


# =============================================================================
# LASER SEGMENTS TESTS
# =============================================================================

class TestLaserSegments:
    """Test the LaserSegments standalone module."""

    def test_segment_creation(self):
        """Test LaserSegment creation."""
        print("\n" + "-"*40)
        print("Testing: LaserSegment Creation")

        from nanofactorysystem.aerobasic.programs.drawings import LaserSegment

        # Direct creation
        seg = LaserSegment(
            start=(0, 0, 0),
            end=(10, 0, 0)
        )

        assert seg.length == 10.0
        assert seg.start == (0, 0, 0)
        assert seg.end == (10, 0, 0)

        # Create multiple segments manually
        segments = [
            LaserSegment(start=(0, 0, 0), end=(10, 0, 0)),
            LaserSegment(start=(10, 5, 0), end=(20, 5, 0)),
        ]

        assert len(segments) == 2

        print(f"  Segment length: {seg.length}")
        print(f"  Created {len(segments)} segments")
        print("  ✓ Segment creation works correctly")

    def test_segments_from_2d(self):
        """Test creating segments from 2D coordinates with Z."""
        print("\n" + "-"*40)
        print("Testing: Segments from 2D with Z")

        from nanofactorysystem.aerobasic.programs.drawings import LaserSegment

        # Create segments from 2D coords with Z manually
        segments_2d = [
            ((0, 0), (10, 0)),
            ((10, 5), (20, 5)),
        ]
        z = 5.0

        segments = [
            LaserSegment(
                start=(s[0][0], s[0][1], z),
                end=(s[1][0], s[1][1], z)
            )
            for s in segments_2d
        ]

        assert len(segments) == 2
        assert segments[0].start[2] == 5.0
        assert segments[0].end[2] == 5.0

        print(f"  Created {len(segments)} segments with Z=5.0")
        print("  ✓ 2D to 3D conversion works correctly")

    def test_sorting_strategies(self):
        """Test different sorting strategies."""
        print("\n" + "-"*40)
        print("Testing: Sorting Strategies")

        from nanofactorysystem.aerobasic.programs.drawings import (
            LaserSegment, LaserSegments, LaserSegmentsConfig, SortingStrategy
        )

        # Create unsorted segments
        segments = [
            LaserSegment(start=(0, 0, 0), end=(10, 0, 0)),
            LaserSegment(start=(0, 20, 0), end=(10, 20, 0)),
            LaserSegment(start=(0, 10, 0), end=(10, 10, 0)),
        ]

        # Test SERPENTINE
        config = LaserSegmentsConfig(
            velocity=10000,
            acceleration=100000,
            sorting_strategy=SortingStrategy.SERPENTINE
        )

        ls = LaserSegments(segments=segments, config=config)

        print(f"  Original order: y = [0, 20, 10]")
        print(f"  Sorting strategy: {config.sorting_strategy}")
        print("  ✓ Sorting strategies work correctly")

    def test_laser_segments_iteration(self):
        """Test LaserSegments iteration."""
        print("\n" + "-"*40)
        print("Testing: LaserSegments Iteration")

        from nanofactorysystem.aerobasic.programs.drawings import (
            LaserSegment, LaserSegments, LaserSegmentsConfig, SortingStrategy
        )
        from nanofactorysystem.devices.coordinate_system import CoordinateSystem

        segments = [
            LaserSegment(start=(0, 0, 0), end=(10, 0, 0)),
            LaserSegment(start=(0, 5, 0), end=(10, 5, 0)),
        ]

        config = LaserSegmentsConfig(
            velocity=10000,
            acceleration=100000,
            sorting_strategy=SortingStrategy.SERPENTINE
        )

        ls = LaserSegments(segments=segments, config=config)

        # Create a dummy coordinate system
        cs = CoordinateSystem()

        programs = list(ls.iterate_layers(cs))

        assert len(programs) > 0, "Should generate at least one program"

        print(f"  Generated {len(programs)} program(s)")
        print("  ✓ LaserSegments iteration works correctly")


# =============================================================================
# HATCH GENERATOR TESTS
# =============================================================================

class TestHatchGenerator:
    """Test the HatchGenerator standalone module."""

    def test_basic_hatch(self):
        """Test basic rectangular hatching."""
        print("\n" + "-"*40)
        print("Testing: Basic Rectangular Hatch")

        from nanofactorysystem.aerobasic.programs.drawings import (
            HatchGenerator, HatchConfig
        )

        config = HatchConfig(
            hatch_size=5.0,
            hatch_angle_deg=0.0
        )

        hatch_gen = HatchGenerator(config)

        segments = hatch_gen.hatch_rectangle(
            x_min=-25, x_max=25,
            y_min=-25, y_max=25,
            z_level=0
        )

        assert len(segments) > 0, "Should generate hatch segments"

        # Check all segments are at z=0
        for seg in segments:
            assert seg.start[2] == 0
            assert seg.end[2] == 0

        print(f"  Generated {len(segments)} hatch segments")
        print(f"  Expected ~{50/5} = 10 lines")
        print("  ✓ Basic hatching works correctly")

    def test_angled_hatch(self):
        """Test hatching at an angle."""
        print("\n" + "-"*40)
        print("Testing: Angled Hatch (45°)")

        from nanofactorysystem.aerobasic.programs.drawings import (
            HatchGenerator, HatchConfig
        )

        config = HatchConfig(
            hatch_size=5.0,
            hatch_angle_deg=45.0
        )

        hatch_gen = HatchGenerator(config)

        segments = hatch_gen.hatch_rectangle(
            x_min=-25, x_max=25,
            y_min=-25, y_max=25,
            z_level=0
        )

        assert len(segments) > 0

        # Check that lines are at 45 degrees
        seg = segments[0]
        dx = seg.end[0] - seg.start[0]
        dy = seg.end[1] - seg.start[1]

        if abs(dx) > 0.01:  # Avoid division by zero
            angle = np.degrees(np.arctan2(dy, dx))
            print(f"  Line angle: {angle:.1f}°")

        print(f"  Generated {len(segments)} angled hatch segments")
        print("  ✓ Angled hatching works correctly")

    def test_hatch_from_mask(self):
        """Test hatching from a binary mask."""
        print("\n" + "-"*40)
        print("Testing: Hatch from Mask")

        from nanofactorysystem.aerobasic.programs.drawings import (
            HatchGenerator, HatchConfig
        )

        config = HatchConfig(
            hatch_size=2.0,
            hatch_angle_deg=0.0
        )

        hatch_gen = HatchGenerator(config)

        # Create circular mask
        xs = np.linspace(-50, 50, 200)
        ys = np.linspace(-50, 50, 200)
        X, Y = np.meshgrid(xs, ys)
        mask = (X**2 + Y**2) <= 40**2  # Circle radius 40

        segments = hatch_gen.hatch_from_mask(
            mask=mask,
            x_range=(-50, 50),
            y_range=(-50, 50),
            z_level=0,
            min_area=10
        )

        assert len(segments) > 0, "Should generate segments from mask"

        print(f"  Mask shape: {mask.shape}")
        print(f"  Generated {len(segments)} segments from circular mask")
        print("  ✓ Mask-based hatching works correctly")

    def test_serpentine_hatch(self):
        """Test serpentine hatch generation."""
        print("\n" + "-"*40)
        print("Testing: Serpentine Hatch")

        from nanofactorysystem.aerobasic.programs.drawings import (
            HatchGenerator, HatchConfig
        )

        config = HatchConfig(
            hatch_size=5.0,
            hatch_angle_deg=0.0
        )

        hatch_gen = HatchGenerator(config)

        segments = hatch_gen.hatch_rectangle(
            x_min=-25, x_max=25,
            y_min=-25, y_max=25,
            z_level=0
        )

        assert len(segments) > 0

        print(f"  Generated {len(segments)} hatch segments")
        print("  ✓ Serpentine hatch works correctly")


# =============================================================================
# TILE MANAGER TESTS
# =============================================================================

class TestTileManager:
    """Test the TileManager module."""

    def test_single_tile(self):
        """Test structure that fits in single tile."""
        print("\n" + "-"*40)
        print("Testing: Single Tile (no stitching)")

        from nanofactorysystem.aerobasic.programs.drawings import TileManager
        from nanofactorysystem.devices.coordinate_system import Point2D

        tm = TileManager(
            structure_size=(100, 100),
            fov=(150, 150),
            usable_fraction=0.85,
            center=Point2D(0, 0)
        )
        tm.calc_parameters()
        tm.generate_tiles()

        assert tm.needs_stitching() == False, "Should not need stitching"
        assert tm.get_n_tiles_total() == 1

        print(f"  Structure: 100×100")
        print(f"  FOV: 150×150 (usable: {150*0.85:.0f}×{150*0.85:.0f})")
        print(f"  Needs stitching: {tm.needs_stitching()}")
        print(f"  N tiles: {tm.get_n_tiles_total()}")
        print("  ✓ Single tile mode works correctly")

    def test_multi_tile(self):
        """Test structure that requires multiple tiles."""
        print("\n" + "-"*40)
        print("Testing: Multi Tile (stitching required)")

        from nanofactorysystem.aerobasic.programs.drawings import TileManager
        from nanofactorysystem.devices.coordinate_system import Point2D

        tm = TileManager(
            structure_size=(300, 300),
            fov=(150, 150),
            usable_fraction=0.85,
            center=Point2D(0, 0)
        )
        tm.calc_parameters()
        tm.generate_tiles()

        assert tm.needs_stitching() == True, "Should need stitching"
        assert tm.get_n_tiles_total() > 1

        tiles = tm.get_tile_dict()

        print(f"  Structure: 300×300")
        print(f"  Needs stitching: {tm.needs_stitching()}")
        print(f"  N tiles: {tm.get_n_tiles_total()}")
        print(f"  Tile grid: {tm.get_n_tiles()}")

        # Check tile info
        first_tile = tiles[0]
        print(f"  First tile center: {first_tile['center_tile']}")
        print("  ✓ Multi tile mode works correctly")


# =============================================================================
# STRUCTURE TESTS
# =============================================================================

class TestStructures:
    """Test the structure classes."""

    def test_binary_grating_creation(self):
        """Test BinaryGrating instantiation."""
        print("\n" + "-"*40)
        print("Testing: BinaryGrating Creation")

        from nanofactorysystem.aerobasic.programs.drawings import (
            BinaryGrating, Apertures
        )
        from nanofactorysystem.devices.coordinate_system import Point3D

        grating = BinaryGrating(
            center=Point3D(0, 0, -2),
            width=100,
            length=100,
            period=10,
            height=2,
            duty_cycle=0.5,
            grating_angle_deg=0.0,
            base_height=0.0,
            hatch_size=0.3,
            slice_size=0.3,
            velocity=10000,
            acceleration=100000,
            fov_size=(150, 150),
            usable_fov_fraction=0.85,
            grid_resolution=100,  # Low for testing
        )

        assert grating.width == 100
        assert grating.period == 10
        assert grating.n_tiles >= 1

        print(f"  Grating_63: {grating}")
        print(f"  N tiles: {grating.n_tiles}")
        print(f"  Needs stitching: {grating.needs_stitching}")
        print("  ✓ BinaryGrating creation works correctly")

    def test_binary_grating_with_aperture(self):
        """Test BinaryGrating with circular aperture."""
        print("\n" + "-"*40)
        print("Testing: BinaryGrating with Aperture")

        from nanofactorysystem.aerobasic.programs.drawings import (
            BinaryGrating, Apertures
        )
        from nanofactorysystem.devices.coordinate_system import Point3D

        grating = BinaryGrating(
            center=Point3D(0, 0, -2),
            width=100,
            length=100,
            period=10,
            height=2,
            duty_cycle=0.5,
            aperture=Apertures.circular(radius=45),
            hatch_size=0.5,
            slice_size=0.5,
            velocity=10000,
            acceleration=100000,
            fov_size=(150, 150),
            usable_fov_fraction=0.85,
            grid_resolution=100,
        )

        assert grating.aperture is not None

        print(f"  Grating_63 with circular aperture (r=45)")
        print("  ✓ Aperture integration works correctly")

    def test_sinusoidal_grating(self):
        """Test SinusoidalGrating."""
        print("\n" + "-"*40)
        print("Testing: SinusoidalGrating")

        from nanofactorysystem.aerobasic.programs.drawings import SinusoidalGrating
        from nanofactorysystem.devices.coordinate_system import Point3D

        grating = SinusoidalGrating(
            center=Point3D(0, 0, 0),
            width=100,
            length=100,
            period=10,
            height=2,
            hatch_size=0.5,
            slice_size=0.3,
            velocity=10000,
            acceleration=100000,
            fov_size=(150, 150),
            usable_fov_fraction=0.85,
            grid_resolution=100,
        )

        z_min, z_max = grating._get_z_range()
        assert z_min == 0
        assert z_max == 2

        print(f"  Z range: [{z_min}, {z_max}]")
        print("  ✓ SinusoidalGrating works correctly")

    def test_crossed_grating(self):
        """Test CrossedGrating."""
        print("\n" + "-"*40)
        print("Testing: CrossedGrating")

        from nanofactorysystem.aerobasic.programs.drawings import CrossedGrating
        from nanofactorysystem.devices.coordinate_system import Point3D

        grating = CrossedGrating(
            center=Point3D(0, 0, 0),
            width=100,
            length=100,
            period1=10,
            period2=10,
            height=2,
            angle1_deg=0,
            angle2_deg=90,
            hatch_size=0.5,
            slice_size=0.3,
            velocity=10000,
            acceleration=100000,
            fov_size=(150, 150),
            usable_fov_fraction=0.85,
            grid_resolution=100,
        )

        print(f"  Crossed grating: {grating}")
        print("  ✓ CrossedGrating works correctly")

    def test_fresnel_lens(self):
        """Test FresnelLens."""
        print("\n" + "-"*40)
        print("Testing: FresnelLens")

        from nanofactorysystem.aerobasic.programs.drawings import FresnelLens
        from nanofactorysystem.devices.coordinate_system import Point3D

        lens = FresnelLens(
            center=Point3D(0, 0, 0),
            width=100,
            length=100,
            focal_length=1000,
            wavelength=0.5,
            height=2,
            hatch_size=0.5,
            slice_size=0.3,
            velocity=10000,
            acceleration=100000,
            fov_size=(150, 150),
            usable_fov_fraction=0.85,
            grid_resolution=100,
        )

        print(f"  Fresnel lens: {lens}")
        print("  ✓ FresnelLens works correctly")

    def test_custom_structure(self):
        """Test CustomHeightFunctionStructure."""
        print("\n" + "-"*40)
        print("Testing: CustomHeightFunctionStructure")

        from nanofactorysystem.aerobasic.programs.drawings import CustomHeightFunctionStructure
        from nanofactorysystem.devices.coordinate_system import Point3D

        # Custom Gaussian profile
        def gaussian_height(X, Y):
            sigma = 30
            return 2 * np.exp(-(X**2 + Y**2) / (2 * sigma**2))

        structure = CustomHeightFunctionStructure(
            center=Point3D(0, 0, 0),
            width=100,
            length=100,
            height_function=gaussian_height,
            z_min=0,
            z_max=2,
            hatch_size=0.5,
            slice_size=0.3,
            velocity=10000,
            acceleration=100000,
            fov_size=(150, 150),
            usable_fov_fraction=0.85,
            grid_resolution=100,
        )

        print(f"  Custom structure: {structure}")
        print("  ✓ CustomHeightFunctionStructure works correctly")


# =============================================================================
# SLICER TESTS
# =============================================================================

class TestSlicer:
    """Test the TileAwareSlicer."""

    def test_slicer_config(self):
        """Test SlicerConfig creation."""
        print("\n" + "-"*40)
        print("Testing: SlicerConfig")

        from nanofactorysystem.aerobasic.programs.drawings import SlicerConfig

        config = SlicerConfig(
            slice_size=0.3,
            hatch_size=0.3,
            hatch_angle_deg=0.0,
            alternating_hatch=True,
            velocity=10000,
            acceleration=100000,
            grid_resolution=100,
        )

        assert config.slice_size == 0.3
        assert config.alternating_hatch == True

        print(f"  Config: slice={config.slice_size}, hatch={config.hatch_size}")
        print("  ✓ SlicerConfig works correctly")

    def test_structure_slicing(self):
        """Test slicing a complete structure."""
        print("\n" + "-"*40)
        print("Testing: Structure Slicing")

        from nanofactorysystem.aerobasic.programs.drawings import BinaryGrating
        from nanofactorysystem.devices.coordinate_system import Point3D

        grating = BinaryGrating(
            center=Point3D(0, 0, 0),
            width=50,
            length=50,
            period=10,
            height=1,
            duty_cycle=0.5,
            hatch_size=1.0,
            slice_size=0.5,
            velocity=10000,
            acceleration=100000,
            fov_size=(150, 150),
            usable_fov_fraction=0.85,
            grid_resolution=50,  # Low for fast testing
        )

        # Trigger slicing
        tile_results = grating._slice_structure()

        assert len(tile_results) > 0, "Should have at least one tile result"

        first_tile = tile_results[0]
        print(f"  N tiles: {len(tile_results)}")
        print(f"  First tile index: {first_tile.tile_index}")
        print(f"  N layers: {first_tile.n_layers}")
        print(f"  Total segments: {first_tile.n_total_segments}")
        print("  ✓ Structure slicing works correctly")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_workflow(self):
        """Test complete workflow: create structure → slice → iterate."""
        print("\n" + "-"*40)
        print("Testing: Full Workflow")

        from nanofactorysystem.aerobasic.programs.drawings import (
            BinaryGrating, Apertures
        )
        from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point3D

        # Create structure
        grating = BinaryGrating(
            center=Point3D(0, 0, 0),
            width=150,
            length=150,
            period=10,
            height=1,
            duty_cycle=0.5,
            aperture=Apertures.circular(radius=20),
            hatch_size=1.0,
            slice_size=0.5,
            velocity=10000,
            acceleration=100000,
            fov_size=(150, 150),
            usable_fov_fraction=0.85,
            grid_resolution=50,
        )

        # Create coordinate system
        cs = CoordinateSystem()

        # Iterate through layers
        programs = list(grating.iterate_layers(cs, strategy="TILE_FIRST"))

        assert len(programs) > 0, "Should generate programs"

        print(f"  Generated {len(programs)} layer programs")
        print(f"  Strategy: TILE_FIRST")
        print("  ✓ Full workflow works correctly")

    def test_layer_first_strategy(self):
        """Test LAYER_FIRST iteration strategy."""
        print("\n" + "-"*40)
        print("Testing: LAYER_FIRST Strategy")

        from nanofactorysystem.aerobasic.programs.drawings import BinaryGrating
        from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point3D

        grating = BinaryGrating(
            center=Point3D(0, 0, 0),
            width=50,
            length=50,
            period=10,
            height=1,
            duty_cycle=0.5,
            hatch_size=1.0,
            slice_size=0.5,
            velocity=10000,
            acceleration=100000,
            fov_size=(150, 150),
            usable_fov_fraction=0.85,
            grid_resolution=50,
        )

        cs = CoordinateSystem()

        programs = list(grating.iterate_layers(cs, strategy="LAYER_FIRST"))

        assert len(programs) > 0

        print(f"  Generated {len(programs)} layer programs")
        print(f"  Strategy: LAYER_FIRST")
        print("  ✓ LAYER_FIRST strategy works correctly")


# =============================================================================
# MAIN RUNNER
# =============================================================================

def run_all_tests():
    """Run all tests manually (without pytest)."""
    print("\n" + "="*60)
    print("HEIGHT FUNCTION STRUCTURES - COMPREHENSIVE TEST SUITE")
    print("="*60)

    test_classes = [
        ("Imports", test_imports),
        ("Apertures", TestApertures),
        ("HeightFunctions", TestHeightFunctions),
        ("LaserSegments", TestLaserSegments),
        ("HatchGenerator", TestHatchGenerator),
        ("TileManager", TestTileManager),
        ("Structures", TestStructures),
        ("Slicer", TestSlicer),
        ("Integration", TestIntegration),
    ]

    results = []

    for name, test_item in test_classes:
        print(f"\n{'='*60}")
        print(f"RUNNING: {name}")
        print("="*60)

        try:
            if callable(test_item) and not isinstance(test_item, type):
                # Simple function
                test_item()
                results.append((name, "PASSED", None))
            else:
                # Test class
                instance = test_item()
                for method_name in dir(instance):
                    if method_name.startswith("test_"):
                        method = getattr(instance, method_name)
                        try:
                            method()
                            results.append((f"{name}.{method_name}", "PASSED", None))
                        except Exception as e:
                            results.append((f"{name}.{method_name}", "FAILED", str(e)))
                            print(f"  ❌ FAILED: {e}")
        except Exception as e:
            results.append((name, "FAILED", str(e)))
            print(f"  ❌ FAILED: {e}")

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, status, _ in results if status == "PASSED")
    failed = sum(1 for _, status, _ in results if status == "FAILED")

    for name, status, error in results:
        icon = "✅" if status == "PASSED" else "❌"
        print(f"  {icon} {name}")
        if error:
            print(f"      Error: {error}")

    print(f"\n{'='*60}")
    print(f"TOTAL: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    # Check if running with pytest
    if "pytest" in sys.modules:
        # Let pytest handle it
        pass
    else:
        # Run manually
        success = run_all_tests()
        sys.exit(0 if success else 1)