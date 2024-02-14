##########################################################################
# Copyright (c) 2023-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import logging


##########################################################################
# Parameter prototype class

class Parameter(object):

    """ Prototype class providing a standardized interface to export
    parameters and results of an application class to a data packege
    object. """

    _defaults = {"a": None}

    def __init__(self, logger=None, **kwargs):

        # Initialize properties
        self._params = {}
        
        # Store logger
        if logger is None:
            self.log = logging
        else:
            self.log = logger
        
        # Store parameters
        for key, value in self._defaults.items():
            if key in kwargs:
                value = kwargs.pop(key)
            self[key] = value


    def __setitem__(self, key, value):

        """ Setter method to access class parameters using the
        dictionary syntax. """

        #print("set", key, value)
        if not key in self._defaults:
            raise KeyError("Unknown item %s!" % key)
        self._params[key] = value
        

    def __getitem__(self, key):

        """ Getter method to access class parameters using the
        dictionary syntax. """
        
        #print("get", key)
        if not key in self._defaults:
            raise KeyError("Unknown item %s!" % key)
        #print("result", self._params[key])
        return self._params[key]


    def parameters(self):

        """ Return a copy of the parameter dictionary of this object.
        """

        return dict(self._params)