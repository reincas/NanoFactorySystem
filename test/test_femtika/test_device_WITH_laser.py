import time
import unittest

from aerobasic import Axis, GalvoLaserOverrideMode, SingleAxis
from aerobasic.ascii import AerotechError
from . import FemtikaTest


class TestFemtikaNoLaser(FemtikaTest):

    def test_laser_override_commands_manual(self):
        self.api.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.ON)
        time.sleep(5)
        self.api.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.OFF)

    def test_laser_override_auto(self):
        self.api.ABSOLUTE()
        self.api.send("ACKNOWLEDGEALL\n")
        self.api.send("IFOV OFF\n")
        self.api.send("GALVO LASERONDELAY A 0\n")
        self.api.send("GALVO LASEROFFDELAY A 0\n")
        # self.api.send("GALVO LASER1PULSEWIDTH A 500000\n")
        # self.api.send("GALVO LASEROUTPUTPERIOD A 500000\n")
        self.api.send("GALVO LASERMODE A 0\n")
        self.api.send("IFOV AXISPAIR 0, A, X")
        self.api.send("IFOV AXISPAIR 1, B, Y")
        self.api.send("ENCODER OUT X ON 0,0")
        self.api.send("ENCODER OUT Y ON 0,0")
        self.api.send("IFOV SYNCAXES Z\n")
        self.api.send("IFOV SIZE 0.50000\n")
        self.api.send("IFOV TIME 10.00000\n")
        self.api.send("IFOV TRACKINGSPEED 500.00000\n")
        self.api.send("IFOV TRACKINGACCEL 500.00000")

        self.api.send("IFOV ON\n")

        # No Laser visible
        self.api.LINEAR(A=-5)
        self.api.LINEAR(A=0)

        # Activate
        self.api.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.AUTO)
        time.sleep(1)

        # Laser visible
        self.api.LINEAR(A=5)
