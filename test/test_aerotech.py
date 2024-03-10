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
path = mkdir("test/aerotech")
logger = getLogger(logfile="%s/console.log" % path)
with A3200(user, logger, **args) as controller:
    x0, y0, z0 = controller.position("XYZ")
    logger.info("Stage x position: %.3f µm" % x0)
    logger.info("Stage y position: %.3f µm" % y0)
    logger.info("Stage z position: %.3f µm" % z0)
    dc = controller.container()
    dc.write("%s/controller.zdc" % path)
    print(dc)
    logger.info("Done.")
