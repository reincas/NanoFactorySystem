import numpy as np
from skimage import measure


'''
def intersect_line_with_segment(p0, d, a, b):
    """ Schnittpunkt einer unendlichen Linie p0 + t d
        mit Segment a→b. Gibt t zurück oder None. """

    v = b - a
    M = np.array([d, -v]).T  # d * t + v * u = (a - p0)

    try:
        sol = np.linalg.solve(M, a - p0)
    except np.linalg.LinAlgError:
        return None

    t, u = sol
    if 0 <= u <= 1:
        return t
    return None


def hatch_segments_for_polygon(polygon, hatch_deg, hatch_dist, z):
    """Erzeugt Hatch-Segmente aus einem 2D-Polygon für Winkel θ."""

    poly = np.array(polygon)
    angle = np.deg2rad(hatch_deg)

    # Linienrichtung
    d = np.array([np.cos(angle), np.sin(angle)])

    # Normalenrichtung (Abstand)
    n = np.array([-np.sin(angle), np.cos(angle)])

    # Bounding Box zur Erfassung des Scan-Bereichs
    x_min, y_min = poly.min(axis=0)
    x_max, y_max = poly.max(axis=0)
    diag = np.linalg.norm([x_max-x_min, y_max-y_min])

    # edges
    edges = [(poly[i], poly[(i+1) % len(poly)]) for i in range(len(poly))]

    # Verschiebungen entlang Normalenrichtung
    num_lines = int(diag / hatch_dist) + 3
    offsets = np.linspace(-diag, diag, num_lines)

    result_segments = []

    for s in offsets:

        # Basispunkt der Linie (weit außerhalb der Bounding Box)
        p0 = np.array([0.0, 0.0]) + n*s - d*diag

        # Schnittparameter mit Kanten sammeln
        ts = []
        for a, b in edges:
            t = intersect_line_with_segment(p0, d, a, b)
            if t is not None:
                ts.append(t)

        if len(ts) < 2:
            continue

        # Sortieren + Duplikate entfernen
        ts.sort()
        # ts = sorted(ts)
        filtered_ts = []
        eps = 1e-9
        for t in ts:
            if not filtered_ts or abs(t - filtered_ts[-1]) > eps:
                filtered_ts.append(t)
        ts = filtered_ts

        # Paarweise Segmente bilden
        for i in range(0, len(ts)-1, 2):
            t0, t1 = ts[i], ts[i+1]

            p_start = p0 + t0*d
            p_end   = p0 + t1*d

            # minimale Länge filtern
            # if np.linalg.norm(p_end - p_start) < 1e-12:
            #     continue

            result_segments.append(
                ( (p_start[0], p_start[1], z),
                  (p_end[0],   p_end[1],   z) )
            )

    return result_segments
'''


def intersect_line_with_segment(p0, d, a, b):
    """
    Schnittpunkt einer unendlichen Linie p(t) = p0 + t*d
    mit dem Segment a->b.
    Gibt t zurück (Parameter auf der Linie) oder None.
    """
    v = b - a
    M = np.array([[d[0], -v[0]],
                  [d[1], -v[1]]])

    rhs = a - p0
    det = np.linalg.det(M)

    if abs(det) < 1e-12:
        return None  # parallel

    ts = np.linalg.solve(M, rhs)
    t, s = ts[0], ts[1]

    if 0 <= s <= 1:
        return t
    return None


def hatch_segments_for_polygon(polygon, hatch_angle_deg, hatch_dist, z):
    """
    polygon: Nx2 array der Polygonecken (geschlossen!)
    hatch_angle_deg: Richtung der Hatch-Linien
    hatch_dist: Abstand zwischen Linien
    z: aktuelle Z-Schicht
    """
    poly = np.array(polygon)
    x_min, y_min = poly.min(axis=0)
    x_max, y_max = poly.max(axis=0)

    theta = np.deg2rad(hatch_angle_deg)
    d = np.array([np.cos(theta), np.sin(theta)])   # Richtungsvektor der Hatch-Linie
    n = np.array([-d[1], d[0]])                    # Normalvektor

    # Bestimme Projektions-Bereich in Richtung n
    proj_min = np.dot([x_min, y_min], n)
    proj_max = np.dot([x_max, y_max], n)

    # Erzeuge Offsets der Hatch-Linien
    offsets = np.arange(proj_min - hatch_dist,
                        proj_max + hatch_dist,
                        hatch_dist)

    result_segments = []

    # Alle Kanten des Polygons
    edges = [(poly[i], poly[(i+1) % len(poly)]) for i in range(len(poly))]

    for off in offsets:
        # Punkt p0 der Hatch-Linie: alle Punkte mit p•n = off
        # Finde einen Punkt darauf (Parameter t irrelevant)
        p0 = n * off  # Punkt auf der Linie

        # Schnittpunkte mit Polygon
        ts = []
        for a, b in edges:
            t = intersect_line_with_segment(p0, d, a, b)
            if t is not None:
                ts.append(t)

        if len(ts) < 2:
            continue

        ts.sort()

        # Paare (t0, t1), (t2, t3), ...
        for i in range(0, len(ts)-1, 2):
            t0, t1 = ts[i], ts[i+1]

            p_start = p0 + t0 * d
            p_end   = p0 + t1 * d

            result_segments.append(((p_start[0], p_start[1], z),
                                    (p_end[0],   p_end[1],   z)))

    return result_segments



def projection_s(x, y, phi, xc=0.0, yc=0.0):
    xt = x - xc
    yt = y - yc
    return xt*np.cos(phi) + yt*np.sin(phi)


def square_wave_xy(x, y, T, L1, phi=0, xc=0, yc=0, phase_shift=0,
                   amplitude=1, z0=0, centered=False):

    s = projection_s(x, y, phi, xc, yc)
    frac = np.mod(s - phase_shift, T) / T
    duty = L1 / T

    step = (frac < duty).astype(float)

    if centered:
        return z0 + amplitude * (2*step - 1) / 2
    else:
        return z0 + amplitude * step


def analytic_to_polygon(f, x_range, y_range, res=500, threshold=0.5):
    xs = np.linspace(x_range[0], x_range[1], res)
    ys = np.linspace(y_range[0], y_range[1], res)
    X, Y = np.meshgrid(xs, ys)

    Z = f(X, Y)

    contours = measure.find_contours(Z, threshold)

    polygons = []
    for c in contours:
        poly = []
        for yi, xi in c:
            # Proper coordinate interpolation
            x_coord = xs[0] + (xs[-1] - xs[0]) * (xi / (res - 1))
            y_coord = ys[0] + (ys[-1] - ys[0]) * (yi / (res - 1))
            poly.append([x_coord, y_coord])

        polygons.append(np.array(poly))

    return polygons


def visualize_example(phi=0):
    import matplotlib.pyplot as plt
    # ===== visualization code =====

    # Create grid
    N = 600
    x = np.linspace(-5, 5, N)
    y = np.linspace(-5, 5, N)
    X, Y = np.meshgrid(x, y)

    # Parameters for the square wave
    T = 2.0  # period
    L1 = 1.0  # "on" region width
    # phi = np.pi / 6  # rotation angle
    phase_shift = 0
    centered = True

    Z = square_wave_xy(X, Y, T, L1, phi=phi, phase_shift=phase_shift, centered=centered)

    # Plot
    plt.figure(figsize=(7, 6))
    plt.imshow(Z, extent=[x.min(), x.max(), y.min(), y.max()],
               origin='lower', cmap='viridis', aspect='equal')
    plt.colorbar(label="Amplitude")
    plt.title("2D Square Wave Pattern")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.show()

def make_square_wave_function(T, L1, phi=0, xc=0, yc=0, phase_shift=0,
                              amplitude=1, z0=0, centered=False):
    def f(x, y):
        return square_wave_xy(x, y, T, L1, phi, xc, yc, phase_shift,
                              amplitude, z0, centered)

    return f


if __name__ == '__main__':
    winkel=0

    visualize_example(phi=winkel)
    # Construct function f(x, y)
    f = make_square_wave_function(
        T=2.0,
        L1=1.0,
        phi=winkel,
        centered=True
    )

    # Create polygon(s)
    polygons = analytic_to_polygon(
        f,
        x_range=(-5, 5),
        y_range=(-5, 5),
        res=800,
        threshold=0.1  # contour level
    )

    # print(polygons)

    segments = []
    for poly in polygons:
        segs = hatch_segments_for_polygon(poly, 0, 0.5, z=0.5)
        segments.extend(segs)

    print("uupp")
