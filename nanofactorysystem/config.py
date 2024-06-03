##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module reads the configuration file of the NanoFactorySystem package
# as object sysConfig, which is an instance of the class Config. It also
# provides the helper function popargs, which takes one or more sections from
# a runtime configuration dictionary.
#
##########################################################################

import json
from pathlib import Path
from typing import Any


# def norm_orcid(orcid):

#     """ Return normalized ORCiD string if the given string is a valid ORCiD
#     and None otherwise. In fact, it currently only checks if the string is a
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


def popargs(args, sections):
    """ Pop given sections from an arguments dictionary. """

    if isinstance(sections, str):
        sections = (sections,)

    return {k: args.pop(k, {}) for k in sections}


class Config(object):
    _path = Path.home() / "nanofactory.json"

    def __init__(self, path=None):

        if path is None:
            path = Config._path

        with open(path, "rb") as fp:
            config = fp.read()
        self.config = json.loads(config)

    def keys(self):

        return [k for k, v in self.config.items() if not isinstance(v, dict)]

    def sections(self):

        return [k for k, v in self.config.items() if isinstance(v, dict)]

    def users(self) -> list[str]:

        return [k[5:] for k in self.config.keys() if k[:5] == "user:"]

    def objectives(self) -> list[str]:

        return [k[10:] for k in self.config.keys() if k[:10] == "objective:"]

    def user(self, key: str) -> dict[str, Any]:

        if key not in self.users():
            raise RuntimeError(f"Unknown user '{key}'!")
        return self.config[f"user:{key}"] | {"key": key}

    def objective(self, key: str) -> dict[str, Any]:

        if key not in self.objectives():
            raise RuntimeError(f"Unknown objective '{key}'!")
        return self.config[f"objective:{key}"] | {"key": key}

    def __getattr__(self, key: str):

        if key in self.keys():
            return self.config[key]
        elif key in self.sections():
            return dict(self.config[key])
        raise AttributeError(f"Unknown attribute '{key}'!")

    def __str__(self) -> str:

        lines = []
        for key in sorted(self.keys()):
            lines.append(f"{key} = {getattr(self, key)}")

        for skey in sorted(self.sections()):
            section = getattr(self, skey)

            lines.append(f"[{skey}]")
            for key in sorted(section):
                lines.append(f"    {key} = {section[key]}")

        return "\n".join(lines)


# Read the current config file
sysConfig = Config()
