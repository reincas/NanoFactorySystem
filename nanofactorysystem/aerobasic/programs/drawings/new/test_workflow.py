"""
Standalone Test for Height Function Structures

This script tests the core algorithms without nanofactorysystem dependencies.
"""

import numpy as np
from dataclasses import dataclass
from typing import Callable, List, Tuple, Optional, Iterator
from skimage.measure import label, regionprops, find_contours
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


# =============================================================================
# MOCK CLASSES (simulating nanofactorysystem interfaces)
# =============================================================================

@dataclass
class Point2D:
    X: float
    Y: float

    def __add__(self, other):
        return Point2D(self.X + other.X, self.Y + other.Y)


@dataclass
class Point3D:
    X: float
    Y: float
    Z: float

    def __add__(self, other):
        if isinstance(other, Point3D):
            return Point3D(self.X + other.X, self.Y + other.Y, self.Z + other.Z)
        elif isinstance(other, Point2D):
            return Point3D(self.X + other.X, self.Y + other.Y, self.Z)
        return NotImplemented


class CoordinateSystem:
    pass


class MockProgram:
    def __init__(self):
        self.commands = []
        self.segments = []

    def LINEAR(self, **kwargs):
        self.commands.append(("LINEAR", kwargs))

    def comment(self, text):
        self.commands.append(("COMMENT", text))

    def add_programm(self, other):
        if hasattr(other, 'segments'):
            self.segments.extend(other.segments)


# =============================================================================
# IMPORT CORE ALGORITHMS FROM height_function_structures.py
# (Copied here for standalone testing)
# =============================================================================

def _intersect_line_with_segment(p0, d, a, b):
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


def _hatch_polygon(polygon, angle_deg, distance):
    poly = np.array(polygon)
    if len(poly) < 3:
        return []

    theta = np.deg2rad(angle_deg)
    d = np.array([np.cos(theta), np.sin(theta)])
    n = np.array([-d[1], d[0]])

    projections = poly @ n
    proj_min, proj_max = projections.min(), projections.max()
    offsets = np.arange(proj_min, proj_max + distance, distance)

    segments = []
    edges = [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]

    for off in offsets:
        p0 = n * off
        ts = []
        for a, b in edges:
            t = _intersect_line_with_segment(p0, d, a, b)
            if t is not None:
                ts.append(t)

        if len(ts) < 2:
            continue

        ts.sort()
        filtered = [ts[0]]
        for t in ts[1:]:
            if abs(t - filtered[-1]) > 1e-9:
                filtered.append(t)
        ts = filtered

        for i in range(0, len(ts) - 1, 2):
            p_start = p0 + ts[i] * d
            p_end = p0 + ts[i + 1] * d
            if np.linalg.norm(p_end - p_start) > 1e-9:
                segments.append(((float(p_start[0]), float(p_start[1])),
                                 (float(p_end[0]), float(p_end[1]))))
    return segments


def _mask_to_polygons(mask, xs, ys, min_area=10):
    labels_img = label(mask.astype(np.uint8))
    regions = regionprops(labels_img)

    polygons = []
    for region in regions:
        if region.area < min_area:
            continue

        region_mask = (labels_img == region.label).astype(float)
        contours = find_contours(region_mask, 0.5)

        for contour in contours:
            poly = []
            for yi, xi in contour:
                x_coord = xs[0] + (xs[-1] - xs[0]) * xi / (len(xs) - 1)
                y_coord = ys[0] + (ys[-1] - ys[0]) * yi / (len(ys) - 1)
                poly.append([x_coord, y_coord])

            poly = np.array(poly)
            if len(poly) > 2 and not np.allclose(poly[0], poly[-1]):
                poly = np.vstack([poly, poly[0]])

            if len(poly) >= 4:
                polygons.append(poly)

    return polygons


# =============================================================================
# HEIGHT FUNCTIONS
# =============================================================================

class HeightFunctions:
    @staticmethod
    def sinusoidal(period, height, angle_deg=0, z0=0, phase=0):
        theta = np.deg2rad(angle_deg)

        def f(x, y):
            s = x * np.cos(theta) + y * np.sin(theta)
            return z0 + (height / 2) * np.sin(2 * np.pi / period * s + phase)

        return f

    @staticmethod
    def blazed_grating(period, height, angle_deg=0, z0=0):
        theta = np.deg2rad(angle_deg)

        def f(x, y):
            s = x * np.cos(theta) + y * np.sin(theta)
            return z0 + height * np.mod(s, period) / period

        return f

    @staticmethod
    def binary_grating(period, height, duty_cycle=0.5, angle_deg=0, z0=0):
        theta = np.deg2rad(angle_deg)

        def f(x, y):
            s = x * np.cos(theta) + y * np.sin(theta)
            frac = np.mod(s, period) / period
            return z0 + height * (frac < duty_cycle).astype(float)

        return f


# =============================================================================
# SLICING ENGINE
# =============================================================================

@dataclass
class SliceData:
    z_level: float
    polygons: list
    segments_2d: list

    def get_segments_3d(self):
        return [((x1, y1, self.z_level), (x2, y2, self.z_level))
                for (x1, y1), (x2, y2) in self.segments_2d]


def slice_height_function(height_func, x_range, y_range, z_min, z_max,
                          slice_size, hatch_size, hatch_angle_deg=0,
                          alternating_hatch=True, grid_resolution=400,
                          aperture=None):
    """Slice a height function into layers with hatching"""

    xs = np.linspace(x_range[0], x_range[1], grid_resolution)
    ys = np.linspace(y_range[0], y_range[1], grid_resolution)
    X, Y = np.meshgrid(xs, ys)

    Z = height_func(X, Y)

    if aperture is not None:
        aperture_mask = aperture(X, Y)
        Z = np.where(aperture_mask, Z, np.nan)

    n_slices = max(1, round((z_max - z_min) / slice_size))
    z_levels = np.linspace(z_min, z_max, n_slices + 1)

    slices = []

    for i, z_level in enumerate(z_levels):
        mask = (Z >= z_level) & ~np.isnan(Z)
        polygons = _mask_to_polygons(mask, xs, ys, min_area=10)

        if alternating_hatch:
            angle = hatch_angle_deg + i * 90
        else:
            angle = hatch_angle_deg

        all_segments = []
        for poly in polygons:
            segs = _hatch_polygon(poly, angle, hatch_size)
            all_segments.extend(segs)

        slices.append(SliceData(
            z_level=z_level,
            polygons=polygons,
            segments_2d=all_segments
        ))

    return slices


# =============================================================================
# TILE MANAGER
# =============================================================================

@dataclass
class TileBounds:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    center_x: float
    center_y: float

    @property
    def as_tuple(self):
        return (self.x_min, self.x_max, self.y_min, self.y_max)


def generate_tiles(x_range, y_range, fov_size=(150, 150), usable_fraction=0.85):
    """Generate tiles for a given area"""
    x_min, x_max = x_range
    y_min, y_max = y_range

    tile_width = fov_size[0] * usable_fraction
    tile_height = fov_size[1] * usable_fraction

    width = x_max - x_min
    height = y_max - y_min

    if width <= tile_width and height <= tile_height:
        return [TileBounds(x_min, x_max, y_min, y_max,
                           (x_min + x_max) / 2, (y_min + y_max) / 2)]

    n_tiles_x = int(np.ceil(width / tile_width))
    n_tiles_y = int(np.ceil(height / tile_height))

    tiles = []
    for row in range(n_tiles_y):
        for col in range(n_tiles_x):
            tx_min = x_min + col * tile_width
            tx_max = min(tx_min + tile_width, x_max)
            ty_min = y_min + row * tile_height
            ty_max = min(ty_min + tile_height, y_max)

            tiles.append(TileBounds(tx_min, tx_max, ty_min, ty_max,
                                    (tx_min + tx_max) / 2, (ty_min + ty_max) / 2))
    return tiles


def clip_segments_to_bounds(segments, bounds):
    """Clip segments to rectangular bounds"""
    x_min, x_max, y_min, y_max = bounds
    clipped = []
    for (x1, y1), (x2, y2) in segments:
        if (x_min <= x1 <= x_max and y_min <= y1 <= y_max and
                x_min <= x2 <= x_max and y_min <= y2 <= y_max):
            clipped.append(((x1, y1), (x2, y2)))
    return clipped


# =============================================================================
# COMPLETE WORKFLOW TEST
# =============================================================================

def test_complete_workflow():
    """Test the complete workflow: Height Function → Slicing → Tiling → Segments"""

    print("=" * 70)
    print("COMPLETE WORKFLOW TEST")
    print("=" * 70)

    # === STEP 1: Define Structure Parameters ===
    print("\n[STEP 1] Define Structure Parameters")

    center = Point3D(X=0, Y=0, Z=-2)
    width = 200.0  # µm - larger than FOV to test stitching
    length = 150.0  # µm

    # Grating_63 parameters
    period = 3.0
    height = 1.0
    grating_angle = 30  # degrees

    # Process parameters
    hatch_size = 0.5
    slice_size = 0.2

    # FOV parameters
    fov_size = (150, 150)
    usable_fov_fraction = 0.85

    print(f"  Center: ({center.X}, {center.Y}, {center.Z})")
    print(f"  Size: {width} x {length} µm")
    print(f"  Grating: period={period}µm, height={height}µm, angle={grating_angle}°")
    print(f"  FOV: {fov_size[0]} x {fov_size[1]} µm (usable: {usable_fov_fraction * 100}%)")

    # === STEP 2: Create Height Function ===
    print("\n[STEP 2] Create Height Function")

    height_func = HeightFunctions.sinusoidal(
        period=period,
        height=height,
        angle_deg=grating_angle,
        z0=height / 2  # Center around height/2 so range is [0, height]
    )

    z_min, z_max = 0.0, height
    print(f"  z(x,y) = {height / 2} + {height / 2}·sin(2π/{period}·s(x,y))")
    print(f"  Z range: [{z_min}, {z_max}]")

    # === STEP 3: Check if Stitching Needed ===
    print("\n[STEP 3] Check Stitching Requirements")

    tile_width = fov_size[0] * usable_fov_fraction
    tile_height = fov_size[1] * usable_fov_fraction
    needs_stitching = width > tile_width or length > tile_height

    print(f"  Structure: {width} x {length} µm")
    print(f"  Usable tile: {tile_width} x {tile_height} µm")
    print(f"  Needs stitching: {needs_stitching}")

    # === STEP 4: Perform Slicing ===
    print("\n[STEP 4] Slice Structure")

    x_range = (center.X - width / 2, center.X + width / 2)
    y_range = (center.Y - length / 2, center.Y + length / 2)

    # Optional aperture (circular)
    def circular_aperture(x, y):
        return (x - center.X) ** 2 + (y - center.Y) ** 2 <= (min(width, length) / 2) ** 2

    slices = slice_height_function(
        height_func=height_func,
        x_range=x_range,
        y_range=y_range,
        z_min=z_min,
        z_max=z_max,
        slice_size=slice_size,
        hatch_size=hatch_size,
        hatch_angle_deg=grating_angle,  # Hatch parallel to grating
        alternating_hatch=True,
        aperture=circular_aperture
    )

    print(f"  Number of slices: {len(slices)}")
    total_segments = sum(len(s.segments_2d) for s in slices)
    print(f"  Total segments (before tiling): {total_segments}")

    for i, s in enumerate(slices[:3]):
        print(f"    Slice {i}: z={s.z_level:.3f}, {len(s.polygons)} polygons, {len(s.segments_2d)} segments")
    if len(slices) > 3:
        print(f"    ... and {len(slices) - 3} more slices")

    # === STEP 5: Generate Tiles (if needed) ===
    print("\n[STEP 5] Generate Tiles")

    tiles = generate_tiles(x_range, y_range, fov_size, usable_fov_fraction)
    print(f"  Number of tiles: {len(tiles)}")

    for i, tile in enumerate(tiles):
        print(f"    Tile {i}: center=({tile.center_x:.1f}, {tile.center_y:.1f}), "
              f"bounds=[{tile.x_min:.1f}, {tile.x_max:.1f}] x [{tile.y_min:.1f}, {tile.y_max:.1f}]")

    # === STEP 6: Generate Programs (TILE_FIRST strategy) ===
    print("\n[STEP 6] Generate Programs (TILE_FIRST strategy)")

    programs = []
    total_segments_after_clipping = 0

    for tile_idx, tile in enumerate(tiles):
        tile_programs = []

        for slice_idx, slice_data in enumerate(slices):
            # Clip segments to tile bounds
            clipped = clip_segments_to_bounds(slice_data.segments_2d, tile.as_tuple)

            if clipped:
                # Create program data
                program_data = {
                    'tile_idx': tile_idx,
                    'slice_idx': slice_idx,
                    'z_level': slice_data.z_level,
                    'tile_center': (tile.center_x, tile.center_y),
                    'segments': clipped,
                    'n_segments': len(clipped)
                }
                tile_programs.append(program_data)
                total_segments_after_clipping += len(clipped)

        programs.append({
            'tile_idx': tile_idx,
            'tile_center': (tile.center_x, tile.center_y),
            'layer_programs': tile_programs
        })

    print(f"  Total segments after clipping: {total_segments_after_clipping}")
    print(f"  Programs generated: {sum(len(p['layer_programs']) for p in programs)}")

    # === STEP 7: Simulate Execution Order ===
    print("\n[STEP 7] Execution Order (TILE_FIRST)")
    print("  " + "-" * 50)

    for prog in programs:
        print(f"  MOVE TO TILE {prog['tile_idx']} at ({prog['tile_center'][0]:.1f}, {prog['tile_center'][1]:.1f})")
        for lp in prog['layer_programs'][:2]:
            print(f"    → Layer z={lp['z_level']:.3f}: {lp['n_segments']} segments")
        if len(prog['layer_programs']) > 2:
            print(f"    → ... and {len(prog['layer_programs']) - 2} more layers")

    # === VISUALIZATION ===
    print("\n[VISUALIZATION] Creating plots...")

    fig = plt.figure(figsize=(16, 10))

    # 1) Height function
    ax1 = fig.add_subplot(2, 3, 1, projection='3d')
    xs = np.linspace(x_range[0], x_range[1], 100)
    ys = np.linspace(y_range[0], y_range[1], 100)
    X, Y = np.meshgrid(xs, ys)
    Z = height_func(X, Y)
    Z_masked = np.where(circular_aperture(X, Y), Z, np.nan)
    ax1.plot_surface(X, Y, Z_masked, cmap='viridis', alpha=0.8)
    ax1.set_title(f"Height Function\n(period={period}µm, angle={grating_angle}°)")
    ax1.set_xlabel('X (µm)')
    ax1.set_ylabel('Y (µm)')

    # 2) Top view with tiles
    ax2 = fig.add_subplot(2, 3, 2)
    im = ax2.imshow(Z_masked, extent=[*x_range, *y_range], origin='lower', cmap='viridis')
    plt.colorbar(im, ax=ax2, label='z (µm)')
    for i, tile in enumerate(tiles):
        rect = plt.Rectangle((tile.x_min, tile.y_min),
                             tile.x_max - tile.x_min, tile.y_max - tile.y_min,
                             fill=False, edgecolor='red', linewidth=2)
        ax2.add_patch(rect)
        ax2.plot(tile.center_x, tile.center_y, 'r+', markersize=10)
        ax2.text(tile.center_x, tile.center_y + 5, f'T{i}', ha='center', color='red')
    ax2.set_title(f"Top View with Tiles ({len(tiles)} tiles)")
    ax2.set_xlabel('X (µm)')
    ax2.set_ylabel('Y (µm)')

    # 3) Polygons for selected slice
    ax3 = fig.add_subplot(2, 3, 3)
    mid_slice = slices[len(slices) // 2]
    for poly in mid_slice.polygons:
        ax3.fill(poly[:, 0], poly[:, 1], alpha=0.5, edgecolor='black')
    ax3.set_title(f"Polygons at z={mid_slice.z_level:.3f}")
    ax3.set_aspect('equal')
    ax3.set_xlabel('X (µm)')
    ax3.set_ylabel('Y (µm)')

    # 4) All hatch segments (2D)
    ax4 = fig.add_subplot(2, 3, 4)
    for s in slices:
        for (x1, y1), (x2, y2) in s.segments_2d[::3]:  # Every 3rd for visibility
            ax4.plot([x1, x2], [y1, y2], 'b-', linewidth=0.3, alpha=0.5)
    ax4.set_title(f"All Hatch Segments\n({total_segments} total)")
    ax4.set_aspect('equal')
    ax4.set_xlim(*x_range)
    ax4.set_ylim(*y_range)
    ax4.set_xlabel('X (µm)')
    ax4.set_ylabel('Y (µm)')

    # 5) 3D segments
    ax5 = fig.add_subplot(2, 3, 5, projection='3d')
    for s in slices[::2]:  # Every other slice
        z = s.z_level
        for (x1, y1), (x2, y2) in s.segments_2d[::5]:
            ax5.plot([x1, x2], [y1, y2], [z, z], 'b-', linewidth=0.3, alpha=0.5)
    ax5.set_title("3D Hatch Segments")
    ax5.set_xlabel('X')
    ax5.set_ylabel('Y')
    ax5.set_zlabel('Z')

    # 6) Summary
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis('off')
    summary = f"""
    WORKFLOW SUMMARY
    ════════════════════════════════════════

    Structure:
      • Size: {width} × {length} µm
      • Grating: period={period}µm, height={height}µm
      • Angle: {grating_angle}°

    Slicing:
      • Slice size: {slice_size} µm
      • Hatch size: {hatch_size} µm
      • Number of slices: {len(slices)}

    Tiling:
      • FOV: {fov_size[0]} × {fov_size[1]} µm
      • Usable: {usable_fov_fraction * 100}%
      • Tiles needed: {len(tiles)}

    Output:
      • Total segments: {total_segments}
      • After clipping: {total_segments_after_clipping}
      • Programs: {sum(len(p['layer_programs']) for p in programs)}

    Strategy: TILE_FIRST
      (Complete all layers per tile before moving)
    """
    ax6.text(0.05, 0.95, summary, transform=ax6.transAxes, fontfamily='monospace',
             fontsize=9, verticalalignment='top')

    plt.tight_layout()
    plt.savefig('/home/claude/workflow_test.png', dpi=150)
    print("  Saved: workflow_test.png")

    print("\n" + "=" * 70)
    print("WORKFLOW TEST COMPLETE")
    print("=" * 70)

    return slices, tiles, programs


if __name__ == '__main__':
    slices, tiles, programs = test_complete_workflow()