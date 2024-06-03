##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
from unittest import TestCase

import numpy as np
import cv2 as cv
from nanofactorysystem import getLogger, mkdir
from nanofactorysystem.dhm import DhmClient
class TestDHM(TestCase):
    HOST = "192.168.22.2"
    PORT = 27182

    def test_dhm(self):

        path = mkdir(".test/dhm")
        logger = getLogger(logfile=f"{path}/console.log")

        with DhmClient(host=self.HOST, port=self.PORT) as client:

            logger.info("Select objective.")
            cid = 178
            configs = client.ConfigList
            name = dict(configs)[cid]
            client.Config = cid
            logger.info(f"Objective: {name} [{cid:d}]")

            logger.info(f"Motor pos: {client.MotorPos:.1f} µm")

            logger.info("Test camera shutter.")
            shutter = client.CameraShutter
            shutterus = client.CameraShutterUs
            logger.info(f"Shutter: {shutterus:.1f} us [{shutter:d}]")

            logger.info("Get hologram image.")
            img = client.CameraImage
            fn = f"{path}/hologram.png"
            logger.info(f"Store hologram image file '{fn}'")
            cv.imwrite(fn, img)

            imin = np.min(img)
            imax = np.max(img)
            iavg = np.average(img)
            logger.info(f"Pixel values: {imin:d} - {imax:d} (avg: {iavg:.1f})")

            logger.info("Done.")


