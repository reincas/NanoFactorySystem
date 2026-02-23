##########################################################################
# Copyright (c) 2023-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module provides the HoloContainer class containing a digital
# hologram.
#
##########################################################################

import numpy as np
from scidatacontainer import Container


class HoloContainer(Container):
    """ SciDataContainer for the storage of a digital hologram. """

    containerType = "HologramImage"
    containerVersion = 1.1

    def __pre_init__(self):

        """ Build items dictionary if in creation mode. """

        # Not in creation mode
        if (self.kwargs["file"] is not None) or \
                (self.kwargs["uuid"] is not None):
            return

        # Create or update container items
        if self.kwargs["items"] is None:
            items = {}
        else:
            items = dict(self.kwargs["items"])

        # Container type
        content = items.get("content.json", {})
        content["containerType"] = {
            "name": self.containerType,
            "version": self.containerVersion}

        # Basic meta data
        meta = items.get("meta.json", {})
        meta["title"] = "Hologram Image"
        meta["description"] = "Image from digital holographic microscope."

        # Update items dictionary
        items["content.json"] = content
        items["meta.json"] = meta

        # Hologram image
        holo = self.kwargs.pop("holo_get")
        holo_imgs = self.kwargs.pop("holo_images", None)
        if not isinstance(holo, np.ndarray) or len(holo.shape) != 2:
            raise RuntimeError("Hologram image expected!")
        items["meas/image.png"] = holo
        if holo_imgs is not None and holo_imgs != []:
            for i, img in enumerate(holo_imgs):
                items[f"meas/image_{i+1}.png"] = img

        # Hologram capture time
        cap_time = self.kwargs.pop("capture_time")
        cap_times = self.kwargs.pop("capture_times", None)
        if cap_times is not None and cap_times != []:
            time_dict = {"Image_0_capture_time": cap_time}
            for i, cap_time in enumerate(cap_times):
                time_dict.update({f"Image_{i+1}_capture_time": cap_time})
            items["meas/image_capture_times.json"] = time_dict
        else:
            items["meas/image_capture_time.json"] = cap_time

        # Hologram parameters
        params = self.kwargs.pop("params")
        if not isinstance(params, dict):
            raise RuntimeError("Parameter dictionary expected!")
        items["data/hologram.json"] = params

        # Objective parameters
        objective = self.kwargs.pop("objective")
        if not isinstance(objective, dict):
            raise RuntimeError("Objective dictionary expected!")
        items["data/objective.json"] = objective

        # Optional location coordinates
        loc = self.kwargs.pop("loc", None)
        if loc:
            if not isinstance(loc, dict):
                raise RuntimeError("Location dictionary expected!")
            items["data/location.json"] = loc

        # Replace container items dictionary
        self.kwargs["items"] = items

    def __post_init__(self):

        """ Initialize this container. """

        # Type check of the container
        if (self.content["containerType"]["name"] != self.containerType) or \
                (self.content["containerType"]["version"] != self.containerVersion):
            raise RuntimeError(f"Containertype must be '{self.containerType}'!")

    @property
    def img(self):

        """ Shortcut to the hologram image. """

        return self["meas/image.png"]

    @property
    def params(self):

        """ Shortcut to the parameter data dictionary. """

        return self["data/hologram.json"]

    @property
    def location(self):

        """ Return xyz position of the image or None. """

        if "data/location.json" not in self:
            return None
        return self["data/location.json"]
