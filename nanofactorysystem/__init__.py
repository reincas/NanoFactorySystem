##########################################################################
# Copyright (c) 2023-2024 Reinhard Caspary                               #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################

import logging
from pathlib import Path
from shutil import rmtree

from .config import Config
sysConfig = Config()

from .parameter import Parameter
from .system import System
from .camera import Camera
from .attenuator import Attenuator
from .aerotech import A3200
from .image import ImageContainer


##########################################################################
# Useful tools and definitions
##########################################################################

LOGFMT = logging.Formatter(fmt="%(asctime)s / %(levelname)s / %(message)s",
                           datefmt="%Y-%m-%d %H:%M:%S")

def getLogger(logfile=None):

    """ Configure and return a logger object. """
    
    # Initialize logger object
    logger = logging.getLogger('dummy')
    logger.setLevel(logging.DEBUG)

    # Console output
    consolehandler = logging.StreamHandler()
    consolehandler.setLevel(logging.DEBUG)
    consolehandler.setFormatter(LOGFMT)
    logger.addHandler(consolehandler)

    # Optional file output
    if logfile:
        filehandler = logging.FileHandler(logfile)
        filehandler.setLevel(logging.DEBUG)
        filehandler.setFormatter(LOGFMT)
        logger.addHandler(filehandler)
    
    # Return logger object
    return logger


def mkdir(path, clean=True):

    """ Make sure that the given folder exists and is empty. """

    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    if clean:
        for sub in p.iterdir():
            if sub.is_file():
                sub.unlink()
            elif sub.is_dir():
                rmtree(sub)
    return path


def popargs(args, sections):
    
    """ Pop given sections from an arguments dictionary. """

    if isinstance(sections, str):
        sections = (sections,)
        
    return {k: args.pop(k, {}) for k in sections}
