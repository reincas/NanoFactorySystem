##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module provides the function optImage to get a hologram image
# with optimized contrast.
#
##########################################################################

import logging

import numpy as np


def optImage(dhm, maxof=9, logger=None):
    """ Return image with optimized exposure time. The number of
    overflow pixels in the returned image will be less or equal
    maxof. The second return value is the number of camera images
    grabbed by the algorithm. """

    # Prepare logger
    logger = logger or logging

    # Emergency break: Maximum number of images
    maxcount = 100

    # Maximum pixel value
    maxpixel = (1 << dhm.device.CameraBitPerPixel) - 1

    # Shutter limits
    minshutter = dhm.device.CameraMinShutter
    maxshutter = dhm.device.CameraMaxShutter

    # Initial shutter value
    s = s0 = dhm.device.CameraShutter
    if s0 < 10:
        s = 10

    # Find optimum shutter value
    smin = None
    smax = None
    optimg = None

    count = 0
    while True:
        count += 1
        if count > maxcount:
            raise RuntimeError("optImage failed!")

        # Set exposure time
        dhm.device.CameraShutter = s

        # Get camera image and quantile value
        img = dhm.device.CameraImage
        numof = np.count_nonzero(img >= maxpixel)

        # Show intermediate results
        if smin is None:
            str0 = "None"
        else:
            str0 = f"{smin:4d}"
        str1 = f"{s:4d} [{numof:4d}]"
        if smax is None:
            str2 = "None"
        else:
            str2 = f"{smax:4d}"
        logger.debug(f"{count:03d}: {str0} --  {str1} --  {str2}")

        # Number of overflow pixels above limit
        if numof > maxof:
            smax = s

            # Next shutter value
            if smin is None:
                s = max(minshutter, smax >> 1)
            else:
                s = (smin + smax) >> 1

        # Number of overflow pixels below limit
        else:
            smin = s
            optimg = img

            # Next shutter value
            if smax is None:
                s = min(maxshutter, smin << 1)
            else:
                s = (smin + smax) >> 1

        # Shutter optimized
        if smax is not None and smin is not None and smax - smin <= 1:
            break

    # Fine adjustment, remove outliers
    while True:
        count += 1
        if count > maxcount:
            raise RuntimeError("optImage failed!")

        # Set shutter value +1 above current optimum
        dhm.device.CameraShutter = smin + 1

        # Take camera image
        img = dhm.device.CameraImage
        numof = np.count_nonzero(img >= maxpixel)

        # Number of overflow pixels above limit
        if numof > maxof:
            break

        # New optimum
        smin += 1
        optimg = img

    # Return optimum image and total number of grabbed images
    dhm.device.CameraShutter = smin
    return optimg, count
