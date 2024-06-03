from unittest import TestCase

import numpy as np

from nanofactorysystem.devices.coordinate_system import PlaneFit

points = [
    [
        500.020392570227,
        19759.9893294082,
        25354.60805351914
    ],
    [
        800.0203925702269,
        19759.9893294082,
        25354.665721934143
    ],
    [
        1100.020392570227,
        19759.9893294082,
        25354.723390349147
    ],
    [
        500.020392570227,
        20059.9893294082,
        25354.78105876415
    ],
    [
        800.0203925702269,
        20059.9893294082,
        25354.66688417915
    ],
    [
        1100.020392570227,
        20059.9893294082,
        25354.95624566415
    ],
    [
        500.020392570227,
        20359.9893294082,
        25355.013914079154
    ],
    [
        800.0203925702269,
        20359.9893294082,
        25354.972009594152
    ],
    [
        1100.020392570227,
        20359.9893294082,
        25354.93010510915
    ]
]


class TestCoordinateSystem(TestCase):
    def test_planefit(self):
        planefit = PlaneFit.from_points(points)
        self.assertIsInstance(planefit.p0, np.ndarray)
        self.assertIsInstance(planefit.p1, np.ndarray)
        self.assertIsInstance(planefit.p2, np.ndarray)

        self.assertEqual(3, len(planefit.p0))
        self.assertEqual(3, len(planefit.p1))
        self.assertEqual(3, len(planefit.p2))

        self.assertIsInstance(planefit.average, float)
        self.assertIsInstance(planefit.max_dev, float)
        self.assertIsInstance(planefit.theta_degree, float)
        self.assertIsInstance(planefit.phi_degree, float)
        self.assertIsInstance(planefit.slope, float)
        self.assertIsInstance(str(planefit), str)
        print(str(planefit))
        print(planefit.parameters)
