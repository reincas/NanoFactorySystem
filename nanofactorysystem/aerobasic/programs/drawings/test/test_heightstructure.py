from nanofactorysystem.aerobasic.programs.drawings import BinaryGrating
from nanofactorysystem.devices.coordinate_system import Point3D

structure = BinaryGrating(
    center=Point3D(0, 0, -2),
    width=1000,  # µm
    length=1000,  # µm
    period=10,  # µm
    height=2,  # µm
    duty_cycle=5,  # µm
    grating_angle_deg=0.0,
    base_height=2.0,  # µm
    hatch_size=0.2,
    slice_size=0.2,
    velocity=10000,
    acceleration=10000,
    aperture=None,
    hatch_angle_deg=0.0,
    alternating_hatch=True,
    fov_size=(150, 150),
    usable_fov_fraction=0.85,
    grid_resolution=1000)

slices = structure._slice_structure()

print("a")


