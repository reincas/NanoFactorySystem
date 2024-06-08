import math
from typing import Optional


# def circle_line_intersection1(
#         p1: tuple[float, float],
#         p2: tuple[float, float],
#         circle_center: tuple[float, float],
#         radius: float
# ) -> tuple[Optional[tuple[float, float]], Optional[tuple[float, float]], float]:
#     # https://mathworld.wolfram.com/Circle-LineIntersection.html
#     circle_center = np.asarray(circle_center)
#     x1, y1 = - np.asarray(circle_center) + p1
#     x2, y2 = - np.asarray(circle_center) + p2
#
#     dx = x2 - x1
#     dy = y2 - y1
#     dr = math.sqrt(dx ** 2 + dy ** 2)
#     determinant = x1 * y2 - x2 * y1
#     discriminant = radius ** 2 * dr ** 2 - determinant ** 2
#
#     intersection_1 = None
#     intersection_2 = None
#     dr2 = dr ** 2
#     prefactor_x, prefactor_y = (determinant * dy) / dr2, (- determinant * dx) / dr2
#     if discriminant == 0:
#         intersection_1 = prefactor_x, prefactor_y
#     else:
#         sqrt_part = math.sqrt((radius**2) * dr2 - (determinant ** 2))
#         sgn = lambda x: -1 if x < 0 else 1
#         x_part = sgn(dy) * dx * sqrt_part / dr2
#         y_part = abs(dy) * sqrt_part / dr2
#         intersection_1 = prefactor_x + x_part, prefactor_y + y_part
#         intersection_2 = prefactor_x - x_part, prefactor_y - y_part
#
#     return intersection_1, intersection_2, discriminant

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
