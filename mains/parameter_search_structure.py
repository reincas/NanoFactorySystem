from nanofactorysystem.aerobasic.programs.drawings import DrawableObject
from nanofactorysystem.aerobasic.programs.drawings.lines import Stair
from nanofactorysystem.devices.coordinate_system import Point3D


def structure_building(low_speed_um, accel_x_um, high_speed_um, accel_a_um) -> list[tuple[str, str, DrawableObject]]:
    structures = []

    parameter_1 = ("parameter_V_2000", "ABZ",
                       Stair(
                           Point3D(0, 0, -2),
                           n_steps=6,
                           step_height=0.6,
                           step_length=20,
                           step_width=50,
                           hatch_size=0.125,
                           slice_size=0.3,
                           socket_height=7,
                           velocity=2000,
                           acceleration=accel_a_um,
                       ))
    parameter_2 = ("parameter_V_1000", "ABZ",
                   Stair(
                       Point3D(0, 0, -2),
                       n_steps=6,
                       step_height=0.6,
                       step_length=20,
                       step_width=50,
                       hatch_size=0.125,
                       slice_size=0.3,
                       socket_height=7,
                       velocity=1000,
                       acceleration=accel_a_um,
                   ))
    parameter_3 = ("parameter_v_600", "XYZ",
                   Stair(
                       Point3D(0, 0, -2),
                       n_steps=6,
                       step_height=0.6,
                       step_length=20,
                       step_width=50,
                       hatch_size=0.125,
                       slice_size=0.3,
                       socket_height=7,
                       velocity=600,
                       acceleration=accel_x_um,
                   ))
    parameter_4 = ("parameter_v_300", "XYZ",
                   Stair(
                       Point3D(0, 0, -2),
                       n_steps=6,
                       step_height=0.6,
                       step_length=20,
                       step_width=50,
                       hatch_size=0.125,
                       slice_size=0.3,
                       socket_height=7,
                       velocity=300,
                       acceleration=accel_x_um,
                   ))
    parameter_5 = ("parameter_power_5_a", "ABZ",
                   Stair(
                       Point3D(0, 0, -2),
                       n_steps=6,
                       step_height=0.6,
                       step_length=20,
                       step_width=50,
                       hatch_size=0.125,
                       slice_size=0.3,
                       socket_height=7,
                       velocity=2000,
                       acceleration=accel_a_um,
                   ))
    parameter_6 = ("parameter_power_3_a", "ABZ",
                   Stair(
                       Point3D(0, 0, -2),
                       n_steps=6,
                       step_height=0.6,
                       step_length=20,
                       step_width=50,
                       hatch_size=0.125,
                       slice_size=0.3,
                       socket_height=7,
                       velocity=2000,
                       acceleration=accel_a_um,
                   ))
    parameter_7 = ("parameter_power_5_x", "XYZ",
                   Stair(
                       Point3D(0, 0, -2),
                       n_steps=6,
                       step_height=0.6,
                       step_length=20,
                       step_width=50,
                       hatch_size=0.125,
                       slice_size=0.3,
                       socket_height=7,
                       velocity=300,
                       acceleration=accel_x_um,
                   ))
    parameter_8 = ("parameter_power_3_x", "XYZ",
                   Stair(
                       Point3D(0, 0, -2),
                       n_steps=6,
                       step_height=0.6,
                       step_length=20,
                       step_width=50,
                       hatch_size=0.125,
                       slice_size=0.3,
                       socket_height=7,
                       velocity=300,
                       acceleration=accel_x_um,
                   ))

    structures.append(parameter_1)
    structures.append(parameter_1)
    structures.append(parameter_1)

    structures.append(parameter_2)
    structures.append(parameter_2)
    structures.append(parameter_2)

    structures.append(parameter_3)
    structures.append(parameter_3)
    structures.append(parameter_3)

    structures.append(parameter_4)
    structures.append(parameter_4)
    structures.append(parameter_4)

    structures.append(parameter_5)
    structures.append(parameter_5)
    structures.append(parameter_5)

    structures.append(parameter_6)
    structures.append(parameter_6)
    structures.append(parameter_6)

    structures.append(parameter_7)
    structures.append(parameter_7)
    structures.append(parameter_7)

    structures.append(parameter_8)
    structures.append(parameter_8)
    structures.append(parameter_8)

    return structures

