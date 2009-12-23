#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from LogParser import LogParser
from billing import Billing, PrintCheckForNote, CreateSession, EndSession,\
    SaveSessionInfo, GetLastSessionInfo

from SQLParser import LogParser
from SQLWorker import SQLWorker
#from LogParser import LogParser

from datetime import datetime, timedelta
#from run import Run 

from configs import availableExpCnt, logInterval, show_continue_msg_timer

from kiosklog import logger
from repr_stuff import ReprName
from common_config import sec_in_hour, sec_in_min
from BtnStack import BtnStackTimer
import time

def PingIP(ip, cnt=1):
    pass
#    if (cnt != 0):
#        Run('ping', ['-c', str(cnt), ip], silent=True)
#    else:
#        Run('ping', [ip], silent=True)

def GetTimeDeltaInSec(t):
    #sec_in_day = 3600*24
    try:
        #delta = datetime.now() - t
        res = int(time.time()) -t 
        #res = delta.days*sec_in_day + delta.seconds
    except Exception, e:
        logger.error("In GetTimeDeltaInSec(%s): %s" % (str(t), e.message))
        raise Exception(e)
    logger.debug( "GetTimeDelta. In: %s res: %s" % (str(t), str(res)))
    return res

class Note(object):
    def __init__(self, name, billing, log):
        self.name = name
        self.log = log
        # default values
        # is note on flag
        self.works = True
        # is note in use flag
        self.inuse = False
        # time meter
        self.oldtime = 0
        self.time = 0
        self.start_time = None
        # money meter
        self.money = 0
        self.billing = billing
        # battery meter 
        self.batt = 100
        self.ip = ''
        try:
            self.worker = SQLWorker()
        except Exception, e:
            logger.error('Note init. %s' % (e.message, ))
        self.broken = False
        self.turnedOn = True
        self.get = False
        self.ignoreTurnOff = False
        self.ignore_ping = datetime.now()
        
        self.first_time = True
        self.printing = False
        
        self.has_timer = False
        self.timer_val = 0
        
        self.session_id = None
        self.ui = None
        
    def SetUI(self):
        import UI
        self.ui = UI.UI()
        
    def Update(self, stateDict):
        self.id = stateDict['id']
        
        if(self.first_time and stateDict['state'] == 1):
            self.first_time = False
            # load last session info: session_id + start + stop time
            last_session = GetLastSessionInfo(self)
            if (not last_session):
                self.SetStatus(status=2)
                return
            # if stop time not in the past: use=True, create timer for note
            if (last_session['stop'] > int(time.time())):
                self.inuse = True
                self.start_time = last_session['start']
                self.session_id = last_session['id']
                self.has_timer = True
                self.timer_val = last_session['stop'] - last_session['start']
            # if time unlimited use = True
            elif (last_session['stop'] == 0):
                self.inuse = True
                self.start_time = last_session['start']
            # else - we only close note session
            else:
                self.SetStatus(status=2)
            
            return
        
        if (self.printing): return
        
        if ((stateDict['state'] == 2 or stateDict['state'] == 0) and self.inuse):
            # client turned off the computer
            self.get = True
            self.SetUse(False, status=0)
            PrintCheckForNote(self)
            
        if (stateDict['state'] == 1 and not self.inuse):
            # inuse
            self.SetUse(True)

        self.broken = stateDict['broken']
        #if self.broken: return
        self.last_ping = stateDict['last_ping']
        if (self.oldtime == 0):
            self.oldtime = self.last_ping
            
        logger.debug('Last ping: %s, old time: %s' % (str(self.last_ping), str(self.oldtime)))
        
        try:
            expTimeInSec = GetTimeDeltaInSec(self.oldtime)
        except Exception, e:
            logger.error("Note.Update (102) for %s: %s" % (self.name, e.message))
            raise Exception(e)
        
        logger.debug( 'expTimeInSec %s' % (str(expTimeInSec),))

        if self.inuse:
            logger.debug('last ping: %s, oldtime %s' % (str(self.last_ping), str(self.oldtime)))
            #if (self.last_ping != self.oldtimeself.get = True):
            #self.time += min (expTimeInSec, logInterval)
            #self.time += expTimeInSec
            try:
                self.time = GetTimeDeltaInSec(self.start_time)
            except Exception, e:
                logger.error("Note.Update (115) for %s: %s" % (self.name, e.message))
                raise Exception(e)
            
            self.oldtime = int(time.time()) 
            self.money = self.billing.CountMoney(self)
            if (self.has_timer):
                if (self.time > self.timer_val):
                    self.time = (self.timer_val-1)
                    self.money = self.billing.CountMoney(self)
                    self.ShowContinueWnd()
                    #self.SetUse(False)
                    #PrintCheckForNote(self, GetCancel=False)
        else:
            if (self.time != 0):
                # using was changed externally
                PrintCheckForNote(self)
            self.oldtime = self.last_ping
        
        try:
            lp = GetTimeDeltaInSec(self.last_ping)
        except Exception, e:
            logger.error("Note.Update (136) for %s: %s" % (self.name, e.message))
            raise Exception(e)
        
        
        self.batt = min([int(stateDict['batt']), 100])
        self.ip = stateDict['ip']
        PingIP(self.ip)
        self.id = stateDict['id']
        
        #if (self.inuse):
            # Ignore note signals
        return
        
        if (lp > logInterval*availableExpCnt and not self.inuse):
            self.turnedOn = False
        elif ( not self.IsPingIgnored()) :
            self.turnedOn = True
            self.ignoreTurnOff = False
            if (self.broken):
                self.SetBroken(False)
                logger.debug("Update note Timedelta: %s" % (str(lp), ))
        
        
    def CopyState(self, otherNote):
        # default values
        # is note on flag
        # is note in use flag
        # time meter
        self.oldtime = otherNote.oldtime
        self.start_time = otherNote.start_time
        self.time = otherNote.time
        self.has_timer = otherNote.has_timer
        self.timer_val = otherNote.timer_val 
        # money meter
        self.money = otherNote.money
        otherNote.time  = 0
        otherNote.money = 0
        # battery meter
        
    def SetUse(self, use, status=None):
        self.inuse = use
        if (use == True):
            self.start_time = int(time.time())
            CreateSession(self)
        if (use == False):
            EndSession(self)
            self.has_timer = False
        self.oldtime = self.log.SetUseReturnOldTime(self.id, use, status)
        self.IgnorePing()
        
    def SetStatus(self, status):
        self.log.SetUseReturnOldTime(self.id, None, status)
        
    def SetBroken(self, broken):
        self.log.SetBroken(self.id, broken)
        self.SetUse(False)
        self.broken = broken
        self.IgnorePing()

    def IgnorePing(self):
        self.ignore_ping = datetime.now() + timedelta(seconds=logInterval*availableExpCnt)

    def IsPingIgnored(self):
#        if debug:
#            logger.debug('IsPingIgnored %s' % (self.ignore_ping, self.ignore_ping)
        return self.ignore_ping > datetime.now()
    
    def SetTimer(self, time_in_sec):
        self.has_timer = True
        self.timer_val = time_in_sec
        
    def AddTime(self, time_to_add):
        if (not self.has_timer):
            logger.critical("Note %s doesn't has timer, but AddTimer used" % (ReprName(self.name), ))
        else:
            self.timer_val += time_to_add
            SaveSessionInfo(self)
            
    def ShowContinueWnd(self):
        self.printing = True
        self.SetStatus(status=0)
        btns_ref = ('Продолжить использование', {'proc': self.ContinueUsing, 'arg':None}, 'Завершить работу', {'proc':self.FinishWork, 'arg':None})
        timer_end_func = {'proc': self.FinishWork, 'arg': None}
        self.stack_wnd = BtnStackTimer(btns=btns_ref, timer_end_func=timer_end_func, 
                                       timer=show_continue_msg_timer*sec_in_min, 
                                       title = 'Время работы с ноутбуком %s истекло' % (self.name,))
        
    def ContinueUsing(self):
        self.AddTime(sec_in_hour)
        self.SetStatus(status=1)
        self.printing = False
        if (not self.ui):
            self.SetUI()
        self.ui.Update()
        
    def FinishWork(self):
        self.SetUse(False)
        PrintCheckForNote(self, GetCancel=False)
        self.printing = False
        if (not self.ui):
            self.SetUI()
        self.ui.Update()

class NoteControl(object):
    def __init__(self, filename):
        self.log = LogParser()
        self.log.parse()
        self.noteNames = self.log.noteNames[:]
        self.noteNames.sort()
        self.notes = {}
        for name in self.noteNames:
            self.notes[name] = Note(name, Billing(), self.log)
        self.Update()
        
    def Update(self):
        self.log.parse()
        for name in set(self.log.noteNames).difference(set(self.noteNames)):
            self.notes[name] = Note(name, Billing(), self.log)
            
        for name in set(self.noteNames).difference(set(self.log.noteNames)):
            del self.notes[name]
            
        self.noteNames = self.log.noteNames[:]
        self.noteNames.sort()
        for noteName, note in self.notes.items():
#            try:
            if (True):
                note.Update(self.log.notes[noteName])
#            except Exception, e:
#                logger.error('Error in Update in NoteControl. %s' % (e.message,))
            logger.debug('Update NoteControl %s' % (str(self.log.notes[noteName]), ))

