##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module provides a class for Matrix Vision cameras.
#
##########################################################################
# Default camera settings:
# ------------------------
# Device
#     Family mvBlueFOX3
#     Product mvBlueFOX3-2032aG
#     Serial FF008343
#     DeviceID 0
# Setting - Base - Camera - GenICam - 
# AcquisitionControl        
#     AcquisitionMode Continuous, MultiFrame, SingleFrame
#     ExposureMode Timed, TriggerWidth
#     ExposureTime 20000.000
#     ExposureAuto Off, Continuous
# AnalogControl
#     mvGainMode: Default
#     GainSelector: AnalogAll, DigitalAll
#         Gain: 0.000
#         GainAuto: Off, Continuous
##########################################################################

import ctypes
import numpy as np
try:
    from mvIMPACT import acquire
except:
    acquire = None
    
from scidatacontainer import Container

from . import sysConfig
from .parameter import Parameter


##########################################################################
class Property(object):

    def __init__(self, device, name, mvProperty):

        # Store parameters
        self.device = device
        self.name = name

        # Locate component
        locator = acquire.DeviceComponentLocator(self.device, acquire.dltSetting, "Base")
        if locator.findComponent(self.name) < 0:
            raise RuntimeError("Component '%s' not found!" % self.name)

        # Bind component to a property object
        self.obj = mvProperty
        locator.bindComponent(self.obj, self.name)

    @property
    def minValue(self):

        if not self.obj.hasMinValue:
            raise AttributeError("Component '%s' has no min value!" % self.name)
        return self.obj.getMinValue()

    @property
    def maxValue(self):

        if not self.obj.hasMaxValue:
            raise AttributeError("Component '%s' has no max value!" % self.name)
        return self.obj.getMaxValue()

    @property
    def choices(self):

        if not self.obj.hasDict:
            raise AttributeError("Component '%s' is no selector!" % self.name)
        size = self.obj.dictSize()
        return [self.obj.getTranslationDictString(i) for i in range(size)]

    @property
    def value(self):

        return self.obj.read()
    
    @value.setter
    def value(self, v):

        self.obj.write(v)


class PropertyS(Property):

    def __init__(self, device, name):

        super().__init__(device, name, acquire.PropertyS())


class PropertyInt(Property):

    def __init__(self, device, name):

        super().__init__(device, name, acquire.PropertyI64())


class PropertyFloat(Property):

    def __init__(self, device, name):

        super().__init__(device, name, acquire.PropertyF())


class PropertySelect(Property):

    def __init__(self, device, name):

        super().__init__(device, name, acquire.PropertyI())

    @property
    def value(self):

        return self.obj.readS()
    
    @value.setter
    def value(self, v):

        if not isinstance(v, str):
            if not isinstance(v, int):
                raise ValueError("Selection value not integer!")
            size = self.obj.dictSize()
            if v < 0 or v >= size:
                raise ValueError("Selection value %d not in range 0-%d!" % (v, size-1))
            v = self.obj.getTranslationDictString(v)
        self.obj.writeS(v)


##########################################################################
class CameraDevice(object):

    """ MatrixVision camera device class. This is a conveniance wrapper to the
    MatrixVision library. """

    # Property classes
    _properties = {
        "family": None,
        "product": None,
        "serial": None,
        "deviceID": None,
        "Width": PropertyInt,
        "Height": PropertyInt,
        "OffsetX": PropertyInt,
        "OffsetY": PropertyInt,
        "AcquisitionMode": PropertySelect,
        "ExposureMode": PropertySelect,
        "ExposureTime": PropertyFloat,
        "ExposureAuto": PropertySelect,
        "mvGainMode": PropertySelect,
        "GainSelector": PropertySelect,
        "Gain": PropertyFloat,
        "GainAuto": PropertySelect,
        }

    def __init__(self, product=None, deviceID=None):

        """ Initialize the camera. """

        # Initialize attributes
        self._property = {}
        
        # Get camera device
        self.manager = acquire.DeviceManager()
        if product is None:
            self.device = self.manager.getDevice(0)
        else:
            if deviceID is None:
                assert isinstance(product, str)
                self.device = self.manager.getDeviceByProductAndID(product)
            else:
                assert isinstance(deviceID, str)
                self.device = self.manager.getDeviceByProductAndID(product, deviceID)

        # Initialize the camera device
        self.device.open()

        # Store a function interface and clear the request and the
        # result queue
        self.fi = acquire.FunctionInterface(self.device)
        

    def close(self):

        """ Close camera device. """

        self.device.close()
        self._property = {}


    def __str__(self):

        """ Return description string for the camera. """

        if self.opened:
            result = "Camera %d: %s (S/N %s), %d x %d pixel." \
                     % (self["deviceID"], self["product"], self["serial"],
                        self["Width"], self["Height"])
        else:
            result = "Camera closed."
        return result


    def keys(self):
        
        return list(self._properties.keys())
    
    
    def __setitem__(self, key, value):

        if key in self._property:
            self._property[key].value = value
            return

        if key in self._properties:
            cls = self._properties[key]
            if cls is None:
                raise RuntimeError("Item %s is read-only!" % key)
            self._property[key] = cls(self.device, key)
            self._property[key].value = value
            return

        raise KeyError("Unknown item %s!" % key)
        

    def __getitem__(self, key):

        if key in self._property:
            return self._property[key].value

        if key in self._properties:
            cls = self._properties[key]
            if cls is None:
                value = getattr(self.device, key).read(0)
            else:
                self._property[key] = cls(self.device, key)
                value = self._property[key].value
            return value

        raise KeyError("Unknown item %s!" % key)


    def property(self, key):

        if key in self._property:
            return self._property[key]

        if key in self._properties:
            self._property[key] = self._properties[key](self.device, key)
            return self._property[key]

        raise KeyError("Unknown item %s!" % key)

        
    def getimage(self):

        """ Grab and return a camera image. """

        img = None

        # Place an image request in the request queue
        self.fi.imageRequestSingle()

        # Get result number from the result queue
        timeout = max(50, round(2000*self["ExposureTime"]))
        if np.log(timeout)/np.log(2) >= 32.0:
            raise RuntimeError("Timeout must be a 32 bit integer!")
        reqno = self.fi.imageRequestWaitFor(timeout)
        if self.fi.isRequestNrValid(reqno):

            # Get result from the result queue
            req = self.fi.getRequest(reqno)
            if req.isOK:

                # Get image meta data
                addr = int(req.imageData.read())
                size = req.imageSize.read()
                width = req.imageWidth.read()
                height = req.imageHeight.read()
                depth = req.imageChannelBitDepth.read()
                channels = req.imageChannelCount.read()
                if channels != 1:
                    raise RuntimeError("Gray scale camera required!")

                # Copy image data to numpy array
                cbuf = (ctypes.c_char * size).from_address(addr)
                dtype = np.uint16 if depth > 8 else np.uint8
                img = np.copy(np.frombuffer(cbuf, dtype=dtype))
                img.shape = (height, width)

            # Unlock the request object
            req.unlock()
            req = None

        if img is None:
            raise RuntimeError("Image grabbing failed!")
        return img
 

##########################################################################
class Camera(Parameter):

    """ Camera class. """

    _defaults = {
        "AcquisitionMode": "SingleFrame",
        "ExposureMode": "Timed",
        "ExposureTime": 20000,
        "ExposureAuto": 0,
        "mvGainMode": "Default",
        "GainSelector": "AnalogAll",
        "Gain": 0,
        "GainAuto": 0,
        }

    def __init__(self, user, logger=None, **kwargs):

        """ Initialize the camera. """

        # Not open now
        self.opened = False

        # Store camera data dictionary
        product = kwargs.pop("product", None)
        deviceID = kwargs.pop("deviceID", None)
        self.camera = sysConfig.camera
        
        # Initialize parameter class
        super().__init__(user, logger, **kwargs)
        self.log.info("Initializing camera.")

        # Open camaera device
        self.device = CameraDevice(product, deviceID)
        self.log.info("Camera: %s" % self.device)
        self.setaoi(None)
        
        # Done
        self.log.info("Initialized camera.")
        

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
        
        self.device["AcquisitionMode"] = "Continuous"

        # Close the device
        self.device.close()
        self.opened = False
        self.log.info("Camera closed.")


    def setaoi(self, size=None):

        """ Set area of interest to given quadratic field centered on
        the sensor. Set to full sensor size if no size is given. """

        if not self.opened:
            raise RuntimeError("Camera device closed!")

        # Determine minimum and maximum values
        self.device["OffsetX"] = 0
        self.device["OffsetY"] = 0
        wmin = self.device.property("Width").minValue
        wmax = self.device.property("Width").maxValue
        hmin = self.device.property("Height").minValue
        hmax = self.device.property("Height").maxValue
        
        # Maximize area of interest
        if size is None:
            self.device["Width"] = wmax
            self.device["Height"] = hmax
            self.w, self.h = wmax, hmax

        # Set area of interest to center of the camera sensor
        else:
            size = max(size, wmin, hmin)
            size = min(size, wmax, hmax)
            x = (wmax - size) // 2
            y = (hmax - size) // 2
            self.device["Width"] = size
            self.device["Height"] = size
            self.device["OffsetX"] = x
            self.device["OffsetY"] = y
            self.w = size
            self.h = size


    def _funcexpose(self, t, level):

        """ Get camera image with given eposure time and return
        deviation of mean value from the given value. """
        
        self.device["ExposureTime"] = t
        img = self.device.getimage()
        result = img.mean()-level
        return result
    
        
    def optexpose(self, level=127):

        """ Set exposure time for given mean value of the image content.
        """

        if not self.opened:
            raise RuntimeError("Camera device closed!")
        self.log.info("Start exposure time optimization.")
        
       # Initialize exposure mode
        self.device["ExposureMode"] = "Timed"
        self.device["ExposureAuto"] = 0
        self.device["ExposureTime"] = 20000

        f = self._funcexpose

        tmin = self.device.property("ExposureTime").minValue
        t0 = 20000
        y0 = f(t0, level)
        while t0 > tmin + 100:
            if y0 < 0.0:
                break
            t0 = tmin + 0.9 * (t0 - tmin)
            y0 = f(t0, level)
        else:
            raise RuntimeError("Optimization failed!")

        tmax = min(100000.0, self.device.property("ExposureTime").maxValue)
        t1 = 30000
        y1 = f(t1, level)
        while t1 < tmax - 100:
            if y1 > 0.0:
                break
            t1 = tmax - 0.1 * (tmax - t1)
            y1 = f(t1, level)
        else:
            raise RuntimeError("Optimization failed!")
        
        while (t1-t0) > 10.0:
            t = t0 - y0*(t1-t0)/(y1-y0)
            y = f(t, level)
            if y < 0.0:
                t0 = t
                y0 = y
            elif y > 0.0:
                t1 = t
                y1 = y
            else:
                break
        else:
            t = 0.5 * (t0 + t1)            

        # Set and return the optimum exposure time
        self.device["ExposureTime"] = t
        avg = self.device.getimage().mean()
        self.log.info("Optimized exposure time: %.3f ms, mean image value: %.1f (goal: %d)" % (0.001*t, avg, level))
        return t


    def getimage(self):

        """ Grab and return a camera image. """

        if not self.opened:
            raise RuntimeError("Camera device closed!")

        return self.device.getimage()


    def info(self):

        """ Return a dictionary containing the camera device info. """

        return {
            "family": self.device["family"],
            "product": self.device["product"],
            "serial": self.device["serial"],
            "id": self.device["deviceID"],
            }
    

    def container(self, img=None, config=None, **kwargs):

        """ Return given or current camera image as SciDataContainer. """

        # Grab camera image
        if img is None:
            img = self.getimage()

        # General metadata
        content = {
            "containerType": {"name": "CameraImage", "version": 1.1},
            }
        meta = {
            "title": "Microscope Camera Image",
            "description": "Camera image from Matrix Vision camera",
            }

        # Create container dictionary
        items = {
            "content.json": content,
            "meta.json": meta,
            "meas/image.json": self.parameters(self.camera),
            "meas/image.png": img,
            }
        
        # Return container object
        config = config or self.config
        return Container(items=items, config=config, **kwargs)
