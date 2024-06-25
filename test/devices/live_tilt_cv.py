##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import logging

import cv2
import matplotlib.pyplot as plt
import numpy as np
from offaxisholo import reconstruct

import nanofactorysystem.image.functions as image
from nanofactorysystem import Dhm, sysConfig, getLogger

run = False


############################################################################
# Utility functions
############################################################################

def getImage(dhm):
    holo, count = dhm.getimage()
    spectrum, fx, fy, weight = reconstruct.locateOrder(holo, 16)
    dhm.log.info(f"First order coordinates: {fx:d}, {fy:d} [{100 * weight:.1f}%]")

    maxpixel = 255
    numof = np.count_nonzero(holo >= maxpixel)
    dhm.log.info(f"Overflow pixels: {numof:d}")

    img = np.log(np.abs(spectrum))
    h, w = img.shape
    vmax = 0.5 * np.max(img)
    img = np.where(img > vmax, vmax, img)

    img = image.normcolor(img)
    r0 = dhm.objective["dcRadius"]
    img = image.drawCircle(img, 0, 0, r0, image.CV_RED, 1)

    rmax = np.sqrt(fx ** 2 + fy ** 2) - r0
    rmax = min(rmax, abs(fx), w // 2 - abs(fx), abs(fy), h // 2 - abs(fy))
    dhm.log.info(f"Maximum radius: {rmax:.0f} pixels")
    if rmax > 0:
        img = image.drawCircle(img, fx, fy, rmax, image.CV_RED, 1)
        img = image.drawCircle(img, -fx, -fy, rmax, image.CV_RED, 1)
    img = image.drawCross(img, fx, fy, 30, image.CV_RED, 1)
    img = image.drawCross(img, -fx, -fy, 30, image.CV_RED, 1)
    return img


def showImage(img: np.ndarray):
    cv2.imshow("DHM", img)


############################################################################
# Main function
############################################################################

if __name__ == "__main__":

    args = {
        "dhm": {},
    }

    user = "Reinhard"
    objective = "Zeiss 20x"
    objective = sysConfig.objective(objective)
    # path = mkdir(".test/tilt")
    opt = True
    scan = False
    spectrum = False

    logger = getLogger()
    logger.setLevel(logging.DEBUG)
    with Dhm(user, objective, logger, **args) as dhm:

        if opt:
            dhm.device.MotorPos = 3597
            if scan:
                logger.info("Run OPL Motor Scan...")
                dhm.motorscan()
            logger.info("Motor pos: %.1f µm" % dhm.device.MotorPos)

            logger.info("Optimize Camera Exposure Time...")
            dhm.getimage(opt=True)
            # client.CameraShutter = client.CameraShutter-2
            shutter = dhm.device.CameraShutter
            shutterus = dhm.device.CameraShutterUs
            logger.info(f"Shutter: {shutterus:.1f} us [{shutter:d}]")

        dc = dhm.container()
        dc.write("test.zdc")

        logger.info("Start Spectrum Display Loop...")
        run = True
        while run:
            if spectrum:
                img = getImage(dhm)
            else:
                holo, count = dhm.getimage(opt=False)
                img = image.normcolor(holo)
                img = image.drawCross(img, 0, 0, 30, image.CV_RED, 1)
            showImage(img)
            if cv2.waitKey(10) == ord("q"):
                print("Quitting...")
                run = False

        logger.info("Done.")
