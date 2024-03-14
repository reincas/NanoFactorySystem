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

import numpy as np

LEVELS = ["init", "focus", "layer", "grid", "auto"]


class Transform(object):
    
    def __init__(self, objective):

        self.objective = objective
        self.level = 0
        self.update("init")
        
    
    @property
    def pitch(self):
        
        """ Return mean value of the horizontal and vertical calibrated pixel
        pitches of the camera in micrometre. """
        
        pitch = self.P2D
        pitch *= pitch
        pitch = np.sum(pitch, axis=1)
        pitch = np.sqrt(np.mean(pitch))
        return pitch
    
    
    @property
    def z_off(self):
        
        """ Return axial camera offset in micrometres. """
        
        return -self.P[2,2]
    
    
    @property
    def Pinv(self):
        
        """ Return three-dimensional x,y,z inverse transformation matrix in
        pixel per micrometre. """

        if self._pinv is None:
            self._pinv = np.linalg.inv(self.P)
        return self._pinv
    
    
    @property
    def P2D(self):
        
        """ Return two-dimensional x,y transformation matrix in micrometres
        per pixel. """
        
        return self.P[:2,:2]
    
        
    @property
    def Pinv2D(self):
        
        """ Return two-dimensional x,y inverse transformation matrix in pixels
        per micrometre. """
        
        return self.Pinv[:2,:2]
    
        
    def update(self, level, *args):
        
        """ Update camera calibration data at the given calibration level with
        the respective parameters. Return False and ignore the new calibration
        data, if the given level is larger than 'init' and lower than the
        current one. Return True otherwise. """
        
        # Level test
        level = LEVELS.index(level.lower())
        if level > 0 and level < self.level:
            return False
        
        # Run requested update method
        update = getattr(self, "update_%s" % LEVELS[level])
        update(*args)
        self._pinv = None
        self.level = level
        return True
    

    def update_init(self):
        
        """ Initialize the transformation matrix based on the configuration
        data of the microscope objective. """
        
        # Two-dimensional x,y transformation matrix in micrometre per pixel
        pitch = np.array(self.objective["cameraPitch"], dtype=float)
        pxx = pitch[0][0]
        pxy = pitch[0][1]
        pyx = pitch[1][0]
        pyy = pitch[1][1]
        
        # Camera offset in micrometres
        x_off = 0.0
        y_off = 0.0
        z_off = self.objective["cameraFocus"]
        
        # Three-dimensional x,y,z transformation matrix in micrometre per pixel
        self.P = np.array([[pxx, pxy, -x_off],
                           [pyx, pyy, -y_off],
                           [0.0, 0.0, -z_off]])
                

    def update_focus(self, x_off, y_off, dx_off, dy_off, num):
        
        """ Update transformation matrix with given mean camera offset in
        pixels, standard deviation and number of measurements. Return False
        and ignore the new calibration data, if the current calibration level
        is higher than 'focus'. Return True otherwise. """
        
        x_off, y_off = np.matmul(self.P2D, [x_off, y_off])
        self.P[0,2] = -x_off
        self.P[1,2] = -y_off
    

    def update_layer(self, pitch, size, err_x, err_y):
        
        """ Update transformation matrix with given two-dimensional camera
        pitch matrix in micrometres per pixel, quadratic image size, and RMS
        error resulting from the image registration algorithm. Return False
        and ignore the new calibration data, if the current calibration level
        is higher than 'layer'. Return True otherwise. """
        
        pitch = np.array(pitch, dtype=float)
        assert pitch.shape == (2, 2)
        self.P[:2,:2] = pitch
    

    def update_auto(self, z_off, dz):
        
        """ Update transformation matrix with given axial camera offset in
        micrometres and its precision. """

        self.P[2,2] = -float(z_off)
    

    def update_grid(self, A, dr):
        
        """ Update transformation matrix with given two dimensional affine
        2x3 matrix in micrometres per pixel. """

        self.P[:2,:] = A
    

    def object_pos(self, v_px, vs):
        
        """ Return object coordinates from given camera image coordinates
        based on the given stage coordinates. Object and stage coordinates are
        absolute x,y,z coordinates in micrometres, image coordinates are 
        x,y coordinates in pixels relative to the image centre. """
        
        assert len(vs) == 3
        vs = np.array(vs, dtype=float)
        assert vs.shape == (3,)
        
        if len(v_px) == 2:
            v_px = list(v_px) + [ 1.0 ]
        assert len(v_px) == 3
        v_px = np.array(v_px, dtype=float)
        assert v_px.shape == (3,)
        
        return vs + np.matmul(self.P, v_px)
    

    def camera_pos(self, v_um, vs):
        
        """ Return camera image coordinates from given object coordinates
        based on the given stage coordinates. Object and stage coordinates are
        absolute x,y,z coordinates in micrometres, image coordinates are 
        x,y coordinates in pixels relative to the image centre. """
        
        if len(vs) > 2:
            vs = vs[:2]
        assert len(vs) == 2
        vs = np.array(vs, dtype=float)
        assert vs.shape == (2,)
        
        if len(v_um) == 3:
            v_um = v_um[:2]
        assert len(v_um) == 2
        v_um = np.array(v_um, dtype=float)
        assert v_um.shape == (2,)
        
        return np.matmul(self.Pinv2D, v_um - vs)


    # def camera_rel(self, v_um):
        
    #     """ Return camera image x,y distances from given relative x,y object
    #     distances. """

    #     return self.camera_pos(v_um, [0, 0])        


    def stage_pos(self, v_um, v_px):
        
        """ Return stage coordinates required to match the given object
        coordinates to the given image coordinates. Object and stage
        coordinates are absolute x,y,z coordinates in micrometres, image
        coordinates are x,y coordinates in pixels relative to the image
        centre. """
        
        assert len(v_um) == 3
        v_um = np.array(v_um, dtype=float)
        assert v_um.shape == (3,)
        
        if len(v_px) == 2:
            v_px = list(v_px) + [ 1.0 ]
        assert len(v_px) == 3
        v_px = np.array(v_px, dtype=float)
        assert v_px.shape == (3,)
        
        return v_um - np.matmul(self.P, v_px)
