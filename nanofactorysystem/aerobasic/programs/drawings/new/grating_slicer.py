"""
=============================================================================
GRATING SLICER - Workflow für 2PP-Strukturerzeugung aus analytischen Funktionen
=============================================================================

Workflow:
    1. Definiere Höhenfunktion z(x,y)
    2. Definiere Struktur-Parameter (Periode, Höhe, etc.)
    3. Definiere Slicing-Parameter (z_min, z_max, dz)
    4. Definiere Hatching-Parameter (Winkel, Abstand)
    5. Optional: Begrenzung (Apertur)

Output:
    Liste von Segmenten [(x1,y1,z), (x2,y2,z), ...] für jede Schicht

Autor: Für Hannes' DOE/2PP-Anwendungen
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Callable, List, Tuple, Optional, Dict, Any
from skimage.measure import label, regionprops, find_contours
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


# =============================================================================
# DATENSTRUKTUREN
# =============================================================================

@dataclass
class StructureParams:
    """Parameter für die Struktur"""
    x_range: Tuple[float, float] = (-5, 5)
    y_range: Tuple[float, float] = (-5, 5)
    resolution: int = 500  # Pixel pro Achse


@dataclass
class SlicingParams:
    """Parameter für das Slicing"""
    z_min: float = 0.0
    z_max: float = 1.0
    num_slices: Optional[int] = None  # Anzahl Schichten
    dz: Optional[float] = None  # ODER: Schichtdicke

    def get_z_levels(self) -> np.ndarray:
        """Berechnet die Z-Levels für das Slicing"""
        if self.num_slices is not None:
            return np.linspace(self.z_min, self.z_max, self.num_slices)
        elif self.dz is not None:
            return np.arange(self.z_min, self.z_max + self.dz / 2, self.dz)
        else:
            raise ValueError("Entweder num_slices oder dz muss angegeben werden!")


@dataclass
class HatchingParams:
    """Parameter für das Hatching"""
    angle_deg: float = 0.0  # Winkel der Hatch-Linien
    distance: float = 0.5  # Abstand zwischen Linien
    alternating: bool = False  # Alternierende Winkel pro Schicht
    angle_increment: float = 90  # Winkel-Inkrement wenn alternating=True


@dataclass
class Segment:
    """Ein einzelnes Liniensegment"""
    start: Tuple[float, float, float]
    end: Tuple[float, float, float]

    def to_tuple(self):
        return (self.start, self.end)

    def length(self):
        return np.sqrt(sum((a - b) ** 2 for a, b in zip(self.start, self.end)))


@dataclass
class SliceResult:
    """Ergebnis einer einzelnen Schicht"""
    z_level: float
    polygons: List[np.ndarray]
    segments: List[Segment]


@dataclass
class SlicingResult:
    """Gesamtergebnis des Slicing-Prozesses"""
    slices: List[SliceResult]
    params: Dict[str, Any]

    def get_all_segments(self) -> List[Segment]:
        """Alle Segmente aller Schichten"""
        all_segs = []
        for s in self.slices:
            all_segs.extend(s.segments)
        return all_segs

    def get_segments_as_tuples(self) -> List[Tuple]:
        """Segmente als Liste von Tupeln"""
        return [seg.to_tuple() for seg in self.get_all_segments()]

    def total_segments(self) -> int:
        return sum(len(s.segments) for s in self.slices)

    def total_length(self) -> float:
        return sum(seg.length() for seg in self.get_all_segments())


# =============================================================================
# HÖHENFUNKTIONEN (Beispiele)
# =============================================================================

class HeightFunctions:
    """Sammlung von Standard-Höhenfunktionen für Gitter/DOEs"""

    @staticmethod
    def sinusoidal(period: float, height: float, angle_deg: float = 0,
                   z0: float = 0, phase: float = 0) -> Callable:
        """
        Sinusförmiges Gitter:
        z(x,y) = z0 + (h/2) * sin(2π/L * s(x,y) + φ)

        wobei s(x,y) = x*cos(θ) + y*sin(θ)
        """
        theta = np.deg2rad(angle_deg)

        def f(x, y):
            s = x * np.cos(theta) + y * np.sin(theta)
            return z0 + (height / 2) * np.sin(2 * np.pi / period * s + phase)

        return f

    @staticmethod
    def binary_grating(period: float, height: float, duty_cycle: float = 0.5,
                       angle_deg: float = 0, z0: float = 0) -> Callable:
        """
        Binäres Rechteckgitter:
        z = z0 + height wenn (s mod T)/T < duty_cycle, sonst z = z0
        """
        theta = np.deg2rad(angle_deg)

        def f(x, y):
            s = x * np.cos(theta) + y * np.sin(theta)
            frac = np.mod(s, period) / period
            return z0 + height * (frac < duty_cycle).astype(float)

        return f

    @staticmethod
    def blazed_grating(period: float, height: float, angle_deg: float = 0,
                       z0: float = 0) -> Callable:
        """
        Blazed (Sägezahn) Gitter:
        z(x,y) = z0 + height * (s mod T) / T
        """
        theta = np.deg2rad(angle_deg)

        def f(x, y):
            s = x * np.cos(theta) + y * np.sin(theta)
            return z0 + height * np.mod(s, period) / period

        return f

    @staticmethod
    def triangular_grating(period: float, height: float, angle_deg: float = 0,
                           z0: float = 0) -> Callable:
        """
        Dreieckiges Gitter (symmetrisch):
        """
        theta = np.deg2rad(angle_deg)

        def f(x, y):
            s = x * np.cos(theta) + y * np.sin(theta)
            frac = np.mod(s, period) / period
            # Dreiecksfunktion: 0->1->0 über eine Periode
            return z0 + height * (1 - 2 * np.abs(frac - 0.5))

        return f

    @staticmethod
    def gaussian_bumps(period: float, height: float, sigma: float,
                       angle_deg: float = 0, z0: float = 0) -> Callable:
        """
        Gaußsche Hügel in periodischer Anordnung
        """
        theta = np.deg2rad(angle_deg)

        def f(x, y):
            s = x * np.cos(theta) + y * np.sin(theta)
            # Position innerhalb der Periode
            s_mod = np.mod(s + period / 2, period) - period / 2
            return z0 + height * np.exp(-s_mod ** 2 / (2 * sigma ** 2))

        return f

    @staticmethod
    def crossed_gratings(period1: float, period2: float, height: float,
                         angle1_deg: float = 0, angle2_deg: float = 90,
                         z0: float = 0) -> Callable:
        """
        Gekreuzte Gitter (2D-Gitter)
        """
        theta1 = np.deg2rad(angle1_deg)
        theta2 = np.deg2rad(angle2_deg)

        def f(x, y):
            s1 = x * np.cos(theta1) + y * np.sin(theta1)
            s2 = x * np.cos(theta2) + y * np.sin(theta2)
            z1 = np.sin(2 * np.pi / period1 * s1)
            z2 = np.sin(2 * np.pi / period2 * s2)
            return z0 + (height / 2) * (z1 + z2) / 2

        return f

    @staticmethod
    def fresnel_lens(focal_length: float, wavelength: float, height: float,
                     cx: float = 0, cy: float = 0) -> Callable:
        """
        Fresnel-Linse (radiale Phase)
        """

        def f(x, y):
            r2 = (x - cx) ** 2 + (y - cy) ** 2
            phase = np.pi * r2 / (wavelength * focal_length)
            return height * np.mod(phase, 2 * np.pi) / (2 * np.pi)

        return f

    @staticmethod
    def custom(func: Callable) -> Callable:
        """Wrapper für benutzerdefinierte Funktionen"""
        return func


# =============================================================================
# BEGRENZUNGSFUNKTIONEN (Aperturen)
# =============================================================================

class Apertures:
    """Standard-Aperturen/Begrenzungen"""

    @staticmethod
    def circular(radius: float, cx: float = 0, cy: float = 0) -> Callable:
        def f(x, y):
            return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2

        return f

    @staticmethod
    def rectangular(width: float, height: float,
                    cx: float = 0, cy: float = 0) -> Callable:
        def f(x, y):
            return (np.abs(x - cx) <= width / 2) & (np.abs(y - cy) <= height / 2)

        return f

    @staticmethod
    def elliptical(a: float, b: float,
                   cx: float = 0, cy: float = 0) -> Callable:
        def f(x, y):
            return ((x - cx) / a) ** 2 + ((y - cy) / b) ** 2 <= 1

        return f

    @staticmethod
    def annular(r_inner: float, r_outer: float,
                cx: float = 0, cy: float = 0) -> Callable:
        def f(x, y):
            r2 = (x - cx) ** 2 + (y - cy) ** 2
            return (r2 >= r_inner ** 2) & (r2 <= r_outer ** 2)

        return f

    @staticmethod
    def none() -> Callable:
        """Keine Begrenzung"""

        def f(x, y):
            return np.ones_like(x, dtype=bool)

        return f


# =============================================================================
# KERN-ALGORITHMEN
# =============================================================================

def intersect_line_with_segment(p0: np.ndarray, d: np.ndarray,
                                a: np.ndarray, b: np.ndarray) -> Optional[float]:
    """Schnittpunkt Linie p0 + t*d mit Segment a→b"""
    v = b - a
    det = d[0] * (-v[1]) - d[1] * (-v[0])

    if abs(det) < 1e-12:
        return None

    rhs = a - p0
    t = (rhs[0] * (-v[1]) - rhs[1] * (-v[0])) / det
    s = (d[0] * rhs[1] - d[1] * rhs[0]) / det

    if 0 <= s <= 1:
        return t
    return None


def hatch_polygon(polygon: np.ndarray, angle_deg: float,
                  distance: float, z: float) -> List[Segment]:
    """Erzeugt Hatch-Segmente für ein geschlossenes Polygon"""
    poly = np.array(polygon)
    if len(poly) < 3:
        return []

    theta = np.deg2rad(angle_deg)
    d = np.array([np.cos(theta), np.sin(theta)])
    n = np.array([-d[1], d[0]])

    # Alle Punkte auf Normal projizieren
    projections = poly @ n
    proj_min = projections.min()
    proj_max = projections.max()

    offsets = np.arange(proj_min, proj_max + distance, distance)

    segments = []
    edges = [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]

    for off in offsets:
        p0 = n * off

        ts = []
        for a, b in edges:
            t = intersect_line_with_segment(p0, d, a, b)
            if t is not None:
                ts.append(t)

        if len(ts) < 2:
            continue

        ts.sort()

        # Duplikate entfernen
        filtered = [ts[0]]
        for t in ts[1:]:
            if abs(t - filtered[-1]) > 1e-9:
                filtered.append(t)
        ts = filtered

        for i in range(0, len(ts) - 1, 2):
            t0, t1 = ts[i], ts[i + 1]
            p_start = p0 + t0 * d
            p_end = p0 + t1 * d

            if np.linalg.norm(p_end - p_start) > 1e-9:
                segments.append(Segment(
                    start=(float(p_start[0]), float(p_start[1]), float(z)),
                    end=(float(p_end[0]), float(p_end[1]), float(z))
                ))

    return segments


def mask_to_polygons(mask: np.ndarray, xs: np.ndarray, ys: np.ndarray,
                     min_area: int = 10) -> List[np.ndarray]:
    """Konvertiert Binärmaske in geschlossene Polygone"""
    labels_img = label(mask.astype(np.uint8))
    regions = regionprops(labels_img)

    polygons = []
    for region in regions:
        if region.area < min_area:
            continue

        region_mask = (labels_img == region.label).astype(float)
        contours = find_contours(region_mask, 0.5)

        for contour in contours:
            poly = []
            for yi, xi in contour:
                x_coord = xs[0] + (xs[-1] - xs[0]) * xi / (len(xs) - 1)
                y_coord = ys[0] + (ys[-1] - ys[0]) * yi / (len(ys) - 1)
                poly.append([x_coord, y_coord])

            poly = np.array(poly)

            # Schließen
            if len(poly) > 2 and not np.allclose(poly[0], poly[-1]):
                poly = np.vstack([poly, poly[0]])

            if len(poly) >= 4:
                polygons.append(poly)

    return polygons


# =============================================================================
# HAUPTFUNKTION: SLICER
# =============================================================================

def slice_structure(
        height_func: Callable,
        structure_params: StructureParams,
        slicing_params: SlicingParams,
        hatching_params: HatchingParams,
        aperture: Optional[Callable] = None,
        verbose: bool = True
) -> SlicingResult:
    """
    Hauptfunktion: Sliced eine Höhenfunktion und erzeugt Hatch-Segmente

    Parameters:
    -----------
    height_func : Callable
        Höhenfunktion z(x, y)
    structure_params : StructureParams
        Struktur-Parameter (Bereich, Auflösung)
    slicing_params : SlicingParams
        Slicing-Parameter (z_min, z_max, Schichtdicke)
    hatching_params : HatchingParams
        Hatching-Parameter (Winkel, Abstand)
    aperture : Optional[Callable]
        Begrenzungsfunktion (default: keine)
    verbose : bool
        Debug-Ausgaben

    Returns:
    --------
    SlicingResult mit allen Schichten und Segmenten
    """

    # Grid erstellen
    xs = np.linspace(structure_params.x_range[0], structure_params.x_range[1],
                     structure_params.resolution)
    ys = np.linspace(structure_params.y_range[0], structure_params.y_range[1],
                     structure_params.resolution)
    X, Y = np.meshgrid(xs, ys)

    # Höhenfunktion evaluieren
    Z = height_func(X, Y)

    # Apertur anwenden
    if aperture is not None:
        aperture_mask = aperture(X, Y)
        Z = np.where(aperture_mask, Z, np.nan)

    # Z-Levels berechnen
    z_levels = slicing_params.get_z_levels()

    if verbose:
        print(f"Slicing von z={slicing_params.z_min:.3f} bis z={slicing_params.z_max:.3f}")
        print(f"Anzahl Schichten: {len(z_levels)}")
        print(f"Z-Bereich der Funktion: [{np.nanmin(Z):.3f}, {np.nanmax(Z):.3f}]")

    # Slicing durchführen
    slices = []

    for i, z_level in enumerate(z_levels):
        # Binärmaske: wo ist z >= z_level?
        mask = (Z >= z_level) & ~np.isnan(Z)

        # Polygone extrahieren
        polygons = mask_to_polygons(mask, xs, ys, min_area=10)

        # Hatching-Winkel (optional alternierend)
        if hatching_params.alternating:
            angle = hatching_params.angle_deg + i * hatching_params.angle_increment
        else:
            angle = hatching_params.angle_deg

        # Hatch-Segmente erzeugen
        segments = []
        for poly in polygons:
            segs = hatch_polygon(poly, angle, hatching_params.distance, z_level)
            segments.extend(segs)

        slices.append(SliceResult(
            z_level=z_level,
            polygons=polygons,
            segments=segments
        ))

        if verbose:
            print(f"  Schicht {i + 1}/{len(z_levels)}: z={z_level:.3f}, "
                  f"{len(polygons)} Polygone, {len(segments)} Segmente")

    # Parameter speichern
    params = {
        'structure': structure_params,
        'slicing': slicing_params,
        'hatching': hatching_params,
        'aperture': aperture is not None
    }

    result = SlicingResult(slices=slices, params=params)

    if verbose:
        print(f"\nGesamt: {result.total_segments()} Segmente, "
              f"Gesamtlänge: {result.total_length():.2f}")

    return result


# =============================================================================
# VISUALISIERUNG
# =============================================================================

def visualize_result(result: SlicingResult, height_func: Callable,
                     structure_params: StructureParams,
                     aperture: Optional[Callable] = None,
                     save_path: Optional[str] = None):
    """Visualisiert das Slicing-Ergebnis"""

    fig = plt.figure(figsize=(16, 10))

    # 1) 3D-Ansicht der Höhenfunktion
    ax1 = fig.add_subplot(2, 3, 1, projection='3d')
    xs = np.linspace(*structure_params.x_range, 100)
    ys = np.linspace(*structure_params.y_range, 100)
    X, Y = np.meshgrid(xs, ys)
    Z = height_func(X, Y)
    if aperture is not None:
        Z = np.where(aperture(X, Y), Z, np.nan)
    ax1.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    ax1.set_title('Höhenfunktion z(x,y)')

    # 2) Draufsicht mit Höhenlinien
    ax2 = fig.add_subplot(2, 3, 2)
    xs_fine = np.linspace(*structure_params.x_range, 200)
    ys_fine = np.linspace(*structure_params.y_range, 200)
    X_fine, Y_fine = np.meshgrid(xs_fine, ys_fine)
    Z_fine = height_func(X_fine, Y_fine)
    if aperture is not None:
        Z_fine = np.where(aperture(X_fine, Y_fine), Z_fine, np.nan)
    im = ax2.imshow(Z_fine, extent=[*structure_params.x_range, *structure_params.y_range],
                    origin='lower', cmap='viridis')
    plt.colorbar(im, ax=ax2, label='z')
    z_levels = [s.z_level for s in result.slices]
    ax2.contour(X_fine, Y_fine, Z_fine, levels=z_levels, colors='white',
                linewidths=0.5, alpha=0.7)
    ax2.set_title('Draufsicht mit Slice-Levels')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')

    # 3) Einzelne Schichten (Auswahl)
    num_show = min(4, len(result.slices))
    indices = np.linspace(0, len(result.slices) - 1, num_show, dtype=int)

    ax3 = fig.add_subplot(2, 3, 3)
    colors = plt.cm.plasma(np.linspace(0, 1, len(result.slices)))
    for i, slice_res in enumerate(result.slices):
        if i in indices:
            for poly in slice_res.polygons:
                ax3.fill(poly[:, 0], poly[:, 1], alpha=0.3,
                         facecolor=colors[i], edgecolor='black', linewidth=0.5)
    ax3.set_aspect('equal')
    ax3.set_title(f'Polygone ausgewählter Schichten')
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')

    # 4) Alle Hatch-Segmente (Draufsicht)
    ax4 = fig.add_subplot(2, 3, 4)
    for slice_res in result.slices:
        for seg in slice_res.segments:
            ax4.plot([seg.start[0], seg.end[0]],
                     [seg.start[1], seg.end[1]],
                     'b-', linewidth=0.2, alpha=0.5)
    ax4.set_aspect('equal')
    ax4.set_xlim(*structure_params.x_range)
    ax4.set_ylim(*structure_params.y_range)
    ax4.set_title(f'Alle Hatch-Segmente ({result.total_segments()})')
    ax4.set_xlabel('X')
    ax4.set_ylabel('Y')

    # 5) 3D-Ansicht der Segmente
    ax5 = fig.add_subplot(2, 3, 5, projection='3d')
    for slice_res in result.slices:
        z = slice_res.z_level
        for seg in slice_res.segments[::3]:  # Nur jeden 3. für Übersicht
            ax5.plot([seg.start[0], seg.end[0]],
                     [seg.start[1], seg.end[1]],
                     [z, z], 'b-', linewidth=0.3, alpha=0.5)
    ax5.set_xlabel('X')
    ax5.set_ylabel('Y')
    ax5.set_zlabel('Z')
    ax5.set_title('3D-Ansicht der Segmente')

    # 6) Statistik
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis('off')

    stats_text = f"""
    STATISTIK
    ─────────────────────────
    Anzahl Schichten: {len(result.slices)}
    Gesamte Segmente: {result.total_segments()}
    Gesamte Länge:    {result.total_length():.2f} Einheiten

    Schichten:
    """
    for i, s in enumerate(result.slices):
        stats_text += f"\n      z={s.z_level:.3f}: {len(s.segments)} Segmente"

    ax6.text(0.1, 0.9, stats_text, transform=ax6.transAxes,
             fontfamily='monospace', fontsize=10, verticalalignment='top')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Gespeichert: {save_path}")

    return fig


# =============================================================================
# EXPORT-FUNKTIONEN
# =============================================================================

def export_segments_to_array(result: SlicingResult) -> np.ndarray:
    """
    Exportiert Segmente als NumPy-Array
    Format: [[x1, y1, z1, x2, y2, z2], ...]
    """
    segments = result.get_all_segments()
    data = []
    for seg in segments:
        data.append([
            seg.start[0], seg.start[1], seg.start[2],
            seg.end[0], seg.end[1], seg.end[2]
        ])
    return np.array(data)


def export_segments_by_layer(result: SlicingResult) -> Dict[float, np.ndarray]:
    """
    Exportiert Segmente gruppiert nach Z-Level
    """
    layers = {}
    for slice_res in result.slices:
        data = []
        for seg in slice_res.segments:
            data.append([
                seg.start[0], seg.start[1],
                seg.end[0], seg.end[1]
            ])
        layers[slice_res.z_level] = np.array(data) if data else np.array([]).reshape(0, 4)
    return layers


def export_to_gwl(result: SlicingResult, filename: str,
                  power_func: Optional[Callable] = None):
    """
    Exportiert zu GWL-Format (für Nanoscribe etc.)

    power_func: Optional, Funktion power(z) -> Laserleistung
    """
    with open(filename, 'w') as f:
        f.write("% Generated by grating_slicer.py\n")
        f.write("% DOE/Grating_63 structure\n\n")

        for slice_res in result.slices:
            z = slice_res.z_level

            if power_func:
                power = power_func(z)
                f.write(f"LaserPower {power:.1f}\n")

            f.write(f"% Layer z={z:.4f}\n")

            for seg in slice_res.segments:
                f.write(f"{seg.start[0]:.4f} {seg.start[1]:.4f} {seg.start[2]:.4f}\n")
                f.write(f"{seg.end[0]:.4f} {seg.end[1]:.4f} {seg.end[2]:.4f}\n")
                f.write("Write\n\n")

    print(f"GWL exportiert: {filename}")


# =============================================================================
# BEISPIELE
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("BEISPIEL 1: Sinusförmiges Gitter mit Kreisapertur")
    print("=" * 70)

    # 1. Höhenfunktion definieren
    height_func = HeightFunctions.sinusoidal(
        period=2.0,  # Periode in µm
        height=1.0,  # Höhe (peak-to-peak)
        angle_deg=30,  # Gitter-Orientierung
        z0=0.5,  # Basis-Höhe
        phase=0  # Phase
    )

    # 2. Struktur-Parameter
    structure = StructureParams(
        x_range=(-5, 5),
        y_range=(-5, 5),
        resolution=400
    )

    # 3. Slicing-Parameter
    slicing = SlicingParams(
        z_min=0.1,
        z_max=0.9,
        num_slices=5  # 5 Schichten
        # ODER: dz=0.2    # alle 0.2 µm eine Schicht
    )

    # 4. Hatching-Parameter
    hatching = HatchingParams(
        angle_deg=30,  # Hatching parallel zum Gitter
        distance=0.3,  # Linienabstand
        alternating=False
    )

    # 5. Apertur (optional)
    aperture = Apertures.circular(radius=4.0)

    # 6. Slicing durchführen
    result = slice_structure(
        height_func=height_func,
        structure_params=structure,
        slicing_params=slicing,
        hatching_params=hatching,
        aperture=aperture,
        verbose=True
    )

    # 7. Visualisieren
    fig = visualize_result(result, height_func, structure, aperture,
                           save_path='/home/claude/example1_sinusoidal.png')

    # 8. Export
    segments_array = export_segments_to_array(result)
    print(f"\nExportiertes Array Shape: {segments_array.shape}")
    print(f"Erste 3 Segmente:\n{segments_array[:3]}")

    print("\n" + "=" * 70)
    print("BEISPIEL 2: Blazed Gitter")
    print("=" * 70)

    height_func2 = HeightFunctions.blazed_grating(
        period=1.5,
        height=0.8,
        angle_deg=0
    )

    slicing2 = SlicingParams(z_min=0.0, z_max=0.8, dz=0.1)

    result2 = slice_structure(
        height_func=height_func2,
        structure_params=structure,
        slicing_params=slicing2,
        hatching_params=HatchingParams(angle_deg=90, distance=0.25),
        aperture=Apertures.rectangular(8, 6),
        verbose=True
    )

    visualize_result(result2, height_func2, structure,
                     Apertures.rectangular(8, 6),
                     save_path='/home/claude/example2_blazed.png')

    print("\n" + "=" * 70)
    print("BEISPIEL 3: Gekreuzte Gitter")
    print("=" * 70)

    height_func3 = HeightFunctions.crossed_gratings(
        period1=2.0,
        period2=2.0,
        height=1.0,
        angle1_deg=0,
        angle2_deg=90
    )

    result3 = slice_structure(
        height_func=height_func3,
        structure_params=structure,
        slicing_params=SlicingParams(z_min=-0.4, z_max=0.4, num_slices=5),
        hatching_params=HatchingParams(angle_deg=45, distance=0.2,
                                       alternating=True, angle_increment=90),
        aperture=Apertures.circular(4.5),
        verbose=True
    )

    visualize_result(result3, height_func3, structure,
                     Apertures.circular(4.5),
                     save_path='/home/claude/example3_crossed.png')

    plt.show()