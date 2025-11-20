"""
Flexible Triangle Implementation for NanoFactorySystem
Supports various parameter combinations to define triangles
"""

import math
import numpy as np
from enum import Enum
from typing import Iterator, Optional, Union, Tuple
from dataclasses import dataclass

from nanofactorysystem.aerobasic.programs.drawings import DrawableObject, DrawableAeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.lines import PolyLine, XLines, YLines
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point2D, Point3D


@dataclass
class TriangleGeometry:
    """
    Container for triangle geometry calculations
    """
    # Vertices (always 3 points)
    vertices: list[Point2D]

    # Sides (lengths)
    side_a: float  # Opposite to vertex A
    side_b: float  # Opposite to vertex B
    side_c: float  # Opposite to vertex C (base)

    # Angles (in degrees)
    angle_A: float  # At vertex A
    angle_B: float  # At vertex B
    angle_C: float  # At vertex C

    # Other properties
    area: float
    perimeter: float
    centroid: Point2D
    height: float  # Height from base to opposite vertex
    base_width: float

    @classmethod
    def from_vertices(cls, v1: Point2D, v2: Point2D, v3: Point2D) -> 'TriangleGeometry':
        """Calculate all properties from three vertices"""

        # Calculate side lengths
        side_a = math.sqrt((v2.X - v3.X) ** 2 + (v2.Y - v3.Y) ** 2)  # BC
        side_b = math.sqrt((v1.X - v3.X) ** 2 + (v1.Y - v3.Y) ** 2)  # AC
        side_c = math.sqrt((v1.X - v2.X) ** 2 + (v1.Y - v2.Y) ** 2)  # AB (base)

        # Calculate angles using law of cosines
        angle_A = math.degrees(math.acos((side_b ** 2 + side_c ** 2 - side_a ** 2) / (2 * side_b * side_c)))
        angle_B = math.degrees(math.acos((side_a ** 2 + side_c ** 2 - side_b ** 2) / (2 * side_a * side_c)))
        angle_C = 180 - angle_A - angle_B

        # Calculate area using cross product
        area = 0.5 * abs((v2.X - v1.X) * (v3.Y - v1.Y) - (v3.X - v1.X) * (v2.Y - v1.Y))

        # Calculate centroid
        centroid = Point2D((v1.X + v2.X + v3.X) / 3, (v1.Y + v2.Y + v3.Y) / 3)

        # Calculate height (from base AB to vertex C)
        height = 2 * area / side_c

        return cls(
            vertices=[v1, v2, v3],
            side_a=side_a,
            side_b=side_b,
            side_c=side_c,
            angle_A=angle_A,
            angle_B=angle_B,
            angle_C=angle_C,
            area=area,
            perimeter=side_a + side_b + side_c,
            centroid=centroid,
            height=height,
            base_width=side_c
        )


class FlexibleTriangle(DrawableObject):
    """
    Highly flexible triangle with multiple ways to define it:

    1. By three vertices (points)
    2. By two angles and one side
    3. By three sides
    4. By base, height, and position of apex
    5. By standard types (equilateral, isosceles, right)
    """

    def __init__(
            self,
            center: Union[Point2D, Point3D],

            # Option 1: Direct vertices
            vertices: Optional[list[Point2D]] = None,

            # Option 2: Angles and sides (any valid combination)
            angle_left: Optional[float] = None,  # Angle at left vertex (degrees)
            angle_right: Optional[float] = None,  # Angle at right vertex (degrees)
            angle_top: Optional[float] = None,  # Angle at top vertex (degrees)
            base_width: Optional[float] = None,  # Width of base
            left_side: Optional[float] = None,  # Length of left side
            right_side: Optional[float] = None,  # Length of right side
            height: Optional[float] = None,  # Perpendicular height from base

            # Option 3: Special triangles
            equilateral_side: Optional[float] = None,  # For equilateral triangle

            # Position and orientation
            rotation: float = 0,  # Rotation in degrees (0 = base horizontal)
            apex_offset: float = 0,  # Horizontal offset of apex from center (0 = centered)

            # Drawing parameters
            filled: bool = False,
            hatch_size: float = 1.0,
            velocity: float = 1000.0,
            acceleration: float = 10000.0
    ):
        super().__init__()
        self.center = center
        self.rotation = rotation
        self.filled = filled
        self.hatch_size = hatch_size
        self.velocity = velocity
        self.acceleration = acceleration

        # Calculate vertices based on input parameters
        if vertices is not None:
            # Option 1: Direct vertices provided
            self.geometry = TriangleGeometry.from_vertices(*vertices[:3])

        elif equilateral_side is not None:
            # Special case: Equilateral triangle
            self.geometry = self._create_equilateral(equilateral_side)

        elif angle_left is not None and angle_right is not None and base_width is not None:
            # Option 2a: Two base angles and base width
            self.geometry = self._create_from_base_angles(angle_left, angle_right, base_width)

        elif base_width is not None and height is not None:
            # Option 2b: Base width and height
            self.geometry = self._create_from_base_height(base_width, height, apex_offset, angle_left, angle_right)

        elif angle_left is not None and base_width is not None and left_side is not None:
            # Option 2c: Angle-Side-Side (ASS/SSA)
            self.geometry = self._create_from_ass(angle_left, base_width, left_side)

        elif left_side is not None and right_side is not None and base_width is not None:
            # Option 2d: Three sides (SSS)
            self.geometry = self._create_from_three_sides(left_side, right_side, base_width)

        else:
            raise ValueError(
                "Insufficient parameters to define triangle. Provide either:\n"
                "1. Three vertices\n"
                "2. Two angles and base_width\n"
                "3. base_width and height\n"
                "4. Three sides\n"
                "5. equilateral_side"
            )

        # Apply rotation if specified
        if self.rotation != 0:
            self._rotate_triangle()

    @property
    def center_point(self) -> Point2D:
        if isinstance(self.center, Point3D):
            return Point2D(self.center.X, self.center.Y)
        return self.center

    def _create_equilateral(self, side_length: float) -> TriangleGeometry:
        """Create equilateral triangle"""
        h = side_length * math.sqrt(3) / 2

        # Vertices centered at origin
        v1 = Point2D(-side_length / 2, -h / 3)  # Bottom left
        v2 = Point2D(side_length / 2, -h / 3)  # Bottom right
        v3 = Point2D(0, 2 * h / 3)  # Top

        return TriangleGeometry.from_vertices(v1, v2, v3)

    def _create_from_base_angles(self, angle_left: float, angle_right: float, base_width: float) -> TriangleGeometry:
        """Create triangle from two base angles and base width"""

        # Third angle
        angle_top = 180 - angle_left - angle_right
        if angle_top <= 0:
            raise ValueError(f"Invalid angles: sum must be < 180° (got {angle_left + angle_right}°)")

        # Calculate height using trigonometry
        # height = (base_width/2) * (tan(angle_left) + tan(angle_right)) / 2
        # Simplified:
        height = (base_width / 2) * (
                1 / math.tan(math.radians(angle_left)) +
                1 / math.tan(math.radians(angle_right))
        ) / (
                         1 / math.tan(math.radians(angle_left)) / math.tan(math.radians(angle_right)) + 1
                 )

        # More intuitive approach:
        height = (base_width / 2) * math.tan(math.radians(angle_left)) * math.tan(math.radians(angle_right)) / (
                math.tan(math.radians(angle_left)) + math.tan(math.radians(angle_right))
        )

        # Actually, let's use a clearer formula:
        # For a triangle with base angles α and β:
        height = base_width * math.sin(math.radians(angle_left)) * math.sin(math.radians(angle_right)) / (
            math.sin(math.radians(angle_left + angle_right))
        )

        # Calculate apex x-position
        # Using law of sines
        apex_x = -base_width / 2 + base_width * math.sin(math.radians(angle_left)) / math.sin(
            math.radians(angle_left + angle_right))

        # Create vertices
        v1 = Point2D(-base_width / 2, 0)  # Bottom left
        v2 = Point2D(base_width / 2, 0)  # Bottom right
        v3 = Point2D(apex_x, height)  # Top

        # Center at centroid
        centroid_y = height / 3
        v1 = Point2D(v1.X, v1.Y - centroid_y)
        v2 = Point2D(v2.X, v2.Y - centroid_y)
        v3 = Point2D(v3.X, v3.Y - centroid_y)

        return TriangleGeometry.from_vertices(v1, v2, v3)

    def _create_from_base_height(
            self,
            base_width: float,
            height: float,
            apex_offset: float = 0,
            angle_left: Optional[float] = None,
            angle_right: Optional[float] = None
    ) -> TriangleGeometry:
        """Create triangle from base width, height, and optional apex offset"""

        # If angles are specified, use them to calculate apex position
        if angle_left is not None and angle_right is not None:
            return self._create_from_base_angles(angle_left, angle_right, base_width)

        # Otherwise use apex_offset directly
        # Create vertices
        v1 = Point2D(-base_width / 2, 0)  # Bottom left
        v2 = Point2D(base_width / 2, 0)  # Bottom right
        v3 = Point2D(apex_offset, height)  # Top (with offset)

        # Center at centroid
        centroid_y = height / 3
        v1 = Point2D(v1.X, v1.Y - centroid_y)
        v2 = Point2D(v2.X, v2.Y - centroid_y)
        v3 = Point2D(v3.X, v3.Y - centroid_y)

        return TriangleGeometry.from_vertices(v1, v2, v3)

    def _create_from_three_sides(self, side_a: float, side_b: float, side_c: float) -> TriangleGeometry:
        """Create triangle from three side lengths using law of cosines"""

        # Check triangle inequality
        if not (side_a + side_b > side_c and side_a + side_c > side_b and side_b + side_c > side_a):
            raise ValueError(f"Invalid triangle: sides {side_a}, {side_b}, {side_c} violate triangle inequality")

        # Place first vertex at origin, second on x-axis
        v1 = Point2D(0, 0)
        v2 = Point2D(side_c, 0)  # side_c is the base

        # Calculate position of third vertex using law of cosines
        # cos(A) = (b² + c² - a²) / (2bc)
        cos_A = (side_b ** 2 + side_c ** 2 - side_a ** 2) / (2 * side_b * side_c)
        sin_A = math.sqrt(1 - cos_A ** 2)

        v3 = Point2D(
            side_b * cos_A,
            side_b * sin_A
        )

        # Center at centroid
        centroid_x = (v1.X + v2.X + v3.X) / 3
        centroid_y = (v1.Y + v2.Y + v3.Y) / 3

        v1 = Point2D(v1.X - centroid_x, v1.Y - centroid_y)
        v2 = Point2D(v2.X - centroid_x, v2.Y - centroid_y)
        v3 = Point2D(v3.X - centroid_x, v3.Y - centroid_y)

        return TriangleGeometry.from_vertices(v1, v2, v3)

    def _create_from_ass(self, angle: float, adjacent_side: float, opposite_side: float) -> TriangleGeometry:
        """Create triangle from Angle-Side-Side (may have 0, 1, or 2 solutions)"""

        # Using law of sines: a/sin(A) = b/sin(B)
        sin_opposite_angle = opposite_side * math.sin(math.radians(angle)) / adjacent_side

        if sin_opposite_angle > 1:
            raise ValueError("No valid triangle possible with given parameters")

        opposite_angle = math.degrees(math.asin(sin_opposite_angle))
        third_angle = 180 - angle - opposite_angle

        # Now we have all angles, can construct the triangle
        # Place vertices
        v1 = Point2D(0, 0)
        v2 = Point2D(adjacent_side, 0)

        # Third vertex using the angle
        v3 = Point2D(
            opposite_side * math.cos(math.radians(180 - opposite_angle)),
            opposite_side * math.sin(math.radians(180 - opposite_angle))
        )

        # Center at centroid
        centroid_x = (v1.X + v2.X + v3.X) / 3
        centroid_y = (v1.Y + v2.Y + v3.Y) / 3

        v1 = Point2D(v1.X - centroid_x, v1.Y - centroid_y)
        v2 = Point2D(v2.X - centroid_x, v2.Y - centroid_y)
        v3 = Point2D(v3.X - centroid_x, v3.Y - centroid_y)

        return TriangleGeometry.from_vertices(v1, v2, v3)

    def _rotate_triangle(self):
        """Apply rotation to triangle vertices"""
        angle_rad = math.radians(self.rotation)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        rotated_vertices = []
        for v in self.geometry.vertices:
            x_rot = v.X * cos_a - v.Y * sin_a
            y_rot = v.X * sin_a + v.Y * cos_a
            rotated_vertices.append(Point2D(x_rot, y_rot))

        # Recalculate geometry with rotated vertices
        self.geometry = TriangleGeometry.from_vertices(*rotated_vertices)

    def get_info(self) -> dict:
        """Return dictionary with all triangle properties"""
        return {
            "area": self.geometry.area,
            "perimeter": self.geometry.perimeter,
            "sides": {
                "a": self.geometry.side_a,
                "b": self.geometry.side_b,
                "c": self.geometry.side_c
            },
            "angles": {
                "A": self.geometry.angle_A,
                "B": self.geometry.angle_B,
                "C": self.geometry.angle_C
            },
            "height": self.geometry.height,
            "base_width": self.geometry.base_width,
            "centroid": (self.geometry.centroid.X, self.geometry.centroid.Y)
        }

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        """Generate drawing program for triangle"""
        program = DrawableAeroBasicProgram(coordinate_system)

        # Translate vertices to actual position
        actual_vertices = [
            {"X": self.center.X + v.X, "Y": self.center.Y + v.Y}
            for v in self.geometry.vertices
        ]

        # Add Z coordinate if center is 3D
        if isinstance(self.center, Point3D):
            for v in actual_vertices:
                v['Z'] = self.center.Z

        if not self.filled:
            # Draw outline only
            closed_vertices = actual_vertices + [actual_vertices[0]]
            outline = PolyLine(line=closed_vertices, F=self.velocity)
            program.add_programm(outline.draw_on(coordinate_system))
        else:
            # Fill with hatching
            program.add_programm(self._generate_filled_triangle(coordinate_system))

        yield program

    def _generate_filled_triangle(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        """Fill triangle with hatching pattern"""
        program = DrawableAeroBasicProgram(coordinate_system)

        # Get actual vertex positions
        actual_vertices = [
            (self.center.X + v.X, self.center.Y + v.Y)
            for v in self.geometry.vertices
        ]

        # Find bounding box
        ys = [v[1] for v in actual_vertices]
        min_y, max_y = min(ys), max(ys)

        # Generate horizontal hatching
        z = self.center.Z if isinstance(self.center, Point3D) else 0
        n_lines = int((max_y - min_y) / self.hatch_size) + 1

        order = 1
        for i in range(n_lines):
            y = min_y + i * self.hatch_size

            # Find intersections with triangle edges
            intersections = []
            for j in range(3):
                v1 = actual_vertices[j]
                v2 = actual_vertices[(j + 1) % 3]

                # Check intersection
                if min(v1[1], v2[1]) <= y <= max(v1[1], v2[1]):
                    if abs(v2[1] - v1[1]) > 1e-10:
                        t = (y - v1[1]) / (v2[1] - v1[1])
                        x = v1[0] + t * (v2[0] - v1[0])
                        intersections.append(x)

            # Draw line if we have intersections
            if len(intersections) >= 2:
                intersections.sort()
                lines = [(intersections[0], intersections[-1])[::order]]

                x_line = XLines(
                    y=y,
                    z=z,
                    lines=lines,
                    velocity=self.velocity,
                    acceleration=self.acceleration
                )
                program.add_programm(x_line.draw_on(coordinate_system))
                order *= -1

        return program


# Convenience functions for common triangle types
def create_right_triangle(
        center: Union[Point2D, Point3D],
        base: float,
        height: float,
        right_angle_position: str = "bottom_left",  # "bottom_left", "bottom_right", "top"
        **kwargs
) -> FlexibleTriangle:
    """Create a right-angled triangle"""

    if right_angle_position == "bottom_left":
        rotation = 0
        angle_left = 90
        angle_right = math.degrees(math.atan(height / base))
    elif right_angle_position == "bottom_right":
        rotation = 0
        angle_left = math.degrees(math.atan(height / base))
        angle_right = 90
    elif right_angle_position == "top":
        # Right angle at top requires different approach
        vertices = [
            Point2D(-base / 2, -height / 3),
            Point2D(base / 2, -height / 3),
            Point2D(0, 2 * height / 3)
        ]
        return FlexibleTriangle(center=center, vertices=vertices, **kwargs)
    else:
        raise ValueError(f"Invalid right_angle_position: {right_angle_position}")

    return FlexibleTriangle(
        center=center,
        angle_left=angle_left,
        angle_right=angle_right,
        base_width=base,
        rotation=rotation,
        **kwargs
    )


def create_isosceles_triangle(
        center: Union[Point2D, Point3D],
        base: float,
        height: float,
        **kwargs
) -> FlexibleTriangle:
    """Create an isosceles triangle"""
    return FlexibleTriangle(
        center=center,
        base_width=base,
        height=height,
        apex_offset=0,  # Centered apex
        **kwargs
    )


# Example usage
if __name__ == "__main__":
    # Example 1: Triangle defined by two angles and base
    triangle1 = FlexibleTriangle(
        center=Point2D(0, 0),
        angle_left=45,  # 45° angle at left vertex
        angle_right=60,  # 60° angle at right vertex
        base_width=50,  # 50 μm base
        filled=True,
        hatch_size=2.0
    )

    print("Triangle 1 (45°-60°-75°):")
    info = triangle1.get_info()
    print(f"  Area: {info['area']:.2f} μm²")
    print(f"  Angles: {info['angles']['A']:.1f}°, {info['angles']['B']:.1f}°, {info['angles']['C']:.1f}°")

    # Example 2: Right triangle
    triangle2 = create_right_triangle(
        center=Point2D(100, 0),
        base=40,
        height=30,
        right_angle_position="bottom_left",
        filled=True
    )

    print("\nTriangle 2 (Right triangle):")
    info2 = triangle2.get_info()
    print(f"  Area: {info2['area']:.2f} μm²")
    print(f"  Hypotenuse: {max(info2['sides'].values()):.2f} μm")

    # Example 3: Equilateral triangle
    triangle3 = FlexibleTriangle(
        center=Point2D(0, 100),
        equilateral_side=60,
        rotation=30,  # Rotated 30°
        filled=False
    )

    print("\nTriangle 3 (Equilateral, rotated 30°):")
    info3 = triangle3.get_info()
    print(f"  All sides: {info3['sides']['a']:.2f} μm")
    print(f"  All angles: {info3['angles']['A']:.1f}°")

    # Example 4: Triangle from three sides
    triangle4 = FlexibleTriangle(
        center=Point2D(100, 100),
        left_side=30,
        right_side=40,
        base_width=50,
        filled=True,
        hatch_size=1.5
    )

    print("\nTriangle 4 (From three sides: 30, 40, 50):")
    info4 = triangle4.get_info()
    print(f"  Is right triangle? {abs(info4['angles']['C'] - 90) < 0.1}")
    print(f"  Angles: {info4['angles']['A']:.1f}°, {info4['angles']['B']:.1f}°, {info4['angles']['C']:.1f}°")