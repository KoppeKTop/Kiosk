#!/usr/bin/env python

from NoteControl import NoteControl
#from lock import Locker
from UI import UI
from kiosklog import logger

def main():
    logger.info('Start Kiosk')
#    try:
    if (True):
        NC = NoteControl("test.ini")
        window = UI(NC)
        window.main()
#    except Exception, e:
#        logger.error('Unable to start Kiosk. %s' % (e.message,))
    logger.info('Kiosk finished')

if __name__ == '__main__':
    main()