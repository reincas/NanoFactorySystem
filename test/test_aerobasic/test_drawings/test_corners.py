from nanofactorysystem.aerobasic import VelocityMode
from nanofactorysystem.aerobasic.programs.drawings.lines import CornerRectangle, Corner
from nanofactorysystem.aerobasic.programs.setups import DefaultSetup
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, DropDirection, Unit, Point3D
from ..test_program import AeroBasicProgramTest


class TestCorners(AeroBasicProgramTest):
    def test_top_left_corner(self):
        self.program(DefaultSetup())
        self.program.send("$AO[0].A=3.0")
        coordinate_system = CoordinateSystem(
            offset_x=1750,
            offset_y=21000,
            z_function=25214,
            drop_direction=DropDirection.UP,
            unit=Unit.um
        )

        corner = Corner(
            Point3D(0, 0, -2),
            length=300,
            width=20,
            height=7,
            hatch_size=0.5,
            layer_height=0.75,
            F=2000
        )
        self.program(corner.draw_on(coordinate_system))

    def test_diagonal_corner(self):
        self.program(DefaultSetup())
        self.program.send("$AO[0].A=3.0")
        coordinate_system = CoordinateSystem(
            offset_x=1750,
            offset_y=21000,
            z_function=25214,
            drop_direction=DropDirection.UP,
            unit=Unit.um
        )

        corner = Corner(
            Point3D(0, 0, -2),
            length=300,
            width=20,
            height=7,
            hatch_size=0.5,
            layer_height=0.75,
            rotation_degree=45,
            F=2000
        )
        self.program(corner.draw_on(coordinate_system))

    def test_all_markers(self):
        # Setup
        self.program(DefaultSetup(velocity_mode=VelocityMode.ON))
        self.program.send("$AO[0].A=3.0")

        coordinate_system = CoordinateSystem(
            offset_x=1750,
            offset_y=21000,
            z_function=25214,
            drop_direction=DropDirection.UP,
            unit=Unit.um
        )

        markers = CornerRectangle(
            Point3D(0, 0, -2),
            rectangle_width=1000,
            rectangle_height=1000,
            corner_length=300,
            corner_width=20,
            height=7,
            hatch_size=0.5,
            layer_height=0.75,
            F=2000
        )
        self.program(markers.draw_on(coordinate_system))

    def test_all_markers_optimized(self):
        self.test_all_markers()
        self.program = self.program.optimize(remove_comments=True, remove_whitespace=True)
