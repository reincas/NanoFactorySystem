##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

from scidatacontainer import load_config
from nanofactorysystem import Camera, getLogger

config = load_config(
    author = "Reinhard Caspary",
    email = "reinhard.caspary@phoenixd.uni-hannover.de",
    organization = "Leibniz Universität Hannover",
    orcid = "0000-0003-0460-6088")

logger = getLogger()
with Camera(logger=logger, config=config) as camera:
    logger.info("Exposure time %.4f ms" % (0.001*camera["ExposureTime"]))
    logger.info("Optimizing exposure time...")
    camera.optexpose()
    logger.info("Exposure time %.4f ms" % (0.001*camera["ExposureTime"]))
    dc = camera.container()
    dc.write("image.zdc")
    print(dc)
    logger.info("Done.")
