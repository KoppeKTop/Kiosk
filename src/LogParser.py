#!/usr/bin/env python

from ConfigParser import ConfigParser, ParsingError
from datetime import datetime
from configs import logFile
#class ParsingError(Exception): pass

class LogParser(object):
    def __init__(self):
        self.filename = logFile
        self.parser = ConfigParser()
        
    def parse(self):
        try:
            self.parser.read(self.filename)
        except ParsingError:
            raise ParsingError
        self.noteNames = self.parser.sections()
        self.noteNames.sort()
        self.notes = {}
        
        for note in self.noteNames:
            currNote = {}
            currNote["last_ping"] = datetime.now()
            currNote["batt"] = int(self.parser.get(note, "batt"))
            currNote["state"] = bool(int(self.parser.get(note, "state")))
            currNote["ip"] = self.parser.get(note, "ip")
            currNote["name"] = note
            currNote["broken"] = bool(int(self.parser.get(note, "broken")))
            
            self.notes[note] = currNote
            
    def SetUseReturnOldTime(self, name, inuse):
        self.parser.read(self.filename)
        self.parser.set(name, "state", int(inuse))
        with open(self.filename,'w') as f:
            self.parser.write(f)
        return datetime.now()
        
    def SetBroken(self, name, broken):
        self.parser.read(self.filename)
        self.parser.set(name, "broken", int(broken))
        with open(self.filename,'w') as f:
            self.parser.write(f)
        return datetime.now()
        
    #    
    #def ReadNotesCnt(self):
    #    res = 10
    #    
    #    return res
    #
    #def ReadNoteState(self, noteNum):
    #    state = {'works': True, 'inuse': False,
    #             'time': 0, 'batt': 100}
    #    return state
    #
    #def ReadNotesNames(self):
    