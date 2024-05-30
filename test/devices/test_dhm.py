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
logger = getLogger(logfile=f"{path}/console.log")
with Dhm(user, objective, logger, **args) as dhm:
    
    logger.info("Motor scan.")
    m = dhm.motorscan()
    logger.info(f"Motor pos: {dhm.device.MotorPos:.1f} µm (set: {m:.1f} µm)")

    logger.info("Get hologram container.")
    dc = dhm.container(opt=True)
    fn = f"{path}/hologram.zdc"
    logger.info(f"Store hologram container file '{fn}'")
    dc.write(fn)
    print(dc)

    logger.info("Test camera shutter.")
    shutter = dhm.device.CameraShutter
    shutterus = dhm.device.CameraShutterUs
    logger.info(f"Shutter: {shutterus:.1f} us [{shutter:d}]")

    logger.info("Done.")
