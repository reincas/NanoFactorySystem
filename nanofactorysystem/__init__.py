##########################################################################
# Copyright (c) 2023-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import logging
from pathlib import Path
from shutil import rmtree

from .parameter import Parameter
from .system import System
from .camera import Camera
from .attenuator import Attenuator
from .aerotech import A3200


##########################################################################
# Useful tools and definitions
##########################################################################

LOGFMT = logging.Formatter(fmt="%(asctime)s / %(levelname)s / %(message)s",
                           datefmt="%Y-%m-%d %H:%M:%S")

def getLogger():

    """ Return a basic console logger object. """
    
    logger = logging.getLogger('dummy')
    logger.setLevel(logging.DEBUG)

    consolehandler = logging.StreamHandler()
    consolehandler.setLevel(logging.DEBUG)
    consolehandler.setFormatter(LOGFMT)
    logger.addHandler(consolehandler)
    return logger


def mkdir(path):

    """ Make sure that the given folder exists and is empty. """

    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    for sub in p.iterdir():
        if sub.is_file():
            sub.unlink()
        elif sub.is_dir():
            rmtree(sub)
    return path
