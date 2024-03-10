##########################################################################
# Copyright (c) 2023-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import numpy as np
import matplotlib.pyplot as plt
from nanofactorysystem import Attenuator, getLogger, mkdir

args = {
    "fitKind": "quadratic",
    }

user = "Reinhard"
path = mkdir("test/attenuator")
logger = getLogger(logfile="%s/console.log" % path)
att = Attenuator(user, logger, **args)

logger.info("Calibration data:")
for value, power in att.data:
    logger.info("    %4.1f V -> %6.2f mW" % (value, power))

dc = att.container()
dc.write("%s/attenuator.zdc" % path)
print(dc)

cx = att.data[:,0]
cy = att.data[:,1]
x = np.linspace(att["valueMin"], att["valueMax"], 501)
y = att.atop(x)

fig, ax = plt.subplots(figsize=(12,9))
plt.plot(cx, cy, "r+")
plt.plot(x, y, "b")
plt.xlabel("Set Value [V]")
plt.ylabel("Laser Power [mW]")
plt.savefig("%s/calibration.png" % path)
plt.show()

logger.info("Done.")
