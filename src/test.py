#!/usr/bin/env python

from time import sleep
from random import randint
#from ConfigParser import ConfigParser

''' Read test input and change some data '''
from SQLWorker import SQLWorker
worker = SQLWorker()
while (1):
    #parser = ConfigParser()
    #parser.read('test.ini')
    #notes = parser.sections()
    #for note in notes:
    #    parser.set(note, "last_ping", int(time()))
    #with open('test.ini', 'w') as f:
    #    parser.write(f)
    life = randint(10, 100)
    worker.execute('update computers SET lifepercent=%d' % (life,))
    sleep(15)