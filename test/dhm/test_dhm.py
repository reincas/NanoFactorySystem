##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import numpy as np
import cv2 as cv
from nanofactorysystem import getLogger, mkdir
from nanofactorysystem.dhm import DhmClient

HOST = "192.168.22.2"
PORT = 27182

path = mkdir(".test/dhm")
logger = getLogger(logfile="%s/console.log" % path)

with DhmClient(host=HOST, port=PORT) as client:
    
    logger.info("Select objective.")
    cid = 178
    configs = client.ConfigList
    name = dict(configs)[cid]
    client.Config = cid
    logger.info("Objective: %s [%d]" % (name, cid))

    logger.info("Motor pos: %.1f µm" % client.MotorPos)

    logger.info("Test camera shutter.")
    shutter = client.CameraShutter
    shutterus = client.CameraShutterUs
    logger.info("Shutter: %.1f us [%d]" % (shutterus, shutter))

    logger.info("Get hologram image.")
    img = client.CameraImage
    fn = "%s/hologram.png" % path
    logger.info("Store hologram image file '%s'" % fn)
    cv.imwrite(fn, img)

    imin = np.min(img)
    imax = np.max(img)
    iavg = np.average(img)
    logger.info("Pixel values: %d - %d (avg: %.1f)" % (imin, imax, iavg))

    logger.info("Done.")


