##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module provides the class Config as configuration wrapper for the
# SQLite configuration database of the Laser Nanofactory System from
# Femtika for the NanoFactorySytem library.
#
##########################################################################

import json
from pathlib import Path


# def norm_orcid(orcid):
    
#     """ Return normalized ORCiD string if the given string is a valid ORCiD
#     and None otherwise. In fact it currently checks only if the string is a
#     valid International Standard Name Identifier (ISNI). ORCiD uses a certain
#     ISNI number space, which is not tested here. """
    
#     assert isinstance(orcid, str)
    
#     # Pick all digits and normalize
#     orcid = orcid.replace("-", "").replace(" ", "").upper()
#     if len(orcid) != 16:
#         return None
    
#     # Calculate checksum product
#     R = 2
#     M = 11
#     try:
#         product = 0
#         for digit in orcid[:-1]:
#             product = ((int(digit) + product) * R) % M
#     except ValueError:
#         return None

#     # Calculate checksum digit
#     check = (M + 1 - product) % M
#     check = "0123456789X"[check]
#     if orcid[-1] != check:
#         return None
    
#     # Return pretty formatted ORCiD string
#     return orcid[:4] + "-" + orcid[4:8] + "-" + orcid[8:12] + "-" + orcid[12:]


class Config(object):
    
    _path = Path(Path.home(), "nanofactory.json")

    def __init__(self, path=None):
        
        if path is None:
            path = self._path
            
        with open(path, "rb") as fp:
            config = fp.read()
        self.config = json.loads(config)


    def keys(self):
        
        return [k for k,v in self.config.items() if not isinstance(v, dict)]
    

    def sections(self):
        
        return [k for k,v in self.config.items() if isinstance(v, dict)]
    
    
    def users(self):
        
        return [k[5:] for k in self.config.keys() if k[:5] == "user:"]


    def objectives(self):
        
        return [k[10:] for k in self.config.keys() if k[:10] == "objective:"]


    def user(self, key):
        
        if key not in self.users():
            raise RuntimeError("Unknown user '%s'!" % key)
        return self.config["user:%s" % key] | {"key": key}
    
    
    def objective(self, key):
        
        if key not in self.objectives():
            raise RuntimeError("Unknown objective '%s'!" % key)
        return self.config["objective:%s" % key] | {"key": key}
    
    
    def __getattr__(self, key):

        if key in self.keys():
            return self.config[key]
        elif key in self.sections():
            return dict(self.config[key])
        raise AttributeError("Unknown attribute '%s'!" % key)
        
    
    def __str__(self):
        
        lines = []
        for key in sorted(self.keys()):
            lines.append(("%s = %s" % (key, getattr(self, key))))
            
        for skey in sorted(self.sections()):
            section = getattr(self, skey)
            
            lines.append(("[%s]" % skey))
            for key in sorted(section):
                lines.append(("    %s = %s" % (key, section[key])))
        
        return "\n".join(lines)
