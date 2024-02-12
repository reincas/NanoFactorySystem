##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

from scidatacontainer import load_config
from nanofactorysystem import Attenuator, A3200, getLogger

config = load_config(
    author = "Reinhard Caspary",
    email = "reinhard.caspary@phoenixd.uni-hannover.de",
    organization = "Leibniz Universität Hannover",
    orcid = "0000-0003-0460-6088")

params = {
    "zMax": 26000.0,
    }

logger = getLogger()
with A3200(logger=logger, config=config, **params) as controller:
    log = controller.log
    x0, y0, z0 = controller.position("XYZ")
    log.info("Stage x position: %.3f µm" % x0)
    log.info("Stage y position: %.3f µm" % y0)
    log.info("Stage z position: %.3f µm" % z0)
    dc = controller.container()
    dc.write("controller.zdc")
    print(dc)
    log.info("Done.")
