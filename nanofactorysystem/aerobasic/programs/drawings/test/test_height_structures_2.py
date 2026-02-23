# Test Import
from nanofactorysystem.aerobasic.programs.drawings import (
    BinaryGrating,
    Apertures,
    DrawableAeroBasicProgram,
)
from nanofactorysystem.devices.coordinate_system import Point3D

print("Import erfolgreich!")

# Struktur-Test
g = BinaryGrating(
    center=Point3D(0, 0, 0),
    width=1000, length=1000,
    period=10, height=2,
    duty_cycle=0.5,
    base_height=0,
    hatch_size=0.3,
    slice_size=0.3,
    velocity=10000,
    acceleration=100000,
    fov_size=(150, 150),
    usable_fov_fraction=0.85,
)
print(f"Struktur erstellt: {g}")
print(f"Tiles: {g.n_tiles}")