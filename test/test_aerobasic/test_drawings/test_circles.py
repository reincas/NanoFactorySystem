from nanofactorysystem.aerobasic.programs.drawings.circle import Circle2D, FilledCircle2D, LineCircle2D
from nanofactorysystem.aerobasic.programs.setups import DefaultSetup
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, DropDirection, Unit, Point3D
from ..test_program import AeroBasicProgramTest


class TestCircles(AeroBasicProgramTest):
    def test_single_circle(self):
        self.program(DefaultSetup())
        self.program.send("$AO[0].A=3.0")
        coordinate_system = CoordinateSystem(
            offset_x=17.50,
            offset_y=21.000,
            z_function=25.214,
            drop_direction=DropDirection.UP,
            unit=Unit.mm
        )

        corner = Circle2D(
            center=Point3D(0, 0, 0),
            radius=0.2,
        )
        self.program(corner.draw_on(coordinate_system))

    def test_filled_circle(self):
        self.program(DefaultSetup())
        self.program.send("$AO[0].A=3.0")
        coordinate_system = CoordinateSystem(
            offset_x=17.50,
            offset_y=21.000,
            z_function=25.214,
            drop_direction=DropDirection.UP,
            unit=Unit.mm
        )

        corner = FilledCircle2D(
            center=Point3D(0, 0, 0),
            radius_start=0.2,
            radius_end=0.0,
            hatch_size=0.02,
        )
        self.program(corner.draw_on(coordinate_system))

    def test_filled_circle_big(self):
        self.program(DefaultSetup())
        self.program.send("$AO[0].A=3.0")
        coordinate_system = CoordinateSystem(
            offset_x=17.50,
            offset_y=21.000,
            z_function=25.214,
            drop_direction=DropDirection.UP,
            unit=Unit.mm
        )

        corner = FilledCircle2D(
            center=Point3D(0, 0, 0),
            radius_start=0.4,
            radius_end=0.0,
            hatch_size=0.01,
        )
        self.program(corner.draw_on(coordinate_system))

    def test_filled_ring(self):
        self.program(DefaultSetup())
        self.program.send("$AO[0].A=3.0")
        coordinate_system = CoordinateSystem(
            offset_x=17.50,
            offset_y=21.000,
            z_function=25.214,
            drop_direction=DropDirection.UP,
            unit=Unit.mm
        )

        corner = FilledCircle2D(
            center=Point3D(0, 0, 0),
            radius_start=0.4,
            radius_end=0.2,
            hatch_size=0.01,
        )
        self.program(corner.draw_on(coordinate_system))

    def test_filled_line_circle(self):
        self.program(DefaultSetup())
        self.program.send("$AO[0].A=3.0")
        coordinate_system = CoordinateSystem(
            offset_x=17.50,
            offset_y=21.000,
            z_function=25.214,
            drop_direction=DropDirection.UP,
            unit=Unit.mm
        )

        circle = LineCircle2D(
            center=Point3D(0, 0, 0),
            radius_start=0.4,
            radius_end=0,
            hatch_size=0.01,
            velocity=0.02,
            acceleration=0.002
        )
        self.program(circle.draw_on(coordinate_system))

    def test_filled_line_ring(self):
        self.program(DefaultSetup())
        self.program.send("$AO[0].A=3.0")
        coordinate_system = CoordinateSystem(
            offset_x=17.50,
            offset_y=21.000,
            z_function=25.214,
            drop_direction=DropDirection.UP,
            unit=Unit.mm
        )

        circle = LineCircle2D(
            center=Point3D(0, 0, 0),
            radius_start=0.4,
            radius_end=0.2,
            velocity=0.02,
            acceleration=0.002,
            hatch_size=0.01,
        )
        self.program(circle.draw_on(coordinate_system))
