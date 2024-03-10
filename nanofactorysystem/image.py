##########################################################################
# Copyright (c) 2022-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module provides the ImageContainer class.
#
##########################################################################


import numpy as np
from scidatacontainer import Container


class ImageContainer(Container):

    """ SciDataContainer for the storage of digital holograms. """

    containerType = "CameraImage"
    containerVersion = 1.1

    def __pre_init__(self):

        """ Initialize all items absorbing the constructor parameters
        img and params. """

        # Not in creation mode
        if (self.kwargs["file"] is not None) or \
           (self.kwargs["uuid"] is not None):
            return
        
        # Create or update container items
        if self.kwargs["items"] is None:
            items = {}
        else:
            items = self.kwargs["items"]

        # Parameter img:np.ndarray
        img = self.kwargs.pop("img")
        if not isinstance(img, np.ndarray) or len(img.shape) != 2:
            raise RuntimeError("Hologram image expected!")

        # Parameter params:dict
        params = self.kwargs.pop("params")
        if not isinstance(params, dict):
            raise RuntimeError("Parameter dictionary expected!")

        # Container type
        content = items.get("content.json", {})
        content["containerType"] = {
            "name": self.containerType,
            "version": self.containerVersion}

        # Basic meta data
        meta = items.get("meta.json", {})
        meta["title"] = "Microscope Camera Image"
        meta["description"] = "Camera image from Matrix Vision camera."

        # Update items dictionary
        items["content.json"] = content
        items["meta.json"] = meta
        items["data/camera.json"] = params
        items["meas/image.png"] = img
        self.kwargs["items"] = items


    def __post_init__(self):

        """ Initialize this container. """

        # Type check of the container
        if (self.content["containerType"]["name"] != self.containerType) or \
           (self.content["containerType"]["version"] != self.containerVersion):
            raise RuntimeError("Containertype must be '%s'!" % self.containerType)


    @property
    def img(self):

        """ Shortcut to the camera image. """
        
        return self["meas/image.png"]


    @property
    def params(self):

        """ Shortcut to the parameter data dictionary. """
        
        return self["meas/image.json"]


