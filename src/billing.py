#!/usr/bin/env python
# -*- coding: utf-8 -*-

from configs import priceForHour
from SQLWorker import SQLWorker  
from repr_stuff import ReprName, ReprMoney, ReprBigStr
from BtnStack import BtnStack
from kiosklog import logger
import time
from common_config import *

import gtk

class Billing(object):
    def __init__(self):
        # may read from DB
        # price for sec
        self.price = priceForHour
        
    def CountMoney(self, note):
        'Here we count money for note'
        if (note.time < min_time ):
            return 0
        return note.billing.price * (int(note.time/sec_in_hour)+1)

bill_query = "INSERT INTO bills (comp_id, time_used, money, session_end) VALUES (%d, %d, %d, %d)"
save_session_query = "UPDATE sessions SET stop=%d WHERE id=%d"
new_session_query = "INSERT INTO sessions (comp_id, start) VALUES (%d, %d)"
get_last_session_query = "SELECT id, comp_id, start, stop FROM sessions WHERE comp_id=%d ORDER BY id DESC LIMIT 1"
min_time=5*sec_in_min

#from threading import Thread
#
#class Bill(Thread):
#    def __init__(self, note, GetCancel=False):
#        self.note = note
#        self.GetCancel = GetCancel
#        Thread.__init__(self)
#        
#    def run(self):
#        note = self.note
#        GetCancel = self.GetCancel
#        
#        note.printing = True
#        res = None
#        s = "Работа c ноутбуком %s завершена. %s" % (ReprName(note.name, use_markup=False), ReprMoney(note.money))
#        
#        sql = SQLWorker()
#        gtk.threads_enter()
#        if (GetCancel):
#            msg = gtk.MessageDialog(flags=gtk.DIALOG_MODAL, buttons=gtk.BUTTONS_OK_CANCEL, message_format=s)
#            msg.set_position( gtk.WIN_POS_CENTER )
#            response = msg.run()
#            msg.destroy()
#            if response != gtk.RESPONSE_CANCEL:
#                if (note.time > min_time):
#                    sql.execute(bill_query % (note.id, note.time, note.money, int(time.time())))
#                res = 1
#            else:
#                res = 0
#        else:
#            if (note.time > min_time):
#                sql.execute(bill_query % (note.id, note.time, note.money, int(time.time())))
#            res = 1
#            msg = gtk.MessageDialog(flags=gtk.DIALOG_MODAL, buttons=gtk.BUTTONS_CLOSE, message_format=s)
#            msg.set_position( gtk.WIN_POS_CENTER )
#            msg.run()
#            msg.destroy()
#        
#        gtk.threads_leave()
#        if (res != 0):
#            note.SetUse(False)
#            note.time = 0
#        note.printing = False
#        return res
    
def BillNote(note):
    sql = SQLWorker()
    if (note.time > min_time):
        sql.execute(bill_query % (note.id, note.time, note.money, int(time.time())))
    if (note.inuse == True):
        note.SetUse(False)
    note.time = 0
    
    note.printing = False

def PassNote(note):
    note.printing = False

def PrintCheckForNote(note, GetCancel=False):
    note.printing = True
    ttl = "Работа c ноутбуком %s завершена. %s" % (ReprName(note.name, use_markup=False), ReprMoney(note.money))
    btns = []
    btns.append('OK')
    if (GetCancel):
        btns.append({'proc':BillNote, 'arg':note})
        btns.append('Отмена')
        btns.append({'proc':PassNote, 'arg':note})
    else:
        BillNote(note)
        btns.append({'proc':PassNote, 'arg':note})
        
    msg = BtnStack(btns, ttl)
    msg.show()

def SaveSessionInfo(note):
    """Save session info for note in use
    Changes current opened session in db 'bolt' table 'sessions'
    Attention! Session must be created explicitly!"""
    
    # End time to unlimited session
    unlim_time = 0
#    if (not note.inuse):
#        logger.error('Note %s (%s) not in use to save session info' % (note.id,note.name))
#        return
    # FIXME: workaround for new note
    if (not note.session_id):
        print "no note session id "
        return
    try:
        sql = SQLWorker()
        if (note.has_timer):
            sql.execute(save_session_query % ((note.start_time + note.timer_val), note.session_id))
        else:
            sql.execute(save_session_query % (unlim_time, note.session_id))
    except Exception, e:
        logger.error("Can't save session info to note %s: %s" % (note.name, e.message))
        
def CreateSession(note):
    """Creates new session in db 'bolt' table 'sessions'
    Changes note.session_id"""
    try:
        sql = SQLWorker()
        sql.execute(new_session_query % (note.id, note.start_time))
        last_session = GetLastSessionInfo(note)
        note.session_id = last_session['id']
        SaveSessionInfo(note)
    except Exception, e:
        logger.error("Can't create session info to note %s: %s" % (note.name, e.message)) 
    
def GetLastSessionInfo(note):
    """Creates new session in db 'bolt' table 'sessions'
    Changes note.session_id"""
    res = {}
    try:
        sql = SQLWorker()
        q_res = sql.execute(get_last_session_query % (note.id,))
        if (len(q_res) != 0 ):
            q_res= q_res[0]
            res['id'] = q_res[0]
            res['comp_id'] = q_res[1]
            res['start'] = q_res[2]
            res['stop'] = q_res[3]
    except Exception, e:
        logger.error("Can't load last session info to note %s: %s" % (note.name, e.message))
    return res 

def EndSession(note):
    note.timer_val=note.time + 1 * sec_in_min
    SaveSessionInfo(note)
    note.timer_val = 0
    
#    th = Bill(note, GetCancel=False)
#    th.start()
#    note.printing = True
#    res = None
#    s = "Работа c ноутбуком %s завершена. %s" % (ReprName(note.name, use_markup=False), ReprMoney(note.money))
#    
#    sql = SQLWorker()
#    if (GetCancel):
#        msg = gtk.MessageDialog(flags=gtk.DIALOG_MODAL, buttons=gtk.BUTTONS_OK_CANCEL, message_format=s)
#        msg.set_position( gtk.WIN_POS_CENTER )
#        response = msg.run()
#        msg.destroy()
#        if response != gtk.RESPONSE_CANCEL:
#            if (note.time > min_time):
#                sql.execute(billQuery % (note.id, note.time, note.money, int(time.time())))
#            res = 1
#        else:
#            res = 0
#    else:
#        if (note.time > min_time):
#            sql.execute(billQuery % (note.id, note.time, note.money, int(time.time())))
#        res = 1
#        msg = gtk.MessageDialog(flags=gtk.DIALOG_MODAL, buttons=gtk.BUTTONS_CLOSE, message_format=s)
#        msg.set_position( gtk.WIN_POS_CENTER )
#        msg.run()
#        msg.destroy()
#    if (res != 0):
#        note.time = 0
#    note.printing = False
#    return res
    #note.time = 0
    #print (note.id, note.time, note.money)

