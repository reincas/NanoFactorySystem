##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import numpy as np
import matplotlib.pyplot as plt

from nanofactorysystem import Dhm, sysConfig, getLogger
from nanofactorysystem.hologram.reconstruct import refHolo
import nanofactorysystem.image.functions as image

run = False

############################################################################
# Utility functions
############################################################################

def on_close(event):

    global run
    run = False
    print("Quitting...")


def getImage(dhm):

    holo, count = dhm.getimage()
    #return image.normcolor(holo)
    ref = refHolo(holo, 16, 2)
    print("First order coordinates: %d, %d [%.1f%%]" % (ref.fx, ref.fy, 100*ref.weight))

    maxpixel = 255
    numof = np.count_nonzero(holo >= maxpixel)
    print("Overflow pixels: %d" % numof)
    
    spectrum = np.fft.fft2(holo.astype(np.float64))
    spectrum = np.fft.fftshift(spectrum)
    spectrum = np.log(np.abs(spectrum))
    
    img = spectrum
    h, w = img.shape
    vmax = 0.5*np.max(img)
    img = np.where(img > vmax, vmax, img) 

    img = image.normcolor(img)    
    r0 = dhm.objective["dcRadius"]
    img = image.drawCircle(img, 0, 0, r0, image.CV_RED, 1)
    
    rmax = np.sqrt(ref.fx**2 + ref.fy**2) - r0
    rmax = min(rmax, abs(ref.fx), w//2-abs(ref.fx), abs(ref.fy), h//2-abs(ref.fy))
    print("Maximum radius: %d pixels" % rmax)
    if rmax > 0:
        img = image.drawCircle(img, ref.fx, ref.fy, rmax, image.CV_RED, 1)
        img = image.drawCircle(img, -ref.fx, -ref.fy, rmax, image.CV_RED, 1)
    img = image.drawCross(img, ref.fx, ref.fy, 30, image.CV_RED, 1)
    img = image.drawCross(img, -ref.fx, -ref.fy, 30, image.CV_RED, 1)
    return img


def showImage(ax, img, win):

    h, w, d = img.shape
    border = 20
    img = image.addBorder(img, border, 127)
    extent = [-w//2-border, w//2+border-1, -h//2-border, h//2+border-1]

    if win is None:
        win = ax.imshow(img[:,:,::-1], origin="lower", extent=extent)
    else:
        win.set_data(img[:,:,::-1])
    plt.pause(0.1)
    return win


############################################################################
# Main function
############################################################################

if __name__ == "__main__":

    args = {
        "dhm": {},
        }

    user = "Reinhard"
    objective = "Zeiss 20x"
    objective = sysConfig.objective(objective)
    #path = mkdir(".test/tilt")
    opt = False
    
    fig, ax = plt.subplots()
    fig.canvas.mpl_connect("close_event", on_close)

    logger = getLogger()
    with Dhm(user, objective, logger, **args) as dhm:

        if opt:
            print("Run OPL Motor Scan...")
            dhm.motorscan()
            print("Motor pos:", dhm.device.MotorPos)

            print("Optimize Camera Exposure Time...")
            dhm.getimage(opt=True)
            #client.CameraShutter = client.CameraShutter-2
            shutter = dhm.device.CameraShutter
            shutterus = dhm.device.CameraShutterUs
            print("Shutter: %.1f us [%d]" % (shutterus, shutter))
        
        print("Start Spectrum Display Loop...")
        run = True
        win = None
        while (run):
            img = getImage(dhm)
            win = showImage(ax, img, win)
            #plt.pause(0.1)

        print("Done.")
