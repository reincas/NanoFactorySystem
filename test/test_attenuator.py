##########################################################################
# Copyright (c) 2023-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import numpy as np
import matplotlib.pyplot as plt
from nanofactorysystem import Attenuator, getLogger

author = "Reinhard Caspary"
email = "reinhard.caspary@phoenixd.uni-hannover.de"

logger = getLogger()
att = Attenuator(logger=logger, fitKind="quadratic")
log = att.log

log.info("Calibration data:")
for value, power in att.data:
    log.info("    %4.1f -> %6.2f mW" % (value, power))

dc = att.container(author=author, email=email)
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
log.info("Done.")
