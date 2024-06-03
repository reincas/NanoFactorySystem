import os
from unittest import TestCase

from nanofactorysystem.devices.aerotech import Aerotech3200


class FemtikaTest(TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("EXECUTE_FEMTIKA_TESTS", None):
            raise RuntimeError("EXECUTE_FEMTIKA_TESTS not set. Skipping these tests")

    def setUp(self):
        self.a3200 = Aerotech3200()
        self.api = self.a3200.api
        self.api.connect()

    def tearDown(self):
        self.api.close()

        print("Commands:")
        for cmd in self.api.history:
            print(cmd)
