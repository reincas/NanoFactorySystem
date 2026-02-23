


class LargeStructureStitcher:
    """
    Manager für Strukturen größer als FOV
    """

    def __init__(
            self,
            fov_size: tuple[float, float],  # (width, height) in μm
            overlap: float = 0.1,  # 10% Überlappung
            strategy: StitchingStrategy = StitchingStrategy.LAYER_FIRST
    ):
        self.fov_width, self.fov_height = fov_size
        self.overlap = overlap
        self.strategy = strategy

        # Effektive FOV-Größe (mit Überlappung)
        self.eff_width = self.fov_width * (1 - overlap)
        self.eff_height = self.fov_height * (1 - overlap)

    def generate_layer_first(structure, fov_regions):
        """
        Druckt Schicht für Schicht über alle FOVs

        Ablauf:
        Layer 1: FOV(0,0) → FOV(0,1) → FOV(1,0) → FOV(1,1)
        Layer 2: FOV(0,0) → FOV(0,1) → FOV(1,0) → FOV(1,1)
        ...
        """

        for layer_idx, layer in enumerate(structure.iterate_layers()):
            for fov in fov_regions:
                # Bewege Stage zu FOV
                program.MOVEABS(X=fov.center_x, Y=fov.center_y)
                program.DWELL(0.5)  # Settling time

                # Drucke Layer-Teil in diesem FOV
                clipped = clip_to_fov(layer, fov.bounds)
                program.add_programm(clipped)


    def generate_region_first(structure, fov_regions):
        """
        Druckt komplett in einem FOV bevor zum nächsten gewechselt wird

        Ablauf:
        FOV(0,0): Layer 1 → Layer 2 → ... → Layer N
        FOV(0,1): Layer 1 → Layer 2 → ... → Layer N
        ...
        """

        for fov in fov_regions:
            # Bewege zu FOV
            program.MOVEABS(X=fov.center_x, Y=fov.center_y)
            program.DWELL(0.5)

            # Drucke alle Layer in diesem FOV
            for layer in structure.iterate_layers():
                clipped = clip_to_fov(layer, fov.bounds)
                program.add_programm(clipped)


    def calculate_fov_grid(structure_size, fov_size, overlap=0.1):
        """
        Berechnet optimales FOV-Grid

        Beispiel:
        - Struktur: 300x300 μm
        - FOV: 100x100 μm
        - Overlap: 10%
        → Effektives FOV: 90x90 μm
        → Benötigt: 4x4 Grid (mit Überlappung)
        """

        width, height = structure_size
        fov_w, fov_h = fov_size

        # Effektive Größe
        eff_w = fov_w * (1 - overlap)
        eff_h = fov_h * (1 - overlap)

        # Anzahl FOVs
        n_x = math.ceil(width / eff_w)
        n_y = math.ceil(height / eff_h)

        # Generiere Positionen
        positions = []
        for j in range(n_y):
            for i in range(n_x):
                center_x = (i + 0.5) * eff_w
                center_y = (j + 0.5) * eff_h
                positions.append((center_x, center_y))

        return positions


# Große Linsen-Array (300x300 μm)
class LargeLensArray:
    def __init__(self):
        self.total_size = (300, 300)  # μm
        self.fov_size = (100, 100)  # μm
        self.stitcher = LargeStructureStitcher(
            fov_size=self.fov_size,
            overlap=0.1,
            strategy=StitchingStrategy.LAYER_FIRST
        )

    def generate_program(self):
        # Berechne FOV-Grid
        fov_grid = self.stitcher.calculate_fov_grid(
            self.total_size
        )
        # Grid wird 4x4 FOVs haben

        # Generiere Programm mit Stitching
        return self.stitcher.generate_stitched_program(
            structure=self,
            fov_regions=fov_grid
        )