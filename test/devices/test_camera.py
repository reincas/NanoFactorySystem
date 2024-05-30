##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

from nanofactorysystem import Camera, sysConfig, getLogger, mkdir

args = {
    "camera": {
        "ExposureTime": 10000,
        },
    }

user = "Reinhard"
objective = "Zeiss 20x"
objective = sysConfig.objective(objective)
path = mkdir(".test/camera")
logger = getLogger(logfile=f"{path}/console.log")
with Camera(user, objective, logger, **args) as camera:
    logger.info(f"Exposure time {0.001 * camera['ExposureTime']:.4f} ms")
    logger.info("Optimizing exposure time...")
    camera.optexpose()
    logger.info(f"Exposure time {0.001 * camera['ExposureTime']:.4f} ms")
    dc = camera.container()
    dc.write(f"{path}/image.zdc")
    print(dc)
    logger.info("Done.")
