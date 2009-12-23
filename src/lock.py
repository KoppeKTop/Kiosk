#!/usr/bin/env python
from run import Run
import sys

''' Lock keyboard, but don't mouse  '''

lockprogram = 'lockkbd'

class SingletonError(Exception): pass

class Locker(object):
    ''' Class locks keyboard & mouse drag '''
    instanses = 0
    stateLocked = 1
    stateUnlocked = 0
    def __init__(self, password='pass', fileName='lock.dat'):
        if Locker.instanses:
            raise SingletonError
        Locker.instanses += 1
        self.password = password
        self.fileName = fileName
        self.pid = None

    def Unlock(self):
        # TODO: kill process
        pass

    def Lock(self):
        global lockprogram
        self.pid = Run(lockprogram, [self.password, self.fileName])
            
    def Status(self):
        '''returns True, if object locked
        False - otherwise'''
        res = Locker.stateLocked
        with open(self.fileName, "r") as f:
            if (f.read() != ''):
                res = Locker.stateUnlocked
        return res

def main():
    ''' test cases '''
    if (len(sys.argv) != 1):
        lock = Locker(sys.argv[1:])
    else:
        lock = Locker()
    lock.Lock()

if __name__ == '__main__':
    main()
