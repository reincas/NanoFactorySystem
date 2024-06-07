import matplotlib.pyplot as plt

from nanofactorysystem.aerobasic.programs import AeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.circle import Spiral2D
from nanofactorysystem.aerobasic.programs.drawings.qr_code import QRCode
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

# circle = Spiral2D(
#     center=Point3D(0, 0, 0),
#     radius_start=0.4,
#     radius_end=0.2,
#     velocity=0.02,
#     # acceleration=0.002,
#     hatch_size=0.01,
# )
qr_code = QRCode(Point3D(0, 0, -0.002), "Hallo QR-Codes", 0.1, 0.1)
program(qr_code.draw_on(coordinate_system))
movements = read_text(program.to_text())
fig = plot_movements(movements)
fig.tight_layout()
print(program.to_text())
plt.show()
