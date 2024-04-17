##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module provides the function optExpose to optimize the exposure 
# time of a camera device.
#
##########################################################################

def expose(camera, t, level):

    """ Get camera image with given exposure time and return
    deviation of mean value from the given value. """
    
    camera["ExposureTime"] = t
    img = camera.getimage()
    result = img.mean()-level
    return result

    
def optExpose(camera, level=127):

    """ Find exposure time resulting in a given mean value of the image
    content. """

   # Initialize exposure mode
    camera["ExposureMode"] = "Timed"
    camera["ExposureAuto"] = 0
    camera["ExposureTime"] = 20000

    tmin = camera.property("ExposureTime").minValue
    t0 = 20000
    y0 = expose(camera, t0, level)
    while t0 > tmin + 100:
        if y0 < 0.0:
            break
        t0 = tmin + 0.9 * (t0 - tmin)
        y0 = expose(camera, t0, level)
    else:
        raise RuntimeError("Optimization failed!")

    tmax = min(100000.0, camera.property("ExposureTime").maxValue)
    t1 = 30000
    y1 = expose(camera, t1, level)
    while t1 < tmax - 100:
        if y1 > 0.0:
            break
        t1 = tmax - 0.1 * (tmax - t1)
        y1 = expose(camera, t1, level)
    else:
        raise RuntimeError("Optimization failed!")
    
    while (t1-t0) > 10.0:
        t = t0 - y0*(t1-t0)/(y1-y0)
        y = expose(camera, t, level)
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
    camera["ExposureTime"] = t
    return t
