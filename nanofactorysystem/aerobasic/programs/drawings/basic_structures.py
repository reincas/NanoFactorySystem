"""
Basic geometric structures for laser nanofabrication.

This module provides simple, fundamental geometric shapes:
- Square: Filled or outline square
- Rectangle: Filled or outline rectangle
- Circle: Filled or outline circle
- Triangle: Equilateral triangle (basic version)

For more advanced triangle variants, see triangle_flexible.py
"""

from typing import List
import numpy as np

from nanofactorysystem.devices.coordinate_system import Point3D


class Square:
    """
    A square structure with optional fill pattern.

    Parameters:
        center (Point3D): Center point of the square
        side_length (float): Length of each side in micrometers
        filled (bool): If True, fill with hatch pattern; if False, only draw outline
        hatch_size (float): Distance between hatch lines for filled squares (default: 1.0)
        velocity (float): Drawing velocity in µm/s (default: 10000)
        acceleration (float): Drawing acceleration in µm/s² (default: 50000)
        rotation (float): Rotation angle in degrees (default: 0)

    Example:
        >>> square = Square(
        ...     center=Point3D(0, 0, -2),
        ...     side_length=50,
        ...     filled=True,
        ...     hatch_size=1.0
        ... )
        >>> points = square.draw()

    Notes:
        - Square is centered at the given point
        - Hatch pattern alternates between X and Y directions for better structural integrity
        - For unfilled squares, only the perimeter is drawn
    """

    def __init__(
            self,
            center: Point3D,
            side_length: float,
            filled: bool = True,
            hatch_size: float = 1.0,
            velocity: float = 10000,
            acceleration: float = 50000,
            rotation: float = 0
    ):
        if side_length <= 0:
            raise ValueError(f"side_length must be positive, got {side_length}")
        if hatch_size <= 0:
            raise ValueError(f"hatch_size must be positive, got {hatch_size}")
        if velocity <= 0:
            raise ValueError(f"velocity must be positive, got {velocity}")
        if acceleration <= 0:
            raise ValueError(f"acceleration must be positive, got {acceleration}")

        self.center = center
        self.side_length = float(side_length)
        self.filled = filled
        self.hatch_size = float(hatch_size)
        self.velocity = float(velocity)
        self.acceleration = float(acceleration)
        self.rotation = float(rotation)

    def draw(self) -> List[Point3D]:
        """
        Generate the points for drawing the square.

        Returns:
            List[Point3D]: List of points defining the square structure
        """
        points = []
        half_side = self.side_length / 2

        if not self.filled:
            # Draw only the outline
            corners = [
                Point3D(-half_side, -half_side, self.center.z),
                Point3D(half_side, -half_side, self.center.z),
                Point3D(half_side, half_side, self.center.z),
                Point3D(-half_side, half_side, self.center.z),
                Point3D(-half_side, -half_side, self.center.z)  # Close the square
            ]

            # Apply rotation and translation
            for corner in corners:
                rotated = self._rotate_point(corner, self.rotation)
                points.append(rotated + self.center)
        else:
            # Fill with hatch pattern
            num_lines = int(np.ceil(self.side_length / self.hatch_size)) + 1

            # Horizontal hatch lines
            for i in range(num_lines):
                y = -half_side + i * self.hatch_size
                if y > half_side:
                    break

                # Alternate direction for smoother printing
                if i % 2 == 0:
                    start = Point3D(-half_side, y, self.center.z)
                    end = Point3D(half_side, y, self.center.z)
                else:
                    start = Point3D(half_side, y, self.center.z)
                    end = Point3D(-half_side, y, self.center.z)

                # Apply rotation and translation
                start_rot = self._rotate_point(start, self.rotation) + self.center
                end_rot = self._rotate_point(end, self.rotation) + self.center

                # Mark laser off before line, on during line, off after
                start_rot.laser_off = True
                points.append(start_rot)
                points.append(end_rot)
                end_rot.laser_off = True
                points.append(end_rot)

        return points

    def _rotate_point(self, point: Point3D, angle_deg: float) -> Point3D:
        """Rotate a point around origin by angle_deg degrees."""
        if angle_deg == 0:
            return point

        angle_rad = np.radians(angle_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)

        x_rot = point.x * cos_a - point.y * sin_a
        y_rot = point.x * sin_a + point.y * cos_a

        return Point3D(x_rot, y_rot, point.z)

    @property
    def bounding_box(self):
        """Return (min_x, max_x, min_y, max_y) of the square."""
        half = self.side_length / 2
        return (
            self.center.x - half,
            self.center.x + half,
            self.center.y - half,
            self.center.y + half
        )


class Rectangle:
    """
    A rectangular structure with optional fill pattern.

    Parameters:
        center (Point3D): Center point of the rectangle
        width (float): Width (X direction) in micrometers
        height (float): Height (Y direction) in micrometers
        filled (bool): If True, fill with hatch pattern; if False, only draw outline
        hatch_size (float): Distance between hatch lines for filled rectangles (default: 1.0)
        velocity (float): Drawing velocity in µm/s (default: 10000)
        acceleration (float): Drawing acceleration in µm/s² (default: 50000)
        rotation (float): Rotation angle in degrees (default: 0)

    Example:
        >>> rect = Rectangle(
        ...     center=Point3D(0, 0, -2),
        ...     width=80,
        ...     height=40,
        ...     filled=True,
        ...     hatch_size=0.5
        ... )
        >>> points = rect.draw()

    Notes:
        - Rectangle is centered at the given point
        - Width is along X-axis, height along Y-axis before rotation
        - For width == height, behaves identically to Square
    """

    def __init__(
            self,
            center: Point3D,
            width: float,
            height: float,
            filled: bool = True,
            hatch_size: float = 1.0,
            velocity: float = 10000,
            acceleration: float = 50000,
            rotation: float = 0
    ):
        if width <= 0:
            raise ValueError(f"width must be positive, got {width}")
        if height <= 0:
            raise ValueError(f"height must be positive, got {height}")
        if hatch_size <= 0:
            raise ValueError(f"hatch_size must be positive, got {hatch_size}")
        if velocity <= 0:
            raise ValueError(f"velocity must be positive, got {velocity}")
        if acceleration <= 0:
            raise ValueError(f"acceleration must be positive, got {acceleration}")

        self.center = center
        self.width = float(width)
        self.height = float(height)
        self.filled = filled
        self.hatch_size = float(hatch_size)
        self.velocity = float(velocity)
        self.acceleration = float(acceleration)
        self.rotation = float(rotation)

    def draw(self) -> List[Point3D]:
        """
        Generate the points for drawing the rectangle.

        Returns:
            List[Point3D]: List of points defining the rectangle structure
        """
        points = []
        half_width = self.width / 2
        half_height = self.height / 2

        if not self.filled:
            # Draw only the outline
            corners = [
                Point3D(-half_width, -half_height, self.center.z),
                Point3D(half_width, -half_height, self.center.z),
                Point3D(half_width, half_height, self.center.z),
                Point3D(-half_width, half_height, self.center.z),
                Point3D(-half_width, -half_height, self.center.z)  # Close
            ]

            for corner in corners:
                rotated = self._rotate_point(corner, self.rotation)
                points.append(rotated + self.center)
        else:
            # Fill with hatch pattern
            num_lines = int(np.ceil(self.height / self.hatch_size)) + 1

            for i in range(num_lines):
                y = -half_height + i * self.hatch_size
                if y > half_height:
                    break

                # Alternate direction
                if i % 2 == 0:
                    start = Point3D(-half_width, y, self.center.z)
                    end = Point3D(half_width, y, self.center.z)
                else:
                    start = Point3D(half_width, y, self.center.z)
                    end = Point3D(-half_width, y, self.center.z)

                start_rot = self._rotate_point(start, self.rotation) + self.center
                end_rot = self._rotate_point(end, self.rotation) + self.center

                start_rot.laser_off = True
                points.append(start_rot)
                points.append(end_rot)
                end_rot.laser_off = True
                points.append(end_rot)

        return points

    def _rotate_point(self, point: Point3D, angle_deg: float) -> Point3D:
        """Rotate a point around origin by angle_deg degrees."""
        if angle_deg == 0:
            return point

        angle_rad = np.radians(angle_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)

        x_rot = point.x * cos_a - point.y * sin_a
        y_rot = point.x * sin_a + point.y * cos_a

        return Point3D(x_rot, y_rot, point.z)

    @property
    def bounding_box(self):
        """Return (min_x, max_x, min_y, max_y) of the rectangle."""
        half_w = self.width / 2
        half_h = self.height / 2
        return (
            self.center.x - half_w,
            self.center.x + half_w,
            self.center.y - half_h,
            self.center.y + half_h
        )


class Circle:
    """
    A circular structure with optional fill pattern.

    Parameters:
        center (Point3D): Center point of the circle
        radius (float): Radius in micrometers
        filled (bool): If True, fill with hatch pattern; if False, only draw outline
        hatch_size (float): Distance between hatch lines for filled circles (default: 1.0)
        resolution (int): Number of points for circle outline (default: 100)
        velocity (float): Drawing velocity in µm/s (default: 10000)
        acceleration (float): Drawing acceleration in µm/s² (default: 50000)

    Example:
        >>> circle = Circle(
        ...     center=Point3D(0, 0, -2),
        ...     radius=25,
        ...     filled=True,
        ...     hatch_size=0.5,
        ...     resolution=120
        ... )
        >>> points = circle.draw()

    Notes:
        - Higher resolution = smoother circle but more points
        - For small circles (r < 10), use resolution >= 50
        - For large circles (r > 50), resolution = 100-200 is sufficient
        - Hatch pattern uses horizontal lines clipped to circle boundary
    """

    def __init__(
            self,
            center: Point3D,
            radius: float,
            filled: bool = True,
            hatch_size: float = 1.0,
            resolution: int = 100,
            velocity: float = 10000,
            acceleration: float = 50000
    ):
        if radius <= 0:
            raise ValueError(f"radius must be positive, got {radius}")
        if hatch_size <= 0:
            raise ValueError(f"hatch_size must be positive, got {hatch_size}")
        if resolution < 3:
            raise ValueError(f"resolution must be >= 3, got {resolution}")
        if velocity <= 0:
            raise ValueError(f"velocity must be positive, got {velocity}")
        if acceleration <= 0:
            raise ValueError(f"acceleration must be positive, got {acceleration}")

        self.center = center
        self.radius = float(radius)
        self.filled = filled
        self.hatch_size = float(hatch_size)
        self.resolution = int(resolution)
        self.velocity = float(velocity)
        self.acceleration = float(acceleration)

    def draw(self) -> List[Point3D]:
        """
        Generate the points for drawing the circle.

        Returns:
            List[Point3D]: List of points defining the circle structure
        """
        points = []

        if not self.filled:
            # Draw only the outline
            angles = np.linspace(0, 2 * np.pi, self.resolution, endpoint=True)
            for angle in angles:
                x = self.center.x + self.radius * np.cos(angle)
                y = self.center.y + self.radius * np.sin(angle)
                points.append(Point3D(x, y, self.center.z))
        else:
            # Fill with horizontal hatch lines
            num_lines = int(np.ceil(2 * self.radius / self.hatch_size)) + 1

            for i in range(num_lines):
                y = -self.radius + i * self.hatch_size
                if y > self.radius:
                    break

                # Calculate intersection points with circle
                # Circle equation: x² + y² = r²
                # For given y: x = ±√(r² - y²)
                discriminant = self.radius ** 2 - y ** 2
                if discriminant < 0:
                    continue  # No intersection

                x_offset = np.sqrt(discriminant)

                # Alternate direction
                if i % 2 == 0:
                    start_x = -x_offset
                    end_x = x_offset
                else:
                    start_x = x_offset
                    end_x = -x_offset

                start = Point3D(
                    self.center.x + start_x,
                    self.center.y + y,
                    self.center.z
                )
                end = Point3D(
                    self.center.x + end_x,
                    self.center.y + y,
                    self.center.z
                )

                start.laser_off = True
                points.append(start)
                points.append(end)
                end.laser_off = True
                points.append(end)

        return points

    @property
    def bounding_box(self):
        """Return (min_x, max_x, min_y, max_y) of the circle."""
        return (
            self.center.x - self.radius,
            self.center.x + self.radius,
            self.center.y - self.radius,
            self.center.y + self.radius
        )


class Triangle:
    """
    An equilateral triangle (all sides equal length).

    This is a basic implementation. For more flexibility (different angles,
    right triangles, etc.), use FlexibleTriangle from triangle_flexible.py

    Parameters:
        center (Point3D): Center point of the triangle
        side_length (float): Length of each side in micrometers
        filled (bool): If True, fill with hatch pattern; if False, only draw outline
        hatch_size (float): Distance between hatch lines for filled triangles (default: 1.0)
        orientation (str): Triangle orientation - 'up' or 'down' (default: 'up')
        velocity (float): Drawing velocity in µm/s (default: 10000)
        acceleration (float): Drawing acceleration in µm/s² (default: 50000)
        rotation (float): Additional rotation in degrees (default: 0)

    Example:
        >>> triangle = Triangle(
        ...     center=Point3D(0, 0, -2),
        ...     side_length=40,
        ...     filled=True,
        ...     hatch_size=0.5,
        ...     orientation='up'
        ... )
        >>> points = triangle.draw()

    Notes:
        - This creates an equilateral triangle (60° angles)
        - 'up' orientation: apex points upward (▲)
        - 'down' orientation: apex points downward (▼)
        - For other triangle types, use FlexibleTriangle
    """

    def __init__(
            self,
            center: Point3D,
            side_length: float,
            filled: bool = True,
            hatch_size: float = 1.0,
            orientation: str = 'up',
            velocity: float = 10000,
            acceleration: float = 50000,
            rotation: float = 0
    ):
        if side_length <= 0:
            raise ValueError(f"side_length must be positive, got {side_length}")
        if hatch_size <= 0:
            raise ValueError(f"hatch_size must be positive, got {hatch_size}")
        if orientation not in ['up', 'down']:
            raise ValueError(f"orientation must be 'up' or 'down', got {orientation}")
        if velocity <= 0:
            raise ValueError(f"velocity must be positive, got {velocity}")
        if acceleration <= 0:
            raise ValueError(f"acceleration must be positive, got {acceleration}")

        self.center = center
        self.side_length = float(side_length)
        self.filled = filled
        self.hatch_size = float(hatch_size)
        self.orientation = orientation
        self.velocity = float(velocity)
        self.acceleration = float(acceleration)
        self.rotation = float(rotation)

        # Calculate triangle geometry
        # Equilateral triangle: height = side * sqrt(3)/2
        self.height = self.side_length * np.sqrt(3) / 2

    def _get_vertices(self) -> List[Point3D]:
        """Calculate the three vertices of the equilateral triangle."""
        # Base vertices (before rotation)
        if self.orientation == 'up':
            # Apex at top
            vertices = [
                Point3D(0, self.height * 2 / 3, self.center.z),  # Top apex
                Point3D(-self.side_length / 2, -self.height / 3, self.center.z),  # Bottom left
                Point3D(self.side_length / 2, -self.height / 3, self.center.z),  # Bottom right
            ]
        else:  # 'down'
            # Apex at bottom
            vertices = [
                Point3D(0, -self.height * 2 / 3, self.center.z),  # Bottom apex
                Point3D(-self.side_length / 2, self.height / 3, self.center.z),  # Top left
                Point3D(self.side_length / 2, self.height / 3, self.center.z),  # Top right
            ]

        # Apply rotation if needed
        if self.rotation != 0:
            vertices = [self._rotate_point(v, self.rotation) for v in vertices]

        # Translate to center
        return [v + self.center for v in vertices]

    def draw(self) -> List[Point3D]:
        """
        Generate the points for drawing the triangle.

        Returns:
            List[Point3D]: List of points defining the triangle structure
        """
        points = []
        vertices = self._get_vertices()

        if not self.filled:
            # Draw only the outline
            points.extend(vertices)
            points.append(vertices[0])  # Close the triangle
        else:
            # Fill with horizontal hatch lines
            # Get y-bounds
            y_coords = [v.y for v in vertices]
            y_min = min(y_coords)
            y_max = max(y_coords)

            num_lines = int(np.ceil((y_max - y_min) / self.hatch_size)) + 1

            for i in range(num_lines):
                y = y_min + i * self.hatch_size
                if y > y_max:
                    break

                # Find intersection points with triangle edges
                intersections = self._get_line_intersections(y, vertices)

                if len(intersections) >= 2:
                    # Sort by x-coordinate
                    intersections.sort(key=lambda p: p.x)

                    # Alternate direction
                    if i % 2 == 0:
                        start, end = intersections[0], intersections[-1]
                    else:
                        start, end = intersections[-1], intersections[0]

                    start.laser_off = True
                    points.append(start)
                    points.append(end)
                    end.laser_off = True
                    points.append(end)

        return points

    def _get_line_intersections(self, y: float, vertices: List[Point3D]) -> List[Point3D]:
        """Find where a horizontal line at y intersects the triangle edges."""
        intersections = []

        # Check each edge
        for i in range(3):
            v1 = vertices[i]
            v2 = vertices[(i + 1) % 3]

            # Check if edge crosses the y line
            if min(v1.y, v2.y) <= y <= max(v1.y, v2.y):
                # Avoid duplicate points at vertices
                if v1.y == y:
                    intersections.append(v1)
                elif v2.y == y:
                    intersections.append(v2)
                elif v1.y != v2.y:
                    # Linear interpolation to find x
                    t = (y - v1.y) / (v2.y - v1.y)
                    x = v1.x + t * (v2.x - v1.x)
                    intersections.append(Point3D(x, y, self.center.z))

        return intersections

    def _rotate_point(self, point: Point3D, angle_deg: float) -> Point3D:
        """Rotate a point around origin by angle_deg degrees."""
        angle_rad = np.radians(angle_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)

        x_rot = point.x * cos_a - point.y * sin_a
        y_rot = point.x * sin_a + point.y * cos_a

        return Point3D(x_rot, y_rot, point.z)

    @property
    def bounding_box(self):
        """Return (min_x, max_x, min_y, max_y) of the triangle."""
        vertices = self._get_vertices()
        x_coords = [v.x for v in vertices]
        y_coords = [v.y for v in vertices]
        return (
            min(x_coords),
            max(x_coords),
            min(y_coords),
            max(y_coords)
        )


# Helper functions for quick structure creation

def create_square(center: Point3D, side: float, **kwargs) -> Square:
    """Convenience function to create a square."""
    return Square(center=center, side_length=side, **kwargs)


def create_rectangle(center: Point3D, width: float, height: float, **kwargs) -> Rectangle:
    """Convenience function to create a rectangle."""
    return Rectangle(center=center, width=width, height=height, **kwargs)


def create_circle(center: Point3D, radius: float, **kwargs) -> Circle:
    """Convenience function to create a circle."""
    return Circle(center=center, radius=radius, **kwargs)


def create_triangle(center: Point3D, side: float, **kwargs) -> Triangle:
    """Convenience function to create an equilateral triangle."""
    return Triangle(center=center, side_length=side, **kwargs)


# Example usage and testing
if __name__ == '__main__':
    # Test all basic structures
    center = Point3D(0, 0, -2)

    print("Testing basic structures...")

    # Square
    square = Square(center=center, side_length=50, filled=True, hatch_size=1.0)
    square_points = square.draw()
    print(f"Square: {len(square_points)} points")

    # Rectangle
    rect = Rectangle(center=center, width=80, height=40, filled=True, hatch_size=1.0)
    rect_points = rect.draw()
    print(f"Rectangle: {len(rect_points)} points")

    # Circle
    circle = Circle(center=center, radius=25, filled=True, hatch_size=0.5)
    circle_points = circle.draw()
    print(f"Circle: {len(circle_points)} points")

    # Triangle
    triangle = Triangle(center=center, side_length=40, filled=True, hatch_size=0.5)
    triangle_points = triangle.draw()
    print(f"Triangle: {len(triangle_points)} points")

    print("\nAll structures created successfully!")