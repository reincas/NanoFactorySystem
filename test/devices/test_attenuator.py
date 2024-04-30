##########################################################################
# Copyright (c) 2023-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import numpy as np
import matplotlib.pyplot as plt
from nanofactorysystem import Attenuator, getLogger, mkdir

args = {
    "attenuator": {
        "fitKind": "quadratic",
        },
    }

user = "Reinhard"
path = mkdir(".test/attenuator")
logger = getLogger(logfile=f"{path}/console.log")
att = Attenuator(user, logger, **args)

logger.info("Calibration data:")
for value, power in att.data:
    logger.info(f"    {value:4.1f} V -> {power:6.2f} mW")

dc = att.container()
dc.write(f"{path}/attenuator.zdc")
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
plt.savefig(f"{path}/calibration.png")
plt.show()

logger.info("Done.")
