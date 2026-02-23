"""
Configuration and utility classes for NanoFactorySystem drawings
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union
from enum import Enum
import numpy as np
from pathlib import Path
import json

from nanofactorysystem.devices.coordinate_system import Point2D, Point3D


@dataclass
class DrawingConfig:
    """
    Gemeinsame Konfiguration für alle Drawing-Objekte

    Diese Klasse vereinheitlicht die Parameter-Übergabe und macht
    das System konsistenter und wartbarer.
    """
    # Bewegungsparameter
    velocity: float  # μm/s
    acceleration: float  # μm/s²

    # Strukturparameter
    hatch_size: float  # μm - Abstand zwischen Schraffurlinien
    slice_size: float  # μm - Höhe der einzelnen Layer

    # Optionale Laser-Parameter
    laser_power: Optional[float] = None  # mW
    dwell_time: Optional[float] = None  # s

    # Erweiterte Parameter
    acceleration_distance_factor: float = 2.0
    use_velocity_mode: bool = True
    use_ifov: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def scale_velocity(self, factor: float) -> 'DrawingConfig':
        """Skaliere Geschwindigkeits/Beschleunigungs-Parameter"""
        return DrawingConfig(
            velocity=self.velocity * factor,
            acceleration=self.acceleration * factor,
            hatch_size=self.hatch_size,
            slice_size=self.slice_size,
            laser_power=self.laser_power,
            dwell_time=self.dwell_time,
            acceleration_distance_factor=self.acceleration_distance_factor,
            use_velocity_mode=self.use_velocity_mode,
            use_ifov=self.use_ifov,
            metadata=self.metadata.copy()
        )

    def scale_resolution(self, factor: float) -> 'DrawingConfig':
        """Skaliere Auflösungs-Parameter (kleinerer Faktor = höhere Auflösung)"""
        return DrawingConfig(
            velocity=self.velocity,
            acceleration=self.acceleration,
            hatch_size=self.hatch_size * factor,
            slice_size=self.slice_size * factor,
            laser_power=self.laser_power,
            dwell_time=self.dwell_time,
            acceleration_distance_factor=self.acceleration_distance_factor,
            use_velocity_mode=self.use_velocity_mode,
            use_ifov=self.use_ifov,
            metadata=self.metadata.copy()
        )

    def with_laser_params(self, power: float, dwell_time: float = None) -> 'DrawingConfig':
        """Füge Laser-Parameter hinzu"""
        return DrawingConfig(
            velocity=self.velocity,
            acceleration=self.acceleration,
            hatch_size=self.hatch_size,
            slice_size=self.slice_size,
            laser_power=power,
            dwell_time=dwell_time or self.dwell_time,
            acceleration_distance_factor=self.acceleration_distance_factor,
            use_velocity_mode=self.use_velocity_mode,
            use_ifov=self.use_ifov,
            metadata=self.metadata.copy()
        )

    def to_dict(self) -> dict:
        """Konvertiere zu Dictionary für Serialisierung"""
        return {
            'velocity': self.velocity,
            'acceleration': self.acceleration,
            'hatch_size': self.hatch_size,
            'slice_size': self.slice_size,
            'laser_power': self.laser_power,
            'dwell_time': self.dwell_time,
            'acceleration_distance_factor': self.acceleration_distance_factor,
            'use_velocity_mode': self.use_velocity_mode,
            'use_ifov': self.use_ifov,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DrawingConfig':
        """Erstelle Config aus Dictionary"""
        return cls(**data)

    def save(self, path: Union[str, Path]):
        """Speichere Config als JSON"""
        path = Path(path)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Union[str, Path]) -> 'DrawingConfig':
        """Lade Config aus JSON"""
        path = Path(path)
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))


class ProcessType(Enum):
    """Verschiedene Prozesstypen mit vordefinierten Configs"""
    HIGH_SPEED = "high_speed"
    HIGH_RESOLUTION = "high_resolution"
    STANDARD = "standard"
    CALIBRATION = "calibration"


class ConfigPresets:
    """Vordefinierte Konfigurationen für verschiedene Anwendungen"""

    @staticmethod
    def get_preset(process_type: ProcessType) -> DrawingConfig:
        """Hole vordefinierte Config für Prozesstyp"""
        presets = {
            ProcessType.HIGH_SPEED: DrawingConfig(
                velocity=10000.0,  # 10 mm/s
                acceleration=100000.0,  # 100 mm/s²
                hatch_size=2.0,  # 2 μm
                slice_size=1.0,  # 1 μm
                laser_power=50.0,  # 50 mW
                metadata={'type': 'high_speed', 'description': 'Schnelle Produktion'}
            ),
            ProcessType.HIGH_RESOLUTION: DrawingConfig(
                velocity=500.0,  # 0.5 mm/s
                acceleration=5000.0,  # 5 mm/s²
                hatch_size=0.5,  # 500 nm
                slice_size=0.2,  # 200 nm
                laser_power=20.0,  # 20 mW
                metadata={'type': 'high_resolution', 'description': 'Höchste Auflösung'}
            ),
            ProcessType.STANDARD: DrawingConfig(
                velocity=2000.0,  # 2 mm/s
                acceleration=20000.0,  # 20 mm/s²
                hatch_size=1.0,  # 1 μm
                slice_size=0.5,  # 500 nm
                laser_power=35.0,  # 35 mW
                metadata={'type': 'standard', 'description': 'Standard Prozess'}
            ),
            ProcessType.CALIBRATION: DrawingConfig(
                velocity=1000.0,  # 1 mm/s
                acceleration=10000.0,  # 10 mm/s²
                hatch_size=1.0,  # 1 μm
                slice_size=0.5,  # 500 nm
                laser_power=30.0,  # 30 mW
                dwell_time=0.1,  # 100 ms
                metadata={'type': 'calibration', 'description': 'Für Kalibrierung'}
            )
        }
        return presets[process_type]


class PathOptimizer:
    """Optimiert die Pfade für minimale Bewegungen"""

    @staticmethod
    def optimize_point_order(points: list[Union[Point2D, Point3D]]) -> list[Union[Point2D, Point3D]]:
        """
        Optimiere die Reihenfolge von Punkten für minimale Gesamtdistanz
        Verwendet einen einfachen Nearest-Neighbor Algorithmus
        """
        if len(points) <= 2:
            return points

        optimized = [points[0]]
        remaining = points[1:].copy()

        while remaining:
            current = optimized[-1]
            # Finde nächsten Punkt
            distances = []
            for point in remaining:
                if isinstance(current, Point3D) and isinstance(point, Point3D):
                    dist = np.sqrt((current.X - point.X) ** 2 +
                                   (current.Y - point.Y) ** 2 +
                                   (current.Z - point.Z) ** 2)
                else:
                    # 2D Distanz
                    dist = np.sqrt((current.X - point.X) ** 2 +
                                   (current.Y - point.Y) ** 2)
                distances.append(dist)

            nearest_idx = np.argmin(distances)
            optimized.append(remaining.pop(nearest_idx))

        return optimized

    @staticmethod
    def calculate_total_distance(points: list[Union[Point2D, Point3D]]) -> float:
        """Berechne Gesamtdistanz eines Pfades"""
        if len(points) < 2:
            return 0.0

        total = 0.0
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            if isinstance(p1, Point3D) and isinstance(p2, Point3D):
                dist = np.sqrt((p1.X - p2.X) ** 2 +
                               (p1.Y - p2.Y) ** 2 +
                               (p1.Z - p2.Z) ** 2)
            else:
                dist = np.sqrt((p1.X - p2.X) ** 2 +
                               (p1.Y - p2.Y) ** 2)
            total += dist

        return total


class LayerOptimizer:
    """Optimiert Layer-Generierung"""

    @staticmethod
    def calculate_optimal_layers(height: float, target_slice_size: float) -> tuple[int, float]:
        """
        Berechne optimale Anzahl von Layern und angepasste Slice-Size

        Returns:
            (n_layers, optimized_slice_size)
        """
        n_layers = max(1, round(height / target_slice_size))
        optimized_slice_size = height / n_layers
        return n_layers, optimized_slice_size

    @staticmethod
    def calculate_optimal_hatching(width: float, target_hatch_size: float) -> tuple[int, float]:
        """
        Berechne optimale Anzahl von Schraffurlinien und angepasste Hatch-Size

        Returns:
            (n_lines, optimized_hatch_size)
        """
        n_lines = max(1, round(width / target_hatch_size) + 1)
        optimized_hatch_size = width / (n_lines - 1)
        return n_lines, optimized_hatch_size


def validate_positive(*param_names):
    """Decorator zur Validierung positiver Parameter"""
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for name in param_names:
                if name in bound.arguments:
                    value = bound.arguments[name]
                    if value is not None and value <= 0:
                        raise ValueError(f"{name} must be positive, got {value}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_range(param_name: str, min_val: float = None, max_val: float = None):
    """Decorator zur Validierung von Wertebereichen"""
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            if param_name in bound.arguments:
                value = bound.arguments[param_name]
                if value is not None:
                    if min_val is not None and value < min_val:
                        raise ValueError(f"{param_name} must be >= {min_val}, got {value}")
                    if max_val is not None and value > max_val:
                        raise ValueError(f"{param_name} must be <= {max_val}, got {value}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


# Beispiel-Verwendung der neuen Config
if __name__ == "__main__":
    # Erstelle Config aus Preset
    config = ConfigPresets.get_preset(ProcessType.STANDARD)

    # Modifiziere für höhere Geschwindigkeit
    fast_config = config.scale_velocity(2.0)

    # Modifiziere für höhere Auflösung
    fine_config = config.scale_resolution(0.5)

    # Speichere Config
    config.save("standard_config.json")

    # Lade Config
    loaded_config = DrawingConfig.load("standard_config.json")

    print(f"Standard Config: {config}")
    print(f"Fast Config: {fast_config}")
    print(f"Fine Config: {fine_config}")