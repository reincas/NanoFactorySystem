##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

from nanofactorysystem import Camera, getLogger

author = "Reinhard Caspary"
email = "reinhard.caspary@phoenixd.uni-hannover.de"

logger = getLogger()
with Camera(logger=logger) as camera:
    log = camera.log
    log.info("Exposure time %.4f ms" % (0.001*camera["ExposureTime"]))
    log.info("Optimizing exposure time...")
    camera.optexpose()
    log.info("Exposure time %.4f ms" % (0.001*camera["ExposureTime"]))
    dc = camera.getimage()
    dc = camera.container(img)
    dc.write("image.zdc")
    print(dc)
    log.info("Done.")
