##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# The class Locator which is used for a fine localisation of the low or
# high interface of the photoresin layer on a sample substrate in the Laser
# Nanofactory system.
#
##########################################################################

import logging
import random

from ..parameter import Interface, Result, flex_round

class Locator:

    """ Fine resin layer interface locator class. This iterator class will deliver parameter
    tuples z,dz for external laser scan and focus detection. The result (hit, miss, or ambiguous)
    of each focus detection must be registered using the method register(). The detection starts
    at a given initial z range containing the requested interface and uses a modified bisection
    algorithm to reduce the uncertainty range dz until it reaches a given resolution. Before each
    step, the z range is increased by a factor based on the parameter beta (0.5 = standard bisection,
    1.0 = no reduction). In contrast to the standard algorithm, this allows it to recover from
    dectection errors. """

    def __init__(self, z, dz, zmin, zmax, interface, beta, jitter, resolution, logger=None):

        """ Initialize a Locator object. """

        # Store logger
        self.log = logger or logging

        # Initial scanning parameters and scan range limits
        self.z = float(z)
        self.dz = abs(float(dz))
        self.zmin = float(zmin)
        self.zmax = float(zmax)
        assert (self.zmin < self.zmax)
        assert (self.z > self.zmin and self.z < self.zmax)
        assert (self.dz < self.zmax - self.zmin)

        # Resin layer interface to be detected (low or high)
        assert (isinstance(interface, Interface))
        assert (interface == Interface.LOW or interface == Interface.HIGH)
        self.interface = interface

        # Expansion factor for the stabilized bisection algorithm
        self.beta = abs(float(beta))
        assert (self.beta >= 0.5 and self.beta < 1.0)

        # Jitter factor for scanning positions relative to beta
        jitter = abs(float(jitter))
        assert (jitter >= 0 and jitter < 1.0)
        self.jitter = jitter * (self.beta - 0.5)

        # Upper limit for the uncertainty of the interface position
        self.resolution = abs(float(resolution))

        # Store initial scanning parameters as meta-data
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

        """ Yield next scan parameters using a modified bisection algorithm. Instead
        of just splitting the current range in two parts, the current range is expanded
        based on the factor beta."""

        if self.finished:
            raise StopIteration

        # Add jitter to current range center
        z = self.z + random.uniform(-0.5, 0.5) * self.jitter * self.dz

        # In case of low interface scan the lower half of the current range
        if self.interface == Interface.LOW:
            z_low = self.clip(self.z - self.beta * self.dz)
            z_high = z

        # In case of high interface scan the upper half of the current range
        else:
            z_low = z
            z_high = self.clip(self.z + self.beta * self.dz)

        # Yield the next scan parameters
        z = 0.5 * (z_high + z_low)
        dz = z_high - z_low
        yield z, dz

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

        return f"Locator({self.interface.name.lower()}): {self.status()}"

    @property
    def finished(self):

        """ True, if the uncertainty range of the interface position is less
        or equal the requested resolution. """

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
