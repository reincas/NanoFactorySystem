##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# The class Locator.
#
##########################################################################

import logging
import random

from ..parameter import Interface, Result, flex_round

class Locator:

    def __init__(self, z, dz, zmin, zmax, interface, beta, jitter, resolution, logger=None):

        # Store logger
        self.log = logger or logging

        self.z = float(z)
        self.dz = abs(float(dz))
        self.zmin = float(zmin)
        self.zmax = float(zmax)
        assert (self.zmin < self.zmax)
        assert (self.z > self.zmin and self.z < self.zmax)
        assert (self.dz < self.zmax - self.zmin)

        assert (isinstance(interface, Interface))
        self.interface = interface

        self.beta = abs(float(beta))
        assert (self.beta >= 0.5 and self.beta < 1.0)

        jitter = abs(float(jitter))
        assert (jitter >= 0 and jitter < 1.0)
        self.jitter = jitter * (1.0 - self.beta)

        self.resolution = abs(float(resolution))

        self.z_start = self.z
        self.dz_start = self.dz

    def clip(self, z):

        """ Clip given position to a value in the range [self.zmin, self.zmax]. """

        assert (self.zmax > self.zmin)
        z = float(z)
        z = min(self.zmax, z)
        z = max(self.zmin, z)
        return z

    def __iter__(self):

        """ Return iterator object. """

        return self

    def __next__(self):

        """ Yield next scan parameters. """

        if self.finished:
            raise StopIteration

        z = self.z + random.uniform(-0.5, 0.5) * self.jitter * self.dz
        if self.interface == Interface.LOW:
            z_low = self.clip(self.z - self.beta * self.dz)
            z_high = z
        else:
            z_low = z
            z_high = self.clip(self.z + self.beta * self.dz)

        z = 0.5 * (z_high + z_low)
        dz = z_high - z_low
        return z, dz

    def other_range(self, z, dz):

        if self.interface == Interface.LOW:
            z_low = z + 0.5*dz
            z_high = self.clip(self.z + self.beta * self.dz)
        else:
            z_low = self.clip(self.z - self.beta * self.dz)
            z_high = z - 0.5*dz

        z = 0.5 * (z_high + z_low)
        dz = z_high - z_low
        return z, dz

    def register(self, z, dz, result):

        """ Replace current by scanned range in case of a detected focus, replace by
        other range, if no focus was detected. Nothing is changed in case of an
        ambiguous result. """

        if result == Result.HIT:
            self.z, self.dz = z, dz
        elif result == Result.MISS:
            self.z, self.dz = self.other_range(z, dz)

    def status(self):

        """ Return human-readable status string. """

        return "%g [%g]" % flex_round(self.z, self.dz)

    def __str__(self):

        """ Return human-readable object representation. """

        return self.status()

    @property
    def finished(self):

        return self.dz <= self.resolution

    def result(self):

        """ Return the location result dictionary. """

        assert (self.finished)

        return {
            "zStart": self.z_start,
            "dzStart": self.dz_start,
            "zMin": self.zmin,
            "zMax": self.zmax,
            "z": self.z,
            "dz": self.dz,
            "interface": self.interface.name.lower(),
            "beta": self.beta,
            "jitter": self.jitter,
            "resolution": self.resolution,
        }
