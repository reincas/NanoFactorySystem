##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

from nanofactorysystem import Dhm, sysConfig, getLogger, mkdir

args = {
    "dhm": {
        "oplmode": "both",
        },
    }

user = "Reinhard"
objective = "Zeiss 20x"
objective = sysConfig.objective(objective)
path = mkdir(".test/dhm")
logger = getLogger(logfile="%s/console.log" % path)
with Dhm(user, objective, logger, **args) as dhm:
    
    logger.info("Motor scan.")
    m = dhm.motorscan()
    logger.info("Motor pos: %.1f µm (set: %.1f µm)" % (dhm.device.MotorPos, m))

    logger.info("Get hologram container.")
    dc = dhm.container(opt=True)
    fn = "%s/hologram.zdc" % path
    logger.info("Store hologram container file '%s'" % fn)
    dc.write(fn)
    print(dc)

    logger.info("Test camera shutter.")
    shutter = dhm.device.CameraShutter
    shutterus = dhm.device.CameraShutterUs
    logger.info("Shutter: %.1f us [%d]" % (shutterus, shutter))

    logger.info("Done.")
