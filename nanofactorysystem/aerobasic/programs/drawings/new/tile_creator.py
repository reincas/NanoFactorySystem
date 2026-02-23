import numpy as np
from typing import List, Tuple


class TileCalculator:
    """
    Parameters:
        fov_size: Physikalische FOV-Größe (width, height) in µm
        usable_fov_fraction: Fraktion der FOV die gedruckt wird (z.B. 0.85 = 85%)
                            Die verbleibenden 15% dienen als Rand UND overlap

    Example:
        FOV = 100 µm, usable = 0.85
        → Pro Tile werden 85 µm gedruckt
        → Nächstes FOV startet bei 85 µm
        → FOVs überlappen um 15 µm
    """

    def __init__(
            self,
            fov_size: Tuple[float, float],
            usable_fov_fraction: float = 0.85  # 85% nutzen, 15% = Rand/Overlap
    ):
        self.fov_width = float(fov_size[0])
        self.fov_height = float(fov_size[1])
        self.usable_fraction = usable_fov_fraction

        # Druckbereich pro Tile = Tile-Stepping
        self.tile_width = self.fov_width * usable_fov_fraction
        self.tile_height = self.fov_height * usable_fov_fraction

        # Overlap ergibt sich aus dem Rand
        self.overlap_width = self.fov_width * (1 - usable_fov_fraction)
        self.overlap_height = self.fov_height * (1 - usable_fov_fraction)

    def get_tile_boundaries(
            self,
            structure_bounds: Tuple[float, float, float, float]
    ) -> List[Tuple[float, float, float, float]]:
        """
        Berechnet die Boundaries für alle benötigten Tiles.

        Args:
            structure_bounds: (x_min, x_max, y_min, y_max) der gesamten Struktur

        Returns:
            List von (x_start, x_end, y_start, y_end) für jeden Tile
        """
        x_min, x_max, y_min, y_max = structure_bounds
        width = x_max - x_min
        height = y_max - y_min

        # Prüfen ob Tiling notwendig
        if width <= self.tile_width and height <= self.tile_height:
            # Struktur passt in ein FOV
            return [(x_min, x_max, y_min, y_max)]

        # Anzahl benötigter Tiles berechnen
        num_tiles_x = int(np.ceil(width / self.tile_width))
        num_tiles_y = int(np.ceil(height / self.tile_height))

        tiles = []

        for row in range(num_tiles_y):
            for col in range(num_tiles_x):
                # Tile boundaries berechnen
                # Tiles starten bei Vielfachen von tile_width/height
                tile_x_start = x_min + col * self.tile_width
                tile_x_end = tile_x_start + self.tile_width
                tile_y_start = y_min + row * self.tile_height
                tile_y_end = tile_y_start + self.tile_height

                # An Strukturgrenzen clippen
                tile_x_end = min(tile_x_end, x_max)
                tile_y_end = min(tile_y_end, y_max)

                tiles.append((tile_x_start, tile_x_end, tile_y_start, tile_y_end))

        return tiles

    def get_fov_positions(
            self,
            structure_bounds: Tuple[float, float, float, float]
    ) -> List[Tuple[float, float]]:
        """
        Berechnet die FOV-Zentren für das Mikroskop-Positionierungssystem.

        Returns:
            List von (fov_center_x, fov_center_y) Positionen
        """
        tiles = self.get_tile_boundaries(structure_bounds)
        fov_positions = []

        for x_start, x_end, y_start, y_end in tiles:
            # FOV-Zentrum berechnen
            # (Tile ist zentriert im FOV)
            tile_center_x = (x_start + x_end) / 2
            tile_center_y = (y_start + y_end) / 2

            fov_positions.append((tile_center_x, tile_center_y))

        return fov_positions


# ============================================================================
# DEIN WORKFLOW - Beispiel Implementation
# ============================================================================

def process_structure_with_tiles(structure, fov_size, slicing_distance):
    """
    Beispiel wie du deinen Workflow implementieren kannst.
    """
    # 1. Tile Calculator initialisieren
    tile_calc = TileCalculator(
        fov_size=fov_size,
        usable_fov_fraction=0.85  # 85% nutzen, 15% Rand/Overlap
    )

    # 2. Structure bounds holen
    structure_bounds = structure.bounding_box  # (x_min, x_max, y_min, y_max)

    # 3. Tiles berechnen
    tiles_array = tile_calc.get_tile_boundaries(structure_bounds)

    print(f"Anzahl Tiles: {len(tiles_array)}")

    # 4. Z-heights für slicing berechnen
    z_start = -2.0  # Sicherheitsabstand für Verbindung
    z_end = structure.max_height
    slicing_opt = int(np.round((z_end - z_start) / slicing_distance))
    z_heights = np.linspace(z_start, z_end, slicing_opt)

    print(f"Z-layers: {len(z_heights)}")

    # 5. Über alle Tiles iterieren (TILE_FIRST Strategy)
    all_programs = []

    for tile_idx, (x_start, x_end, y_start, y_end) in enumerate(tiles_array):
        print(f"\nProcessing Tile {tile_idx + 1}/{len(tiles_array)}")
        print(f"  Boundaries: x=[{x_start:.1f}, {x_end:.1f}], y=[{y_start:.1f}, {y_end:.1f}]")

        tile_programs = []

        # 6. Über alle Z-heights für diesen Tile
        for z_height in z_heights:
            # Hier kommt deine Struktur-Scan-Logik
            points = scan_structure_at_height(
                structure,
                z_height,
                tile_bounds=(x_start, x_end, y_start, y_end)
            )

            if len(points) > 0:
                # Program für diesen Layer erstellen
                program = create_polyline_program(points, z_height)
                tile_programs.append(program)

        # Alle Programme für diesen Tile speichern
        all_programs.append({
            'tile_id': tile_idx,
            'bounds': (x_start, x_end, y_start, y_end),
            'programs': tile_programs
        })

    return all_programs


def scan_structure_at_height(structure, z_height, tile_bounds):
    """
    Placeholder für deine Scan-Logik.
    """
    x_start, x_end, y_start, y_end = tile_bounds

    # TODO: Deine Implementierung
    points = []
    return points


def create_polyline_program(points, z_height):
    """
    Placeholder für Program-Erstellung
    """
    pass


# ============================================================================
# EINFACHES BEISPIEL
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Tile Boundary Calculator - CLEAN Version")
    print("=" * 60)

    # FOV definieren
    fov_size = (100, 100)  # 100x100 µm

    # Calculator erstellen
    calc = TileCalculator(
        fov_size=fov_size,
        usable_fov_fraction=0.85  # 85% nutzen, 15% = Rand UND Overlap
    )

    print(f"\nFOV: {fov_size[0]}x{fov_size[1]} µm")
    print(f"Druckbereich pro Tile: {calc.tile_width:.1f}x{calc.tile_height:.1f} µm")
    print(f"Overlap zwischen FOVs: {calc.overlap_width:.1f}x{calc.overlap_height:.1f} µm")
    print(f"Rand pro Seite: {calc.overlap_width / 2:.1f} µm")

    # Beispiel 1: Kleine Struktur (passt in FOV)
    print("\n" + "-" * 60)
    print("Beispiel 1: Kleine Struktur (50x50 µm)")
    small_bounds = (-25, 25, -25, 25)
    tiles = calc.get_tile_boundaries(small_bounds)
    print(f"Anzahl Tiles: {len(tiles)}")
    for i, tile in enumerate(tiles):
        print(f"  Tile {i}: x=[{tile[0]:.1f}, {tile[1]:.1f}], y=[{tile[2]:.1f}, {tile[3]:.1f}]")

    # Beispiel 2: Große Struktur (braucht Tiling)
    print("\n" + "-" * 60)
    print("Beispiel 2: Große Struktur (250x250 µm)")
    large_bounds = (-125, 125, -125, 125)
    tiles = calc.get_tile_boundaries(large_bounds)
    print(f"Anzahl Tiles: {len(tiles)}")

    # Visualisierung
    num_x = int(np.ceil((large_bounds[1] - large_bounds[0]) / calc.tile_width))
    num_y = int(np.ceil((large_bounds[3] - large_bounds[2]) / calc.tile_height))
    print(f"\nGrid: {num_x}x{num_y} tiles")

    for i, tile in enumerate(tiles):
        row = i // num_x
        col = i % num_x
        print(f"  [{row},{col}] Tile {i}: x=[{tile[0]:.1f}, {tile[1]:.1f}], y=[{tile[2]:.1f}, {tile[3]:.1f}]")

    # FOV Positionen für Mikroskop
    print("\n" + "-" * 60)
    print("FOV Positionen für Mikroskop-Positionierungssystem:")
    fov_positions = calc.get_fov_positions(large_bounds)
    for i, (x, y) in enumerate(fov_positions):
        print(f"  Tile {i}: FOV Center = ({x:.1f}, {y:.1f})")

    print("\n" + "=" * 60)