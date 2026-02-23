"""
Practical examples for using the stitching system in your experiments.

This file demonstrates:
1. How to integrate stitching with your experiment workflow
2. When to use stitching vs. grid arrangement
3. Best practices for different scenarios
"""

import numpy as np

from nanofactorysystem.devices.coordinate_system import Point3D
from nanofactorysystem.aerobasic.programs.drawings.basic_structures import Square, Circle
from nanofactorysystem.aerobasic.programs.drawings.stitching import (
    LargeStructureStitcher,
    StitchedStructure,
    StitchingStrategy,
    stitch_if_needed
)


# ============================================================================
# EXAMPLE 1: Simple Stitching Decision
# ============================================================================

def example_1_basic_stitching():
    """
    Basic example: Automatically stitch if structure is too large.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Stitching Decision")
    print("=" * 70)

    # Your objective's FOV size
    FOV_SIZE = (100, 100)  # µm (for ZEISS 20X as example)

    # Create a structure
    structure = Square(
        center=Point3D(0, 0, -2),
        side_length=250,  # Larger than FOV!
        filled=True,
        hatch_size=0.5
    )

    # Automatically handle stitching
    stitched = stitch_if_needed(
        structure=structure,
        fov_size=FOV_SIZE,
        overlap=0.1  # 10% overlap
    )

    # Print information
    stitched.print_info()

    # Process tiles
    if stitched.needs_stitching:
        print(f"\n✓ Structure requires stitching into {stitched.num_tiles} tiles")
        print(f"  Processing order:")
        for tile in stitched.get_ordered_tiles():
            print(f"    {tile}")
    else:
        print(f"\n✓ Structure fits in FOV - no stitching needed")


# ============================================================================
# EXAMPLE 2: Integration with Experiment System
# ============================================================================

def example_2_experiment_integration():
    """
    Show how to integrate stitching with your experiment workflow.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Experiment Integration")
    print("=" * 70)

    # Configuration for your objective
    ZEISS_20X_FOV = (100, 100)
    ZEISS_63X_FOV = (30, 30)

    # Choose your objective
    current_objective = "20X"
    fov_size = ZEISS_20X_FOV if current_objective == "20X" else ZEISS_63X_FOV

    print(f"Using {current_objective} objective with FOV: {fov_size} µm")

    # Create your structures
    structures = [
        ("small_square", Square(Point3D(0, 0, -2), side_length=50, filled=True)),
        ("large_square", Square(Point3D(100, 0, -2), side_length=200, filled=True)),
        ("huge_circle", Circle(Point3D(0, 100, -2), radius=150, filled=True)),
    ]

    # Process each structure
    stitcher = LargeStructureStitcher(fov_size=fov_size, overlap=0.1)

    total_tiles = 0
    for name, structure in structures:
        needs_stitch = stitcher.needs_stitching(structure)
        tiles = stitcher.create_tiles(structure)

        print(f"\n{name}:")
        print(f"  Needs stitching: {needs_stitch}")
        print(f"  Number of tiles: {len(tiles)}")

        if needs_stitch:
            info = stitcher.get_stitching_info(structure)
            print(f"  Grid size: {info['grid_size']}")

        total_tiles += len(tiles)

    print(f"\nTotal tiles to print: {total_tiles}")


# ============================================================================
# EXAMPLE 3: Choosing the Right Strategy
# ============================================================================

def example_3_strategy_comparison():
    """
    Compare different stitching strategies for the same structure.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Strategy Comparison")
    print("=" * 70)

    # Large structure
    structure = Square(
        center=Point3D(0, 0, -2),
        side_length=300,
        filled=True,
        hatch_size=1.0
    )

    strategies = [
        (StitchingStrategy.LAYER_FIRST, "Best for uniform layer exposure"),
        (StitchingStrategy.TILE_FIRST, "Best for minimizing drift"),
        (StitchingStrategy.SNAKE_PATTERN, "Best for speed")
    ]

    for strategy, description in strategies:
        print(f"\n{strategy.value.upper()}:")
        print(f"  {description}")

        stitched = StitchedStructure(
            structure=structure,
            fov_size=(100, 100),
            overlap=0.1,
            strategy=strategy
        )

        ordered_tiles = stitched.get_ordered_tiles()
        print(f"  Processing order: {[t.tile_id for t in ordered_tiles]}")

        # Calculate movement distance (simplified)
        total_distance = 0
        for i in range(len(ordered_tiles) - 1):
            t1 = ordered_tiles[i]
            t2 = ordered_tiles[i + 1]
            dx = t2.center_offset.X - t1.center_offset.X
            dy = t2.center_offset.Y - t1.center_offset.Y
            distance = np.sqrt(dx ** 2 + dy ** 2)
            total_distance += distance

        print(f"  Total XY travel distance: {total_distance:.1f} µm")


# ============================================================================
# EXAMPLE 4: Stitching vs. Grid Arrangement
# ============================================================================

def example_4_stitching_vs_grid():
    """
    Understand when to use stitching vs. when to use grid arrangement.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Stitching vs. Grid Arrangement")
    print("=" * 70)

    FOV_SIZE = (100, 100)

    print("\nScenario 1: ONE LARGE STRUCTURE")
    print("-" * 70)
    print("Use Case: Single 300x300 µm square")
    print("Solution: STITCHING ✓")
    print("Reason: Need to break one structure into tiles\n")

    large_single = Square(Point3D(0, 0, -2), side_length=300, filled=True)
    stitched = stitch_if_needed(large_single, FOV_SIZE)
    print(f"  → Creates {stitched.num_tiles} tiles with overlap")

    print("\n" + "-" * 70)
    print("\nScenario 2: MANY SMALL STRUCTURES")
    print("-" * 70)
    print("Use Case: 100 small 10x10 µm squares in array")
    print("Solution: GRID ARRANGEMENT (not stitching) ✓")
    print("Reason: Each structure fits in FOV, just arrange them\n")

    small_structures = []
    grid_size = 10
    for i in range(grid_size):
        for j in range(grid_size):
            x = i * 15  # 15 µm spacing
            y = j * 15
            small_structures.append(
                Square(Point3D(x, y, -2), side_length=10, filled=True)
            )

    print(f"  → Creates {len(small_structures)} independent structures")
    print(f"  → Total area: {grid_size * 15} x {grid_size * 15} µm")
    print(f"  → Each structure individually fits in FOV")

    print("\n" + "-" * 70)
    print("\nScenario 3: COMBINATION")
    print("-" * 70)
    print("Use Case: Array of large structures")
    print("Solution: GRID + STITCHING ✓")
    print("Reason: Need to arrange AND tile each large structure\n")

    large_structures = []
    for i in range(3):
        for j in range(3):
            x = i * 300
            y = j * 300
            structure = Square(Point3D(x, y, -2), side_length=200, filled=True)
            stitched = stitch_if_needed(structure, FOV_SIZE)
            large_structures.append(stitched)

    total_tiles = sum(s.num_tiles for s in large_structures)
    print(f"  → {len(large_structures)} structures in grid")
    print(f"  → Each structure needs {large_structures[0].num_tiles} tiles")
    print(f"  → Total tiles: {total_tiles}")


# ============================================================================
# EXAMPLE 5: Overlap Configuration
# ============================================================================

def example_5_overlap_tuning():
    """
    Understand how overlap affects stitching quality and print time.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Overlap Tuning")
    print("=" * 70)

    structure = Square(Point3D(0, 0, -2), side_length=250, filled=True)

    overlaps = [0.0, 0.05, 0.1, 0.15, 0.2]

    print("\nOverlap Comparison:")
    print("-" * 70)
    print(f"{'Overlap':<10} {'Tiles':<8} {'Quality':<20} {'Speed':<15}")
    print("-" * 70)

    for overlap in overlaps:
        stitcher = LargeStructureStitcher(
            fov_size=(100, 100),
            overlap=overlap
        )
        tiles = stitcher.create_tiles(structure)

        quality = {
            0.0: "Poor (visible seams)",
            0.05: "Fair (minor seams)",
            0.1: "Good (recommended)",
            0.15: "Excellent",
            0.2: "Overkill"
        }[overlap]

        speed = {
            0.0: "Fastest",
            0.05: "Fast",
            0.1: "Normal",
            0.15: "Slow",
            0.2: "Slowest"
        }[overlap]

        print(f"{overlap * 100:>5.0f}%     {len(tiles):<8} {quality:<20} {speed:<15}")

    print("\nRecommendations:")
    print("  • 0%:   Only for testing - expect visible seams")
    print("  • 5%:   Minimum for production")
    print("  • 10%:  ✓ RECOMMENDED - good balance")
    print("  • 15%:  High quality, slower")
    print("  • 20%:  Rarely needed, significantly slower")


# ============================================================================
# EXAMPLE 6: Practical Workflow
# ============================================================================

def example_6_complete_workflow():
    """
    Complete workflow from structure creation to tile processing.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Complete Workflow")
    print("=" * 70)

    # Step 1: Define your parameters
    print("\nStep 1: Define Parameters")
    print("-" * 70)

    FOV_SIZE = (100, 100)  # Your objective's FOV
    OVERLAP = 0.1  # 10% overlap
    STRATEGY = StitchingStrategy.LAYER_FIRST

    print(f"FOV Size: {FOV_SIZE} µm")
    print(f"Overlap: {OVERLAP * 100:.0f}%")
    print(f"Strategy: {STRATEGY.value}")

    # Step 2: Create structure
    print("\nStep 2: Create Structure")
    print("-" * 70)

    structure = Circle(
        center=Point3D(0, 0, -2),
        radius=150,  # Large circle
        filled=True,
        hatch_size=0.5,
        resolution=200
    )

    x_min, x_max, y_min, y_max = structure.bounding_box
    width = x_max - x_min
    height = y_max - y_min
    print(f"Structure: Circle with radius 150 µm")
    print(f"Bounding box: {width:.1f} x {height:.1f} µm")

    # Step 3: Check if stitching is needed
    print("\nStep 3: Check Stitching Requirement")
    print("-" * 70)

    stitcher = LargeStructureStitcher(FOV_SIZE, OVERLAP, STRATEGY)
    needs_stitch = stitcher.needs_stitching(structure)

    print(f"Needs stitching: {needs_stitch}")

    if needs_stitch:
        # Step 4: Create tiles
        print("\nStep 4: Create Tiles")
        print("-" * 70)

        tiles = stitcher.create_tiles(structure)
        print(f"Number of tiles: {len(tiles)}")

        num_x, num_y = stitcher.calculate_tile_grid(structure)
        print(f"Grid layout: {num_x} x {num_y}")

        # Step 5: Get processing order
        print("\nStep 5: Get Processing Order")
        print("-" * 70)

        ordered_tiles = stitcher.get_tile_order(tiles)
        print(f"Processing {len(ordered_tiles)} tiles in order:")
        for i, tile in enumerate(ordered_tiles, 1):
            row, col = tile.grid_position
            print(f"  {i}. Tile {tile.tile_id} at grid position [{row},{col}]")

        # Step 6: Process each tile
        print("\nStep 6: Process Tiles (Pseudo-code)")
        print("-" * 70)

        print("""
for tile in ordered_tiles:
    # Move stage to tile position
    move_to(tile.center_offset)

    # Draw the tile
    points = tile.structure.draw()
    execute_drawing(points)

    # Optional: Verify tile completion
    if verification_enabled:
        verify_tile(tile)
""")

        # Step 7: Estimate time
        print("\nStep 7: Estimate Print Time")
        print("-" * 70)

        time_per_tile = 60  # seconds (example)
        total_time = stitcher.estimate_print_time(tiles, time_per_tile)

        print(f"Estimated time per tile: {time_per_tile} seconds")
        print(f"Total estimated time: {total_time:.0f} seconds ({total_time / 60:.1f} minutes)")

    else:
        print("\n✓ Structure fits in FOV - no stitching required")
        print("  Can proceed with normal printing")


# ============================================================================
# HELPER: Decision Tree
# ============================================================================

def print_decision_tree():
    """
    Print a decision tree to help choose the right approach.
    """
    print("\n" + "=" * 70)
    print("DECISION TREE: Stitching vs. Grid")
    print("=" * 70)

    print("""
┌─ Is your structure larger than FOV?
│
├─ YES → Use STITCHING
│  │
│  ├─ Single large structure?
│  │  └─ Use: stitch_if_needed()
│  │
│  └─ Multiple large structures?
│     └─ Use: Grid arrangement + stitching for each
│
└─ NO → Do you have multiple structures?
   │
   ├─ YES → Use GRID ARRANGEMENT (not stitching)
   │  └─ Simply arrange them with spacing
   │
   └─ NO → Single structure, fits in FOV
      └─ Print normally, no special handling needed

FOV Sizes (typical):
  • ZEISS 20X: ~100 x 100 µm
  • ZEISS 63X: ~30 x 30 µm
  • ZEISS 100X: ~20 x 20 µm
""")


# ============================================================================
# MAIN: Run all examples
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("STITCHING SYSTEM: PRACTICAL EXAMPLES")
    print("=" * 70)

    # Run all examples
    example_1_basic_stitching()
    example_2_experiment_integration()
    example_3_strategy_comparison()
    example_4_stitching_vs_grid()
    example_5_overlap_tuning()
    example_6_complete_workflow()

    # Print decision tree
    print_decision_tree()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Integrate stitching into your experiment files")
    print("  2. Test with small structures first")
    print("  3. Tune overlap based on your results")
    print("  4. Choose strategy based on your priorities")
    print("=" * 70 + "\n")