import math
from typing import Optional


def _line_circle_intersection(
        r: float, a: float, b: float, c: float
) -> tuple[int, Optional[tuple[float, float]], Optional[tuple[float, float]]]:
    """
    Determines the points of intersection between a circle and a line.

    Source: https://cp-algorithms.com/geometry/circle-line-intersection.html

    :param r: The radius of the circle (assuming center is at 0/0)
    :param a: The coefficient of x in the line equation ax + by + c = 0.
    :param b: The coefficient of y in the line equation ax + by + c = 0.
    :param c: The constant term in the line equation ax + by + c = 0.
    :returns:
        - number of intersection points (0, 1, 2)
        - (x, y) first intersection
        - (x, y) second intersection
    """
    EPS = 1e-9
    x0 = -a * c / (a * a + b * b)
    y0 = -b * c / (a * a + b * b)

    if c * c > r * r * (a * a + b * b) + EPS:
        return 0, None, None
    elif abs(c * c - r * r * (a * a + b * b)) < EPS:
        return 1, (x0, y0), None
    else:
        d = r * r - c * c / (a * a + b * b)
        mult = math.sqrt(d / (a * a + b * b))
        ax = x0 + b * mult
        bx = x0 - b * mult
        ay = y0 - a * mult
        by = y0 + a * mult
        return 2, (ax, ay), (bx, by)


def line_circle_intersection(
        p1: tuple[float, float],
        p2: tuple[float, float],
        circle_center: tuple[float, float],
        radius: float
) -> tuple[int, Optional[tuple[float, float]], Optional[tuple[float, float]]]:
    # Convert line segment points to line equation coefficients a, b, c
    x1, y1 = p1
    x2, y2 = p2

    # Adjust points according to the circle center
    x1 -= circle_center[0]
    y1 -= circle_center[1]
    x2 -= circle_center[0]
    y2 -= circle_center[1]

    a = y2 - y1
    b = x2 - x1
    c = x2 * y1 - x1 * y2

    n, intersection_1, intersection_2 = _line_circle_intersection(radius, a, b, c)

    if intersection_1 is not None:
        intersection_1 = (intersection_1[0] + circle_center[0], intersection_1[1] + circle_center[1])

    if intersection_2 is not None:
        intersection_2 = (intersection_2[0] + circle_center[0], intersection_2[1] + circle_center[1])

    if intersection_1 == intersection_2:
        intersection_2 = None
        n -= 1

    return n, intersection_1, intersection_2


def get_grid_coordinates(
        x0: float,
        y0: float,
        dx: float = 80.0,
        dy: float = 80.0,
        nx: int = 2,
        ny: int = 2,
) -> list[tuple[float, float]]:
    coordinates = []
    for j in range(ny):
        for i in range(nx):
            x = x0 + i * dx
            y = y0 + j * dy
            coordinates.append((x, y))
    return coordinates
