##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module contains some useful functions for the usage of the
# NanoFactorySystem package.
#
##########################################################################

import logging
from pathlib import Path
from shutil import rmtree


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
