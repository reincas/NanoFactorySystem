"""
Beispiel-Implementierung mit der verbesserten Struktur
Zeigt, wie die neuen Config-Klassen mit den bestehenden DrawableObjects verwendet werden
"""

from typing import Iterator, List
import numpy as np

# Imports aus deinem System
from nanofactorysystem.aerobasic.programs.drawings import DrawableObject, DrawableAeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.circle import Circle2D, FilledCircle2D
from nanofactorysystem.aerobasic.programs.drawings.lines import Rectangle3D, XLines, YLines
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point2D, Point3D

# Neue Config imports
from drawing_config import DrawingConfig, ConfigPresets, ProcessType, PathOptimizer, LayerOptimizer


class ImprovedRectangle3D(DrawableObject):
    """
    Verbesserte Rectangle3D Implementation mit Config-Pattern
    """

    def __init__(
            self,
            center: Point3D,
            width: float,  # Y-Richtung
            length: float,  # X-Richtung
            height: float,  # Z-Richtung
            config: DrawingConfig
    ):
        super().__init__()
        self.center = center
        self.width = width
        self.length = length
        self.height = height
        self.config = config

        # Optimiere Layer-Parameter
        self.n_layers, self.optimized_slice_size = LayerOptimizer.calculate_optimal_layers(
            height, config.slice_size
        )

    @property
    def center_point(self) -> Point2D:
        return Point2D(self.center.X, self.center.Y)

    @property
    def volume(self) -> float:
        return self.width * self.length * self.height

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        for layer_idx in range(self.n_layers):
            z_position = self.center.Z + layer_idx * self.optimized_slice_size

            # Wechsle Hatching-Richtung pro Layer
            use_x_direction = (layer_idx % 2 == 0)

            yield self._generate_layer(
                coordinate_system,
                z_position,
                use_x_direction
            )

    def _generate_layer(
            self,
            coordinate_system: CoordinateSystem,
            z_position: float,
            use_x_direction: bool
    ) -> DrawableAeroBasicProgram:
        """Generiere einen einzelnen Layer"""
        program = DrawableAeroBasicProgram(coordinate_system)

        if use_x_direction:
            # Hatching in X-Richtung
            n_lines, optimized_hatch = LayerOptimizer.calculate_optimal_hatching(
                self.width, self.config.hatch_size
            )

            order = 1
            for i in range(n_lines):
                y_pos = self.center.Y - self.width / 2 + i * optimized_hatch
                lines = [
                    (self.center.X - self.length / 2, self.center.X + self.length / 2)[::order]
                ]

                x_line = XLines(
                    y=y_pos,
                    z=z_position,
                    lines=lines,
                    velocity=self.config.velocity,
                    acceleration=self.config.acceleration
                )
                program.add_programm(x_line.draw_on(coordinate_system))
                order *= -1
        else:
            # Hatching in Y-Richtung
            n_lines, optimized_hatch = LayerOptimizer.calculate_optimal_hatching(
                self.length, self.config.hatch_size
            )

            order = 1
            for i in range(n_lines):
                x_pos = self.center.X - self.length / 2 + i * optimized_hatch
                lines = [
                    (self.center.Y - self.width / 2, self.center.Y + self.width / 2)[::order]
                ]

                y_line = YLines(
                    x=x_pos,
                    z=z_position,
                    lines=lines,
                    velocity=self.config.velocity,
                    acceleration=self.config.acceleration
                )
                program.add_programm(y_line.draw_on(coordinate_system))
                order *= -1

        return program


class TestGrid(DrawableObject):
    """
    Erstelle ein Test-Grid aus mehreren Strukturen für Kalibrierung
    """

    def __init__(
            self,
            center: Point3D,
            rows: int,
            cols: int,
            structure_size: float,
            spacing: float,
            height: float,
            config: DrawingConfig
    ):
        super().__init__()
        self.center = center
        self.rows = rows
        self.cols = cols
        self.structure_size = structure_size
        self.spacing = spacing
        self.height = height
        self.config = config

        # Erstelle Grid-Positionen
        self.positions = self._calculate_grid_positions()

    @property
    def center_point(self) -> Point2D:
        return Point2D(self.center.X, self.center.Y)

    def _calculate_grid_positions(self) -> List[Point3D]:
        """Berechne alle Positionen im Grid"""
        positions = []

        for i in range(self.rows):
            for j in range(self.cols):
                x = self.center.X + (j - (self.cols - 1) / 2) * self.spacing
                y = self.center.Y + (i - (self.rows - 1) / 2) * self.spacing
                positions.append(Point3D(x, y, self.center.Z))

        # Optimiere Reihenfolge für minimale Bewegungen
        return PathOptimizer.optimize_point_order(positions)

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        """Generiere alle Strukturen im Grid"""

        for position in self.positions:
            # Erstelle Rectangle an dieser Position
            rect = ImprovedRectangle3D(
                center=position,
                width=self.structure_size,
                length=self.structure_size,
                height=self.height,
                config=self.config
            )

            # Generiere alle Layer für diese Struktur
            yield from rect.iterate_layers(coordinate_system)


class MultiMaterialStructure(DrawableObject):
    """
    Struktur mit verschiedenen Bereichen, die unterschiedliche Configs verwenden
    """

    def __init__(
            self,
            center: Point3D,
            core_radius: float,
            shell_thickness: float,
            height: float,
            core_config: DrawingConfig,
            shell_config: DrawingConfig
    ):
        super().__init__()
        self.center = center
        self.core_radius = core_radius
        self.shell_thickness = shell_thickness
        self.height = height
        self.core_config = core_config
        self.shell_config = shell_config

        # Berechne Layer-Parameter für beide Bereiche
        self.n_layers = max(
            LayerOptimizer.calculate_optimal_layers(height, core_config.slice_size)[0],
            LayerOptimizer.calculate_optimal_layers(height, shell_config.slice_size)[0]
        )
        self.layer_height = height / self.n_layers

    @property
    def center_point(self) -> Point2D:
        return Point2D(self.center.X, self.center.Y)

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        for layer_idx in range(self.n_layers):
            z = self.center.Z + layer_idx * self.layer_height

            program = DrawableAeroBasicProgram(coordinate_system)

            # Core (innerer Bereich)
            core_circle = FilledCircle2D(
                center=Point3D(self.center.X, self.center.Y, z),
                radius_start=0,
                radius_end=self.core_radius,
                hatch_size=self.core_config.hatch_size,
                velocity=self.core_config.velocity
            )
            program.add_programm(core_circle.draw_on(coordinate_system))

            # Shell (äußerer Bereich)
            shell_circle = FilledCircle2D(
                center=Point3D(self.center.X, self.center.Y, z),
                radius_start=self.core_radius,
                radius_end=self.core_radius + self.shell_thickness,
                hatch_size=self.shell_config.hatch_size,
                velocity=self.shell_config.velocity
            )
            program.add_programm(shell_circle.draw_on(coordinate_system))

            yield program


def example_usage():
    """
    Beispiel-Verwendung der neuen Strukturen
    """

    # 1. Erstelle Koordinatensystem
    coord_system = CoordinateSystem()

    # 2. Lade oder erstelle Configs
    standard_config = ConfigPresets.get_preset(ProcessType.STANDARD)
    high_res_config = ConfigPresets.get_preset(ProcessType.HIGH_RESOLUTION)

    # 3. Erstelle einfache Struktur
    print("Erstelle einfaches Rechteck...")
    simple_rect = ImprovedRectangle3D(
        center=Point3D(0, 0, 0),
        width=100.0,  # 100 μm
        length=100.0,  # 100 μm
        height=50.0,  # 50 μm
        config=standard_config
    )

    # Generiere Program
    simple_program = simple_rect.draw_on(coord_system)
    simple_program.write("simple_rectangle.pgm")

    # 4. Erstelle Test-Grid für Kalibrierung
    print("Erstelle Test-Grid...")
    test_grid = TestGrid(
        center=Point3D(0, 0, 0),
        rows=3,
        cols=3,
        structure_size=20.0,  # 20 μm große Strukturen
        spacing=50.0,  # 50 μm Abstand
        height=10.0,  # 10 μm hoch
        config=standard_config
    )

    grid_program = test_grid.draw_on(coord_system)
    grid_program.write("test_grid.pgm")

    # 5. Erstelle Multi-Material Struktur
    print("Erstelle Multi-Material Struktur...")
    multi_material = MultiMaterialStructure(
        center=Point3D(0, 0, 0),
        core_radius=50.0,  # 50 μm Kern
        shell_thickness=25.0,  # 25 μm Schale
        height=30.0,  # 30 μm hoch
        core_config=high_res_config,  # Hohe Auflösung im Kern
        shell_config=standard_config  # Standard in der Schale
    )

    multi_program = multi_material.draw_on(coord_system)
    multi_program.write("multi_material.pgm")

    # 6. Berechne und zeige Statistiken
    print("\n=== Statistiken ===")
    print(f"Simple Rectangle:")
    print(f"  - Volumen: {simple_rect.volume:.2f} μm³")
    print(f"  - Anzahl Layer: {simple_rect.n_layers}")
    print(f"  - Optimierte Slice-Size: {simple_rect.optimized_slice_size:.3f} μm")

    print(f"\nTest Grid:")
    print(f"  - Anzahl Strukturen: {test_grid.rows * test_grid.cols}")
    print(f"  - Gesamt-Fläche: {(test_grid.rows * test_grid.spacing) * (test_grid.cols * test_grid.spacing):.2f} μm²")

    # 7. Speichere Configs für spätere Verwendung
    standard_config.save("configs/standard.json")
    high_res_config.save("configs/high_resolution.json")

    print("\n✅ Programme erfolgreich generiert!")
    print("  - simple_rectangle.pgm")
    print("  - test_grid.pgm")
    print("  - multi_material.pgm")


if __name__ == "__main__":
    example_usage()