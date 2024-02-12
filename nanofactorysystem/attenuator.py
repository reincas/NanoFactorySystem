##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import struct
import numpy
from scipy.interpolate import interp1d
from scidatacontainer import Container, register, load_config

from .parameter import Parameter

# Register binary data calibration format
register("dat", "bin")

# Default location of laser calibration file
CALIBRATION = "C:\\Software\\3DPoli Fabrication\\Calibration\\Calibration.dat"


##########################################################################
class Attenuator(Parameter):

    """ Class for the laser attenuator of the Femtica Laser Nanofactory.
    It loads a calibration file and provides translation between
    attenuator value and laser power in both directions. """

    _defaults = {
        "fitKind": "cubic",
        "polynomialOrder": None,
        "valueMin": 0.0,
        "valueMax": 10.0,
        "powerMin": None,
        "powerMax": None,
        }
    
    def __init__(self, fn=None, logger=None, **kwargs):

        # Initialize parameter class
        super().__init__(logger, **kwargs)
        self.log.info("Initializing attenuator.")

        # SciData author configuration
        self.dc_config = kwargs.pop("config", None) or load_config()
        
        # Read content of the binary calibration file
        if fn is None:
            self.fn = CALIBRATION
        else:
            self.fn = fn
        with open(self.fn, "rb") as fp:
            self.raw = fp.read()
        if len(self.raw) % 16:
            raise RuntimeError("File size must be a multiple of 16!")

        # Convert calibration data to numpy array. First column are
        # attenuator values, second column is laser power in mW.
        self.num = len(self.raw) // 16
        fmt = "<" + 2*self.num*"d"
        self.data = struct.unpack(fmt, self.raw)
        self.data = numpy.array(self.data)
        self.data.shape = (self.num, 2)

        # Either spline or polynomial interpolation.
        # Warning: Polynomial interpolation (in contrast to spline
        # interpolation) does not necessarily contain the original data
        # points!
        a = self.data[:,0]
        p = self.data[:,1]
        if self["fitKind"] == "poly":
            order = self["polynomialOrder"]
            if order is None:
                order = self["polynomialOrder"] = 2
            self.atop = numpy.poly1d(numpy.polyfit(a, p, order))
            self.ptoa = numpy.poly1d(numpy.polyfit(p, a, order))
        else:
            self.atop = interp1d(a, p, kind=self["fitKind"])
            self.ptoa = interp1d(p, a, kind=self["fitKind"])

        # Attenuator range is always 0..10
        if min(a) != self["valueMin"]:
            raise RuntimeError("Attenuator data must start at %.1f!" % self["valueMin"])
        if max(a) != self["valueMax"]:
            raise RuntimeError("Attenuator data must end at %.1f!" % self["valueMax"])

        # Power range
        self["powerMin"] = min(p)
        self["powerMax"] = max(p)

        # Done
        self.log.info(str(self))
        self.log.info("Initialized attenuator.")


    def __self__(self):

        return "Attenuator: %.2f - %.2f mW (%d steps)." % \
               (self["powerMin"], self["powerMax"], self.num)
    

    def info(self):

        """ Return information dictionary. """

        result = self.parameters()
        result["calibration"] = self.data.tolist()
        return result
    

    def container(self, **kwargs):

        """ Return results as SciDataContainer. """

        # General metadata
        content = {
            "containerType": {"name": "DcPowerAttenuator", "version": 1.0},
            }
        meta = {
            "title": "TPP laser power calibration data",
            "description": "TPP laser power calibration.",
            }

        # Calibration data in JSON format
        data = {"data": self.data.tolist()}
        
        # Create container dictionary
        items = {
            "content.json": content,
            "meta.json": meta,
            "data/parameter.json": self.parameters(),
            "meas/calibration.json": data,
            "meas/calibration.dat": self.raw,
            }

        # Return container object
        config = self.dc_config
        if "config" in kwargs:
            config = dict(config).update(kwargs["config"])
        kwargs["config"] = config
        return Container(items=items, **kwargs)
