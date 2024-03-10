##########################################################################
# Copyright (c) 2023-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import logging
from scidatacontainer import load_config

from . import sysConfig

##########################################################################
# Abstract parameter class

class Parameter(object):

    """ Prototype class providing a standardized interface to export
    parameters and results of an application class to a data packege
    object. """

    _defaults = {"dummy": None}

    def __init__(self, user, logger=None, **kwargs):

        # Initialize properties
        self._params = {}

        # Store user data dictionary
        self.username = user
        self.user = sysConfig.user(user)
        self.config = load_config(
            author = self.user.get("name", None),
            email = self.user.get("email", None),
            organization = self.user.get("organization", None),
            orcid = self.user.get("orcid", None))
                
        # Store logger
        self.log = logger or logging
        
        # Store parameters
        if len(kwargs) != 1:
            raise RuntimeError("Unknown arguments section!")
        kwargs = kwargs.values[0]
        for key, value in self._defaults.items():
            if key in kwargs:
                value = kwargs.pop(key)
            self[key] = value


    def __setitem__(self, key, value):

        """ Setter method to access class parameters using the
        dictionary syntax. """

        #print("Set", key, value)
        if hasattr(self, "device") and key in self.device.keys():
            self.device[key] = value
        elif key in self._defaults:
            self._params[key] = value
        else:
            raise KeyError("Unknown item %s!" % key)
        
        

    def __getitem__(self, key):

        """ Getter method to access class parameters using the
        dictionary syntax. """
        
        #print("Get", key)
        if hasattr(self, "device") and key in self.device.keys():
            value = self.device[key]
        elif key in self._defaults:
            value = self._params[key]
        else:
            raise KeyError("Unknown item %s!" % key)
        #print("Value", value)
        return value


    def parameters(self, default=None):

        """ Return a copy of the parameter dictionary of this object updating
        the content of the optional dictionary default. """

        # Prepare default dictionary
        if default is None:
            params = {}
        else:
            assert isinstance(default, dict)
            params = dict(default)
        
        # Update with current parameters
        params.update(self._params)
        
        # Update optional device parameters
        if hasattr(self, "device"):
            for key in self.device.keys():
                params[key] = self.device[key]
        
        # Done.
        return params
