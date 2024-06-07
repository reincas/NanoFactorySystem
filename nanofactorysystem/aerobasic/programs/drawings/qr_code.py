import qrcode

from nanofactorysystem.aerobasic.programs.drawings import DrawableObject, DrawableAeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.lines import VerticalLine
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point2D, Point3D


class QRCode(DrawableObject):
    def __init__(self, center: Point3D, text: str, width: float, height: float):
        super().__init__()
        self.center = center
        self.text = str(text)
        self.width = width
        self.height = height

    @property
    def center_point(self) -> Point2D:
        return self.center

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)
        qr = qrcode.make(self.text, border=0, box_size=1)
        modules = qr.modules
        pixel_size = self.width / len(modules)

        z1 = self.center.Z
        z2 = self.center.Z + self.height
        for i in range(len(modules)):
            for j in range(len(modules)):
                if modules[i][j]:
                    v_line = VerticalLine(
                        Point2D(i * pixel_size + pixel_size / 2, j * pixel_size + pixel_size / 2),
                        z_min=z1,
                        z_max=z2
                    )
                    program.add_programm(v_line.draw_on(coordinate_system))
                    z1, z2 = z2, z1

        return program


if __name__ == '__main__':
    qr = QRCode(Point2D(0, 0), "Hello world")
    print(qr.draw_on(CoordinateSystem()))
