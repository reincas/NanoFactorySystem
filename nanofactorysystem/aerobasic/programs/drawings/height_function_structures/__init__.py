"""
Height Function Structures Package
==================================
Grating_63 and DOE structure classes for 2PP fabrication.

This package provides:
- HeightFunctionStructure base class
- Concrete implementations (gratings, lenses)
- TileAwareSlicer for layer generation

Author: Hannes Robben / Claude
Date: 2025
"""

# =============================================================================
# STRUCTURE CLASSES
# =============================================================================
from .structures import (
    # Base class
    HeightFunctionStructure,

    # Gratings
    SinusoidalGrating,
    BinaryGrating,
    BlazedGrating,
    TriangularGrating,
    CrossedGrating,

    # Lenses
    FresnelLens,

    # Custom
    CustomHeightFunctionStructure,
)

# =============================================================================
# SLICER
# =============================================================================
from .slicer import (
    TileAwareSlicer,
    SlicerConfig,
    SliceResult,
    TileSliceResult,
)

# =============================================================================
# PUBLIC API
# =============================================================================
__all__ = [
    # Structures
    "HeightFunctionStructure",
    "SinusoidalGrating",
    "BinaryGrating",
    "BlazedGrating",
    "TriangularGrating",
    "CrossedGrating",
    "FresnelLens",
    "CustomHeightFunctionStructure",

    # Slicer
    "TileAwareSlicer",
    "SlicerConfig",
    "SliceResult",
    "TileSliceResult",
]