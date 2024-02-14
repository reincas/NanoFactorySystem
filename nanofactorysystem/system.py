##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module provides the system class for a laser direct writing
# system, which is the hardware interface used by the algorithm modules.
#
##########################################################################

import math
import random
from scidatacontainer import Container, load_config

from .parameter import Parameter
from .camera import Camera
from .attenuator import Attenuator
from .aerotech import A3200


##########################################################################
class System(Parameter):

    """ Class for the detection of the xy interfaces of a resin layer on
    the Femtika Nanofactory system. """

    _defaults = {
        "name": None,
        "manufacturer": None,
        "wavelength": None,
        "objective": None,
        "zMax": None,
        "backOffset": -3000.0,
        "speed": 2000.0,
        "delay": 10.0,
        "attenuator": None,
        "camera": None,
        "controller": None,
        }

    def __init__(self, sample=None, logger=None, config=None, **kwargs):

        """ Initialize the scanner algorithm. """

        # Not open now
        self.opened = False

        # Initialize parameter class
        super().__init__(logger, config, **kwargs)
        self.log.info("Initializing system.")

        # Store optional sample data dictionary. Applications using the
        # system should include this item into their data container.
        self.sample = sample

        # No background image so far
        self.back = None

        # Initialize the MatrixVision camera
        self.camera = Camera(logger=self.log, config=self.dc_config)
        if not self.camera.opened:
            self.log.error("Can't connect to camera!")
            raise RuntimeError("Can't connect to camera!")
        self["camera"] = self.camera.info()

        # Initialize attenuator
        self.attenuator = Attenuator(logger=self.log, config=self.dc_config)
        self["attenuator"] = self.attenuator.info()
        
        # Initialize the Aerotech A3200 controller
        if self["zMax"] is None:
            raise RuntimeError("Maximum z value is missing!")
        self.controller = A3200(self.attenuator, logger=self.log,
                                config=self.dc_config, zMax=self["zMax"])
        self.controller.init_zline()
        self["controller"] = self.controller.info()

        # Center the galvo scanner
        self.controller.moveabs(100, a=0, b=0)

        # Current xyz positions
        self.x0, self.y0, self.z0 = self.controller.position("XYZ")
        if self.z0 > self.controller["zMax"]:
            raise RuntimeError("Maximum z position exceeded!")

        # Mark open state
        self.opened = True

        # Done
        self.log.info("Initialized system.")


    def close(self, home=True):

        """ Close connection to hardware devices. """

        if home and self.opened:
            self.home(wait=False)

        self.camera["AcquisitionMode"] = "Continuous"
        self.camera.close()

        try:
            self.controller.close()
        except AttributeError:
            pass

        self.opened = False
        self.log.info("System closed.")
        
        
    def __enter__(self):

        """ Context manager entry method. """

        return self


    def __exit__(self, errtype, value, tb):

        """ Context manager exit method. """

        #print("".join(traceback.format_exception(errtype, value, tb)))
        self.close()


    def home(self, wait=False):

        """ Move stages to their home position. """

        self.controller.moveabs(self["speed"], a=0.0, b=0.0)
        self.controller.moveabs(self["speed"], x=self.x0, y=self.y0, z=self.z0)
        if wait:
            self.controller.wait("XYZ")
        self.log.debug("Moved to home position %.0f, %.0f, %.0f" % (self.x0, self.y0, self.z0))
        

    def position(self, axes):

        """ Return current measured positions in micrometers on the
        given axes as a list of floating point numbers. Return a single
        number if a single axis is requested. """

        return self.controller.position(axes)


    def moveabs(self, speed=None, wait=None, **axes):

        """ Move on one or more axes with the given speed in micrometers
        per second. The absolute positions are given in micrometers as
        named parameters. It is optional to name the axes for which to
        wait to be settled after the movement. """

        if speed is None:
            speed = self["speed"]
        self.controller.moveabs(speed, **axes)
        if wait is not None:
            self.controller.wait(wait)


    def pulse(self, power, duration):

        """ Deliver laser pulse with given power in milliwatts and
        duration in seconds. """

        self.controller.pulse(power, duration)


    def getimage(self):

        """ Get a camera image and return an image container. """

        return self.camera.container(config=self.dc_config)
    

    def polyline(self, line, power, speed, dia):

        """ Exposed a single 2D polyline with given laser power and
        eposure speed at the current position. The given approximate
        focus diameter is used to handle very short polylines. """

        x = [x for x, y in line]
        y = [y for x, y in line]
        llx = min(x)
        lly = min(y)
        urx = max(x)
        ury = max(y)
        size = math.sqrt((urx-llx)**2 + (ury-lly)**2)

        if size < 0.2*dia:
            x = 0.5*(llx+urx)
            y = 0.5*(lly+ury)
            self.controller.moveabs(self["speed"], x=x, y=y)
            self.pulse(power, 10*dia/speed)
        else:
            x, y = line[0]
            self.controller.moveabs(self["speed"], x=x, y=y)
            self.controller.laseron(power)
            for x, y in line[1:]:
                self.controller.moveabs(speed, x=x, y=y)
            self.controller.laseroff()
            
        
    def polylines(self, z, lines, power, speed, dia):

        """ Exposed a couple of 2D polylines with given laser power and
        exposure speed at the given z position. The given approximate
        focus diameter is used to handle very short polylines. """

        self.controller.moveabs(self["speed"], z=z)
        for line in lines:
            self.polyline(line, power, speed, dia)
            

    def dots(self, z, img, pitch, power, dt):

        """ Exposed the given 1 bit image as an array of laser pulses
        with given lateral pitch, laser power and pulse duration at the
        given z position. """

        self.controller.moveabs(self["speed"], z=z)
        x0, y0 = self.position("xy")
        h = len(img)
        for j, row in enumerate(img):
            y = y0 + (j-0.5*(h-1))*pitch
            w = len(row)
            for i, value in enumerate(row):
                x = x0 + (i-0.5*(w-1))*pitch
                if value > 0:
                    self.controller.moveabs(self["speed"], x=x, y=y)
                    self.pulse(power, dt)
        self.controller.moveabs(self["speed"], x=x0, y=y0)
        

    def zline(self, x, y, z, dz, power, speed, duration, jitter=None):

        """ Exposed an axial line or point (dz=0) at given position.
        Return camera images from before and after exposure. """

        # Move to center position
        if jitter:
            xc = random.gauss(x, jitter)
            yc = random.gauss(y, jitter)
        else:
            xc, yc = x, y
        self.controller.moveabs(self["speed"], x=xc, y=yc, z=z)
        self.controller.wait("XYZ", self["delay"])

        # Take pre exposure camera image
        img0 = self.getimage()

        # Correct for forced axial jitter if requested
        if jitter:
            self.controller.moveabs(self["speed"], x=x, y=y, z=z)
            self.controller.wait("XYZ", self["delay"])

        # Expose axial line
        if dz != 0.0:
            v = min(speed, dz/duration)
            dt = dz/v
            self.controller.zline(power, self["speed"], v, dz)
            self.controller.wait("XYZ", self["delay"])

        # Expose a dot
        else:
            v = 0.0
            dz = 0.0
            dt = duration
            self.controller.pulse(power, dt)
            
        # Take post exposure camera image
        if jitter:
            xc = random.gauss(x, jitter)
            yc = random.gauss(y, jitter)
            self.controller.moveabs(self["speed"], x=xc, y=yc, z=z)
            self.controller.wait("XYZ", self["delay"])
        img1 = self.getimage()

        # Done
        return img0, img1, v, dt
            

    def background(self, z=None, dz=None, force=False, home=True):

        """ Eventually move to given z position and take a background
        camera image. Find the exposure time to get camera images with
        an average pixel value of 127. Return image as image container
        object. """

        # Return existing background image, if available
        if not force and self.back is not None:
            self.log.info("Keeping existing background image.")
            return self.back

        self.log.info("Take background image.")

        # Current z position        
        z0 = self.controller.position("Z")

        # Requested z position
        if dz is not None:
            if z is None:
                z = z0 + dz
            else:
                z += dz
        
        # Move to given z position
        if z is not None:
            self.controller.moveabs(self["speed"], z=z)
            self.controller.wait("Z", self["delay"])

        # Set exposure time for normalized image
        self.camera.optExpose(127)
            
        # Take background image
        self.back = self.getimage()

        # Move back to initial z position
        if home:
            self.controller.moveabs(self["speed"], z=z0)
            self.controller.wait("Z", self["delay"])

        # Return images
        self.log.info("Got background image.")
        return self.back


    def container(self, config=None, **kwargs):

        """ Return system configuration as SciDataContainer. """

        # General metadata
        content = {
            "containerType": {"name": "DcSystem", "version": 1.0},
            } 
        meta = {
            "title": "TPP System Configuration Data",
            "description": "Parameters of the TPP system.",
            }

        # Create container dictionary
        items = {
            "content.json": content,
            "meta.json": meta,
            "data/parameter.json": self.parameters(),
            }

        # Return container object
        config = config or self.config
        return Container(items=items, config=config, **kwargs)
