##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module provides a class providing methods to transform between the
# coordinate systems of the stage and the camera of the Laser Nanofactory
# System from Femtika.
#
##########################################################################


class Transform(object):
    
    def __init__(self, objective):
        
        pitch = objective["cameraPitch"]
        self.pxx = pitch[0][0]
        self.pxy = pitch[0][1]
        self.pyx = pitch[1][0]
        self.pyy = pitch[1][1]
        self.x_off = 0.0
        self.y_off = 0.0
        self.z_off = objective["cameraFocus"]
        
        