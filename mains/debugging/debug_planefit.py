import matplotlib.pyplot as plt
import numpy as np
from scidatacontainer import Container

from nanofactorysystem import PlaneFit

plane_dc_path = "../.output/dhm_paper/20240622_PARAMETER_2/plane.zdc"
dc = Container(file=str(plane_dc_path))

lower_points = np.asarray(dc["meas/result.json"]["lower"]["points"])
upper_points = np.asarray(dc["meas/result.json"]["upper"]["points"])

x_min, y_min = np.stack([lower_points, upper_points]).min(axis=(0,1))[:2]
x_max, y_max = np.stack([lower_points, upper_points]).max(axis=(0,1))[:2]
print(x_min, x_max, y_min, y_max)

lower_plane = PlaneFit(lower_points)
upper_plane = PlaneFit(upper_points)

x = np.linspace(x_min, x_max, 10)
y = np.linspace(y_min, y_max, 10)
x, y = np.meshgrid(x, y)

# Compute the z values
z_lower_plane = np.vectorize(lower_plane.getz)(x, y)
z_upper_plane = np.vectorize(upper_plane.getz)(x, y)

# Plot the surface
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(*lower_points.T, label="Lower points")
ax.scatter(*upper_points.T, label="Upper points")
ax.plot_surface(x, y, z_upper_plane, cmap='viridis')
ax.plot_surface(x, y, z_lower_plane, cmap='viridis')
plt.legend()

plt.tight_layout()
plt.show()