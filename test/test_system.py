##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

from nanofactorysystem import System, getLogger

author = "Reinhard Caspary"
email = "reinhard.caspary@phoenixd.uni-hannover.de"

params = {
    "name": "Laser Nanofactory",
    "manufacturer": "Femtika",
    "wavelength": 0.515,
    "objective": "Zeiss 20x, NA 0.8",
    "zMax": 25700.0,
    }

sample = {
    "name": "#1",
    "orientation": "top",
    "substrate": "boro-silicate glass",
    "substrateThickness": 700.0,
    "material": "SZ2080",
    "materialThickness": 75.0,
    }

logger = getLogger()
with System(sample, logger=logger, **params) as mysystem:
    log = mysystem.log
    dc = mysystem.container()
    dc.write("system.zdc")
    print(dc)
    log.info("Done.")
