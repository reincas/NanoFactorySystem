##########################################################################
# Copyright (c) 2023-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import numpy as np
import matplotlib.pyplot as plt
from scidatacontainer import load_config
from nanofactorysystem import Attenuator, getLogger

config = load_config(
    author = "Reinhard Caspary",
    email = "reinhard.caspary@phoenixd.uni-hannover.de",
    organization = "Leibniz Universität Hannover",
    orcid = "0000-0003-0460-6088")

logger = getLogger()
att = Attenuator(logger=logger, config=config, fitKind="quadratic")

logger.info("Calibration data:")
for value, power in att.data:
    logger.info("    %4.1f -> %6.2f mW" % (value, power))

dc = att.container()
dc.write("attenuator.zdc")
print(dc)

cx = att.data[:,0]
cy = att.data[:,1]
x = np.linspace(att["valueMin"], att["valueMax"], 501)
y = att.atop(x)

fig, ax = plt.subplots(figsize=(12,9))
plt.plot(cx, cy, "r+")
plt.plot(x, y, "b")
plt.show()
logger.info("Done.")
