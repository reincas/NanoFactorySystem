##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module provides a class for the digital holographic microscope
# from LyncéeTec.
#
##########################################################################

import numpy as np

from ..parameter import Parameter
from ..config import sysConfig, popargs
from ..dhm import DhmClient, optImage, motorScan
from ..hologram import HoloContainer


class Dhm(Parameter):

    """ Class for digital holographic microscope. """

    _defaults = sysConfig.dhm | {
        "contrastQuantile": 0.05,
        "maxOverflow": 9,
        "oplMode": "both",
        "oplSteps": 11,
        "oplStep": 250.0,
        "oplThreshold": 0.2,
        "oplMinContrast": 0.001,
        "oplMinPos": 5.0,
        "oplOptImage": True,
        "oplInitPos": None,
        "oplOptPos": None,
        }


    def __init__(self, user, objective, logger=None, **kwargs):

        """ Initialize the digital holographic microscope. """

        # Not open now
        self.opened = False

        # Objective parameters
        self.objective = objective

        # Initialize parameter class
        args = popargs(kwargs, "dhm")
        super().__init__(user, logger, **args)
        self.log.info("Initializing holographic microscope.")

        # Open camera device
        host = self["host"]
        port = self["port"]
        self.device = DhmClient(host, port)
        self.opened = True
        if not self.opened:
            self.log.error("Initializing of holographic microscope failed!")
            return

        # Apply initial parameters
        for key in self.device.set_keys():
            if key in self.keys() and self[key] is not None:
                self.device[key] = self[key]
        
        # Select objective
        cid = self.objective["dhmId"]
        configs = self.device.ConfigList
        name = dict(configs)[cid]
        self.device.Config = cid
        self.log.info("Holographic Microscope: %s" % self.device)
        logger.info("Objective: %s [%d]" % (name, cid))

        # Done
        self.log.info("Initialized holographic microscope.")
        

    def __enter__(self):

        """ Context manager entry method. """

        return self


    def __exit__(self, errtype, value, tb):

        """ Context manager exit method. """

        self.device.close()


    def close(self):

        """ Close camera device. """

        # Closed already
        if not self.opened:
            return
        
        # Close the device
        self.device.close()
        self.opened = False
        self.log.info("Holographic microscope closed.")


    def getimage(self, opt=True):

        """ Grab a camera image with maximized exposure time limited by
        a maximum of self["maxOverflow"] overflow pixels if opt is True.
        Return the total number of images grabbed by the algorithm as second
        parameter. Return a camera image using the current exposure
        time, if opt is False. """

        if opt:
            img, count = optImage(self, self["maxOverflow"], self.log)
        else:
            img = self.device.CameraImage
            count = None
        return img, count


    def motorscan(self, m0=None):

        """ Perform a scan of the optical path length (OPL) motor. The
        interference contrast is maximized by balancing the path lengths
        of object and reference beam. """

        args = {
            "mode": self["oplMode"],
            "steps": self["oplSteps"],
            "dm": self["oplStep"],
            "thresh": self["oplThreshold"],
            "init": m0,
            "minc": self["oplMinContrast"],
            "minm": self["oplMinPos"],
            "opt": self["oplOptImage"],
            "logger": self.log,
        }
        m, m0 = motorScan(self, **args)
        self["oplInitPos"] = m0
        self["oplOptPos"] = m
        return m


    def container(self, opt=True, loc=None, config=None, **kwargs):

        """ Return a HoloContainer with current hologram image. """

        # Hologram image
        holo, count = self.getimage(opt=opt)
        kwargs["holo"] = holo

        # Median values
        q = [self["contrastQuantile"], 0.5, 1.0-self["contrastQuantile"]]
        imin, imedian, imax = np.quantile(holo, q, method="nearest")

        # Overflow and underflow pixels
        numuf = np.count_nonzero(holo <= 0)
        numof = np.count_nonzero(holo >= 255)

        kwargs["results"] = {
            "optCount": count,
            "minValue": int(np.min(holo)),
            "maxValue": int(np.max(holo)),
            "avgerageValue": float(np.average(holo)),
            "lowQuantileValue": int(imin),
            "medianValue": int(imedian),
            "highQuantileValue": int(imax),
            "underflowPixel": numuf,
            "overflowPixel": numof,            
            }
        
        # Hologram parameters
        kwargs["params"] = self.parameters()

        # Objective parameters
        kwargs["objective"] = self.objective
        
        # Location coordinates
        kwargs["loc"] = loc

        # User configuration        
        kwargs["config"] = config or self.config

        # Return container object
        return HoloContainer(items=None, **kwargs)
