##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

from nanofactorysystem import A3200, getLogger, mkdir

args = {
    "attenuator": {
        "fitKind": "quadratic",
        },
    "controller": {
        "zMax": 25700.0,
        },
    }

user = "Reinhard"
path = mkdir(".test/aerotech")
logger = getLogger(logfile=f"{path}/console.log")
with A3200(user, logger, **args) as controller:
    x0, y0, z0 = controller.position("XYZ")
    logger.info(f"Stage x position: {x0:.3f} µm")
    logger.info(f"Stage y position: {y0:.3f} µm")
    logger.info(f"Stage z position: {z0:.3f} µm")
    dc = controller.container()
    dc.write(f"{path}/controller.zdc")
    print(dc)
    logger.info("Done.")
