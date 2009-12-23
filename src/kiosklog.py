'''
Created on 05.12.2009

@author: andrey
'''

from configs import log_file, default_error, debug
import os.path as path
import logging
import logging.config

class LoadLogError(Exception):
    pass

try:
    logging.config.fileConfig(path.expanduser(log_file))
    # create logger
    logger = logging.getLogger("KioskLogger")
    if (debug):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
except Exception, e:
    with open(default_error, 'w') as err:
        err.write("Can't load config file from %s.\nError: %s\n" % (log_file,e.message))
    # FIXME: Create self logging class
    raise LoadLogError(e)

