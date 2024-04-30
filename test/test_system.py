##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

from nanofactorysystem import System, getLogger, mkdir

args = {
    "attenuator": {
        "fitKind": "quadratic",
        },
    "controller": {
        "zMax": 25700.0,
        },
    "sample": {
        "name": "#1",
        "orientation": "top",
        "substrate": "boro-silicate glass",
        "substrateThickness": 700.0,
        "material": "SZ2080",
        "materialThickness": 75.0,
        },
    }

user = "Reinhard"
objective = "Zeiss 20x"
path = mkdir(".test/system")
logger = getLogger(logfile=f"{path}/console.log")
with System(user, objective, logger, **args) as system:
    dc = system.container()
    dc.write(f"{path}/system.zdc")
    print(dc)
    logger.info("Done.")
