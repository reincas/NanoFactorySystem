import matplotlib.pyplot as plt

from nanofactorysystem.aerobasic.programs import AeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.circle import FilledCircle2D, Spiral2D, LineCircle2D, Circle2D
from nanofactorysystem.aerobasic.programs.drawings.lens import SphericalLens
from nanofactorysystem.aerobasic.programs.drawings.lines import Rectangle3D
# from nanofactorysystem.aerobasic.programs.drawings.qr_code import QRCode
from nanofactorysystem.aerobasic.programs.setups import DefaultSetup
from nanofactorysystem.aerobasic.utils.visualization import read_text, plot_movements
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, DropDirection, Unit, Point3D

program = AeroBasicProgram()
program(DefaultSetup())
program.send("$AO[0].A=3.0")
coordinate_system = CoordinateSystem(
    offset_x=17.50,
    offset_y=21.000,
    z_function=25.214,
    drop_direction=DropDirection.UP,
    unit=Unit.mm
)

circle = Circle2D(
    center=Point3D(0, 0, 0),
    radius=0.1,
    # radius_start=0.4,
    # radius_end=0.0,
    velocity=0.02,
    # acceleration=0.002,
    # hatch_size=0.01,
)

lens = SphericalLens(
    Point3D(0, 0, 0),
    max_height=0.05,
    radius_of_curvature=1.03,
    layer_height=0.0002,
    # circle_object_factory=FilledCircle2D.as_circle_factory(2.5),
    # circle_object_factory=Spiral2D.as_circle_factory(2.5),
    circle_object_factory=LineCircle2D.as_circle_factory(0.2, 0.2),
    hatch_size=0.006,
    velocity=200,
)

rect = Rectangle3D(
    Point3D(0,0,0),
    0.05,
    0.1,
    structure_height=0.003,
    layer_height=0.00005,
    hatch_size=0.01)

print(rect.to_json())
print(lens.to_json())

circle

# qr_code = QRCode(Point3D(0, 0, -0.002), "Hallo QR-Codes", 0.1, 0.1)
# program(circle.draw_on(coordinate_system))
# program(lens.draw_on(coordinate_system))
program(rect.draw_on(coordinate_system))
movements = read_text(program.to_text())
fig = plot_movements(movements)
fig.tight_layout()
program.write("plot_drawings.txt")
plt.show()
print(program.to_text())
