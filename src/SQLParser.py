#!/usr/bin/env python

import SQLWorker
#from configs import debug
import time

get_note_state_query = "SELECT id, ip, lifepercent, lastupdate, state, broken FROM computers ORDER BY id"

lock_query = "UPDATE computers SET state=2 WHERE id=%d" 
set_state_query = "UPDATE computers SET state=%d WHERE id=%d"
unlock_query = "UPDATE computers SET state=1 WHERE id=%d"

set_broken_query = "UPDATE computers SET broken=1 WHERE id=%d"
unset_broken_query = "UPDATE computers SET broken=0 WHERE id=%d" 

get_time_query = "SELECT lastupdate FROM computers WHERE id=%d"

get_last_bills = "SELECT b.id, c.ip, b.time_used, b.money, b.session_end FROM bills b LEFT JOIN computers c ON b.comp_id=c.id WHERE b.session_end>%s"
get_last_n_bills = "SELECT b.id, c.ip, b.time_used, b.money, b.session_end FROM bills b LEFT JOIN computers c ON b.comp_id=c.id ORDER BY b.id DESC LIMIT 0, %d"

from kiosklog import logger

def IP2Name(ip):
    return '%02d' % int(ip.split('.')[-1])

class LogParser(object):
    def __init__(self, filename=''):
        try:
            self.worker=SQLWorker.SQLWorker()
        except Exception, e:
            logger.error('Init LogParser. %s' % (e.message,))
        #self.filename = filename
        
        
    def parse(self):
        dbData = self.worker.execute(get_note_state_query)
        logger.debug("DB data in SQLParser:\n%s" % (str(dbData), ) )
        
        #print self.noteNames
        #self.noteNames = self.parser.sections()
        self.notes = {}
        
        for noteState in dbData:
            currNote = {}
            currNote["last_ping"] = int( time.mktime( noteState[3].timetuple() ) )
            currNote["batt"] = noteState[2]
            currNote["state"] = noteState[4]
            currNote["ip"] = noteState[1]
            currNote["name"] = IP2Name(currNote["ip"]) # last number in IP
            currNote["broken"] = noteState[5]
            currNote["id"] = noteState[0]
            
            self.notes[currNote["name"]] = currNote
        self.noteNames = self.notes.keys()
            
    def SetUseReturnOldTime(self, _id, use, state=None):
        if (state != None): 
            q = set_state_query % (state, _id)
        else:
            if (use):
                q = unlock_query % (_id,)
            else:
                q = lock_query % (_id,)
        self.worker.execute(q)
        return int( time.mktime( self.worker.execute(get_time_query % (_id,))[0][0].timetuple() ) )
        
    def SetBroken(self, _id, broken):
        if (broken):
            q = set_broken_query % (_id,)
        else:
            q = unset_broken_query % (_id,)
        
        logger.debug('query in SetBroken: %s' % (q,))
        self.worker.execute(q)
        
    def StatToDict(self, stat):
        res = []
        for session in stat:
            curr_ses = {}
            curr_ses['id'] = session[0]
            curr_ses['name'] = IP2Name(session[1])
            curr_ses['time_used'] = session[2]
            curr_ses['money'] = session[3]
            curr_ses['session_end'] = session[4]
            res.append(curr_ses)
        return res
        
    def GetStatAfterDate(self, date):
        stamp = int( time.mktime( date.timetuple() ) ) 
        q = get_last_bills % (stamp,)
        out = self.worker.execute(q)
        return self.StatToDict(out)
            
    def GetLastNStat(self, count):
        q = get_last_n_bills % (count,)
        out = self.worker.execute(q)
        res = self.StatToDict(out)
        res.reverse()
        return res
        
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
