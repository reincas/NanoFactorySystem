# Drawings Module - Modular Structure

## Übersicht

Die neue modulare Struktur trennt wiederverwendbare Komponenten von spezifischen Struktur-Implementierungen.

```
drawings/
├── __init__.py                  # Haupt-Init mit allen Imports
├── base.py                      # DrawableObject, etc. (bestehend)
├── lines.py                     # PolyLine, Rectangle3D, etc. (bestehend)
│
├── tile_manager.py              # ✓ STANDALONE - Bleibt wie es ist
├── apertures.py                 # ★ NEU STANDALONE - Für alle Strukturen!
├── laser_segments.py            # ★ NEU STANDALONE - Für alle Strukturen!
├── hatch_generator.py           # ★ NEU STANDALONE - Für alle Strukturen!
├── height_functions.py          # ★ NEU STANDALONE - Mathematische Funktionen
│
└── height_function_structures/  # Grating-Strukturen
    ├── __init__.py
    ├── slicer.py
    └── structures.py
```

## Installation

### Schritt 1: Neue Dateien kopieren

```bash
cd nanofactorysystem/aerobasic/programs/drawings/

# Neue standalone Module hinzufügen
cp drawings_modular/apertures.py .
cp drawings_modular/laser_segments.py .
cp drawings_modular/hatch_generator.py .
cp drawings_modular/height_functions.py .

# Height function structures Ordner hinzufügen
cp -r drawings_modular/height_function_structures/ .

# __init__.py ersetzen (BACKUP machen!)
cp __init__.py __init__.backup.py
cp drawings_modular/__init__.py .
```

### Schritt 2: Imports anpassen

Falls du Import-Fehler bekommst, passe die `__init__.py` an:

```python
# Kommentiere aus was fehlt:
# from .lines import XLines, YLines, ZLines  # Falls nicht vorhanden
```

## Vorteile der modularen Struktur

### 1. Apertures für ALLE Strukturen

```python
from nanofactorysystem.aerobasic.programs.drawings import Apertures

# Jetzt kann JEDE Struktur Apertures nutzen!
aperture = Apertures.circular(radius=50)
aperture = Apertures.rectangular(width=100, height=80)
aperture = Apertures.annular(inner_radius=20, outer_radius=50)

# Kombinieren
aperture = Apertures.subtract(
    Apertures.circular(radius=50),
    Apertures.rectangular(width=20, height=20)
)
```

### 2. HatchGenerator für beliebige Formen

```python
from nanofactorysystem.aerobasic.programs.drawings import HatchGenerator, HatchConfig

# Für Rectangle3D mit Aperture (zukünftig)
hatch_gen = HatchGenerator(HatchConfig(hatch_size=0.3, hatch_angle_deg=45))

# Hatch mit Aperture
segments = hatch_gen.hatch_with_aperture(
    x_min=-50, x_max=50,
    y_min=-50, y_max=50,
    z_level=0,
    aperture=Apertures.circular(radius=40),
    resolution=500
)
```

### 3. LaserSegments statt PolyLines

```python
from nanofactorysystem.aerobasic.programs.drawings import (
    LaserSegments, LaserSegmentsConfig, SortingStrategy
)

# Für discontinuous laser paths
config = LaserSegmentsConfig(
    velocity=10000,
    acceleration=100000,
    sorting_strategy=SortingStrategy.SERPENTINE
)

laser_segments = LaserSegments(segments=my_segments, config=config)
```

## Beispiel: Binary Grating

```python
from nanofactorysystem.aerobasic.programs.drawings import (
    BinaryGrating, Apertures
)
from nanofactorysystem.devices.coordinate_system import Point3D

grating = BinaryGrating(
    center=Point3D(0, 0, -2),
    width=100,
    length=100,
    period=10,
    height=2,
    duty_cycle=0.5,           # Oder 5 für 5µm
    grating_angle_deg=0.0,
    base_height=2.0,
    
    # Fabrication
    hatch_size=0.2,
    slice_size=0.2,
    velocity=10000,
    acceleration=100000,
    
    # Aperture (NEU: Standalone Modul!)
    aperture=Apertures.circular(radius=50),
    
    # Hatching
    hatch_angle_deg=0.0,
    alternating_hatch=True,
    
    # Tiling
    fov_size=(150, 150),
    usable_fov_fraction=0.85,
    grid_resolution=500       # NICHT 10000!
)

# Iteration mit Strategie-Wahl
for program in grating.iterate_layers(cs, strategy="TILE_FIRST"):
    ...
```

## Strategie-Vergleich

```python
# TILE_FIRST: Ein Tile komplett, dann nächstes
for program in grating.iterate_layers(cs, strategy="TILE_FIRST"):
    ...

# LAYER_FIRST: Layer 1 in allen Tiles, dann Layer 2, etc.
for program in grating.iterate_layers(cs, strategy="LAYER_FIRST"):
    ...
```

## Zukünftige Erweiterungen

Mit der modularen Struktur kannst du einfach:

1. **Rectangle3D mit Aperture** erweitern
2. **Stair mit Aperture** erweitern
3. **Neue Strukturen** hinzufügen die alle Module nutzen
4. **STL Import** über `HeightFunctions.from_array()` implementieren

## Dateistruktur nach Installation

```
nanofactorysystem/aerobasic/programs/drawings/
├── __init__.py                  # Aktualisiert
├── base.py                      # Unverändert
├── lines.py                     # Unverändert
├── tile_manager.py              # Unverändert
│
├── apertures.py                 # ★ NEU
├── laser_segments.py            # ★ NEU
├── hatch_generator.py           # ★ NEU
├── height_functions.py          # ★ NEU
│
└── height_function_structures/  # ★ NEU
    ├── __init__.py
    ├── slicer.py
    └── structures.py
```
