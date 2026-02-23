from dataclasses import dataclass
from typing import Optional, Iterator
import unittest

from nanofactorysystem.aerobasic.programs.drawings import DrawableAeroBasicProgram, DrawableObject
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point3D
from functools import wraps

def validate_positive(*param_names):
    """Decorator zur Validierung positiver Parameter"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            bound = func.__code__.co_varnames
            for i, value in enumerate(args):
                if i < len(param_names) and bound[i] in param_names:
                    if value <= 0:
                        raise ValueError(f"{bound[i]} must be positive, got {value}")
            for name in param_names:
                if name in kwargs and kwargs[name] <= 0:
                    raise ValueError(f"{name} must be positive, got {kwargs[name]}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

"""
class Circle2D(DrawableObject):
    @validate_positive('radius', 'velocity')
    def __init__(self, center, radius, velocity):
        # ...

class TestDrawableObjects(unittest.TestCase):
    def setUp(self):
        self.coord_system = CoordinateSystem()

    def test_circle_creation(self):
        circle = Circle2D(
            center=Point3D(0, 0, 0),
            radius=10.0,
            velocity=100.0
        )
        program = circle.draw_on(self.coord_system)
        self.assertIsNotNone(program)

    def test_rectangle_volume(self):
        rect = Rectangle3D(
            center=Point3D(0, 0, 0),
            width=10, length=20, height=5,
            hatch_size=1, slice_size=0.5,
            velocity=100, acceleration=1000
        )
        self.assertEqual(rect.structure_width, 10)
        self.assertEqual(rect.structure_length, 20)
"""


class LayerManager:
    """Verwaltet Layer-Generierung mit Optimierungen"""

    def __init__(self, coordinate_system: CoordinateSystem):
        self.coordinate_system = coordinate_system
        self.layer_cache = {}

    def optimize_layer_order(
            self,
            objects: list[DrawableObject]
    ) -> Iterator[DrawableAeroBasicProgram]:
        """Optimiere die Reihenfolge der Layer für minimale Bewegungen"""
        # Sortiere Objekte nach Position für optimale Pfade
        sorted_objects = sorted(objects, key=lambda o: (o.center_point.X, o.center_point.Y))

        for obj in sorted_objects:
            yield from obj.iterate_layers(self.coordinate_system)


class StructureFactory:
    """Factory für häufig verwendete Strukturen"""

    def __init__(self, default_config: DrawingConfig):
        self.config = default_config

    def create_test_grid(
            self,
            center: Point3D,
            rows: int,
            cols: int,
            spacing: float
    ) -> list[DrawableObject]:
        """Erstelle ein Test-Grid aus mehreren Strukturen"""
        structures = []
        for i in range(rows):
            for j in range(cols):
                offset = Point3D(
                    X=i * spacing - (rows - 1) * spacing / 2,
                    Y=j * spacing - (cols - 1) * spacing / 2,
                    Z=0
                )
                structures.append(
                    Circle2D(
                        center=center + offset,
                        radius=spacing / 4,
                        velocity=self.config.velocity
                    )
                )
        return structures


@dataclass
class DrawingConfig:
    """Gemeinsame Konfiguration für alle Drawing-Objekte"""
    velocity: float
    acceleration: float
    hatch_size: float
    slice_size: float

    # Optional parameters
    laser_power: Optional[float] = None
    dwell_time: Optional[float] = None

    def scale(self, factor: float) -> 'DrawingConfig':
        """Skaliere alle Geschwindigkeits/Beschleunigungs-Parameter"""
        return DrawingConfig(
            velocity=self.velocity * factor,
            acceleration=self.acceleration * factor,
            hatch_size=self.hatch_size,
            slice_size=self.slice_size,
            laser_power=self.laser_power,
            dwell_time=self.dwell_time
        )




class StructureFactory:
    """Factory für häufig verwendete Strukturen"""

    def __init__(self, default_config: DrawingConfig):
        self.config = default_config

    def create_test_grid(
            self,
            center: Point3D,
            rows: int,
            cols: int,
            spacing: float
    ) -> list[DrawableObject]:
        """Erstelle ein Test-Grid aus mehreren Strukturen"""
        structures = []
        for i in range(rows):
            for j in range(cols):
                offset = Point3D(
                    X=i * spacing - (rows - 1) * spacing / 2,
                    Y=j * spacing - (cols - 1) * spacing / 2,
                    Z=0
                )
                structures.append(
                    Circle2D(
                        center=center + offset,
                        radius=spacing / 4,
                        velocity=self.config.velocity
                    )
                )
        return structures
