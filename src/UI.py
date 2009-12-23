#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
Created on 16.10.2009

@author: andrey
'''
#from SQLParser import LogParser
from BtnStack import BtnStackTimer

import gtk
import gobject
import math
import os.path as path
#import time
from NoteControl import NoteControl, PingIP
from configs import logInterval, unlockPass, contacts_file, stat_lines, coffe_open_hour
from lock import Locker
from billing import PrintCheckForNote
from datetime import datetime, timedelta

from repr_stuff import *

from kiosklog import logger
#from threading import Thread

from BtnStack import BtnStack#, ButtonsArrange

from common_config import *

def delete_event(widget, event, data=None):
    return False
    
def destroy(widget, data=None):
    gtk.main_quit()
    
gtk_states = [gtk.STATE_NORMAL, gtk.STATE_ACTIVE, gtk.STATE_PRELIGHT,
              gtk.STATE_SELECTED, gtk.STATE_INSENSITIVE]

def GetSqrtCnt(cnt):
    res = int(math.sqrt(cnt)+1)
    if ((res-1)**2 == cnt): res = res-1
    return res

def GetColourFromBatt(charge):
    MAX=65535
    #grad = charge/100. * math.pi/2
    charge -=10
    if charge <= 0:
        r = MAX
        g = 0
    elif charge <= 45:
        r = MAX
        g = int(charge/45. * MAX)
    else:
        r = int((1-(charge-45)/45.) * MAX)
        g = MAX
        
    #r = int(math.cos(grad)*MAX)
    #g = MAX-r
    #r=g=int(0.5*MAX)
    b=0

    return gtk.gdk.Color(red=r, green=g, blue=b) #@UndefinedVariable
        
ChangeNoteWnd = None

def UpdateColourFromCharge(widg, charge):
    style = widg.get_style().copy()
    for k in gtk_states:
        style.bg[k] = GetColourFromBatt(charge)
    widg.set_style(style)

def StartChangeWin(note, ui, show_no_note_msg=True, bill_if_none=False, bill_if_cancel=False, unset_use = True):
    wnd = ChangeNoteWnd(note, ui, bill_if_cancel)
    res = False
    if not wnd.bad:
        wnd.show()
        res = True
    else:
        if (unset_use):
            note.SetUse(False)
        if (show_no_note_msg):
            msg = gtk.MessageDialog(parent=ui.win, flags=gtk.DIALOG_MODAL, buttons=gtk.BUTTONS_CLOSE, message_format="Нет свободных ноутбуков.")
            msg.run()
            msg.destroy()
        if (bill_if_none):
            PrintCheckForNote(note)
        res = False
    return res

def SetDefFocus(widget):
    widget.set_focus_on_click(False)
    widget.can_focus = False


class InUseWidget(gtk.Table):
    def __init__(self, ui, note):
        if (note.has_timer):
            rows = 3
        else:
            rows = 2
        cols = 6
        gtk.Table.__init__(self, rows, cols, True)
        
        self.ui = ui
        self.note = note
        
        self.panel = gtk.Button(label = None)
        SetDefFocus(self.panel)

        self.attach(self.panel, 0, cols-2, 0, rows)
        self.stateLabel = gtk.Label()
        self.stateLabel.set_justify(gtk.JUSTIFY_CENTER)
        self.stateLabel.set_use_markup(True)
        self.panel.add(self.stateLabel)
        
        self.stopBtn = gtk.Button("Стоп")
        SetDefFocus(self.stopBtn)
        self.attach(self.stopBtn, cols-2, cols, 0, 1)
        self.stopBtn.connect("clicked", self.FinishClick, self)
        #self.stopBtn.show()
        
        self.changeBtn = gtk.Button("Сменить\nноутбук")
        SetDefFocus(self.changeBtn)
        self.attach(self.changeBtn, cols-2, cols, rows-1, rows)
        self.changeBtn.connect("clicked", self.ChangeNoteClick, self)
        
        if (self.note.has_timer):
            self.addHourBtn = gtk.Button("+")
            SetDefFocus(self.addHourBtn)
            self.attach(self.addHourBtn, cols-2, cols-1, 1, 2)
            self.addHourBtn.connect("clicked", self.AddHourClick, self)
            
            self.subHourBtn = gtk.Button("-")
            SetDefFocus(self.subHourBtn)
            self.attach(self.subHourBtn, cols-1, cols, 1, 2)
            self.subHourBtn.connect("clicked", self.SubHourClick, self)
        
        self.default_style = self.get_style().copy()
        
        self.show_all()
        #self.changeBtn.show()
        
    def Update(self):
        name = ReprName(self.note.name)
        time = ReprSecondsWithTimer(self.note, big=True)
        money = ReprMoney(self.note.money)
        batt = ReprBatt(self.note.batt)
        used = ReprBigStr("Используется")
        self.stateLabel.set_markup('\n'.join([name, time, money, batt, used]))
        #self.stateLabel.set_text('\n'.join([name, time, money, batt, used]))
        
        UpdateColourFromCharge(self.panel, self.note.batt)
        
        return True
        
    def FinishClick(self, widget, event):
        PrintCheckForNote(self.note, GetCancel=True)
#        if (resp != 1):
#            return
#        self.note.SetUse(False)
#        
#        self.ui.Update()
        
    def ChangeNoteClick(self, widget, event):
        #self.ui.win.set_keep_above(False)
        StartChangeWin(self.note, self.ui, unset_use=False)
        
    def AddHourClick(self, widget, event):
        self.note.AddTime(sec_in_hour)
        self.Update()
        
    def SubHourClick(self, widget, event):
        if (self.note.timer_val > sec_in_hour and self.note.time < self.note.timer_val-sec_in_hour):
            self.note.AddTime(-sec_in_hour)
            self.Update()

class FreeWidget(gtk.Table):
    def __init__(self, ui, note):
        self.rows = 2
        self.cols = 3
        gtk.Table.__init__(self, self.rows, self.cols, True)
        
        self.ui = ui
        self.note = note
        
        self.panel = gtk.Button(label = None)
        SetDefFocus(self.panel)
        self.attach(self.panel, 0, self.cols, 0, self.rows)
        
        self.stateLabel = gtk.Label()
        self.stateLabel.set_use_markup(True)
        self.stateLabel.set_justify(gtk.JUSTIFY_CENTER)
        self.panel.add(self.stateLabel)
        self.show_all()
        
        self.panel.connect("clicked", self.StartClick, self)
        
        self.old_style=self.get_style()
        self.cancel_response = 65
        
    def Update(self):
        name = ReprName(self.note.name)
        batt = ReprBatt(self.note.batt)
        free = ReprBigStr('Свободен')
        self.stateLabel.set_markup('\n'.join([name, batt, free]))
        
        UpdateColourFromCharge(self.panel, self.note.batt)
        
        return True
        
    def GetStartDialog(self):
        btns_set = ("1 час", {'proc':self.Start, 'arg': 1}, 
                    "2 часа", {'proc':self.Start, 'arg': 2}, 
                    "3 часа", {'proc':self.Start, 'arg': 3}, 
                    "Без ограничения", {'proc':self.Start, 'arg': 0}, 
                    "Отмена", {'proc':self.Start, 'arg': self.cancel_response})
        ttl = "Начать работу с ноутбуком %s" % (ReprName(self.note.name, use_markup=False),)
        msg = BtnStack(btns_set, ttl)
        msg.show()
        
#        msg = gtk.Dialog(title="Начать работу с ноутбуком %s" % (ReprName(self.note.name, use_markup=False),), 
#                         parent=self.ui.win, 
#                         flags=gtk.DIALOG_MODAL, 
#                         buttons=btns_set)
#        #msg = gtk.MessageDialog(flags=gtk.DIALOG_MODAL, buttons=gtk.BUTTONS_OK_CANCEL, message_format=s)
#        msg.set_position( gtk.WIN_POS_CENTER )
#        response = msg.run()
#        msg.destroy()
#        return response
        
    def StartClick(self, widget, event):
        self.GetStartDialog()
    
    def Start(self, time):
        if (time != self.cancel_response):
            if (time != 0):
                self.note.SetTimer(time*sec_in_hour)
            self.note.SetUse(True)
        self.ui.Update()
        
class BrokenWidget(FreeWidget):
    def Update(self):
        self.stateLabel.set_markup('Ноутбук %s сломан\nВключить' % (self.note.name, ))
        return True
        
    def StartClick(self, widget, event):
        self.note.SetBroken(False)
        self.note.turnedOn=True
        self.ui.Update()
        
class TurnedOffWidget(FreeWidget):
    def __init__(self, ui, note):
        self.rows = 2
        self.cols = 3
        gtk.Table.__init__(self, self.rows, self.cols, True)
        
        self.ui = ui
        self.note = note
        
        self.panel = gtk.Button(label = 'Нет сигнала \nот ноутбука\n%s\nВключите ноутбук' %(self.note.name ,))
        SetDefFocus(self.panel)
        self.attach(self.panel, 0, self.cols-1, 0, self.rows)
        
        self.turnOffBtn = gtk.Button("Ноутбук\nсломан")
        SetDefFocus(self.turnOffBtn)
        self.attach(self.turnOffBtn, self.cols-1, self.cols, 0, self.rows)
        self.turnOffBtn.connect("clicked", self.TurnOffClick, self)
        
        self.oldstyle=self.get_style()
        
        self.show_all()
    
    def Update(self):
        return True
        
    def StartClick(self, widget, event):
        pass
        #self.lockWatch_id = gobject.timeout_add(1000, self.LockWatcher)
        
    def TurnOffClick(self, widget, event):
        self.note.SetBroken(True)
        self.ui.Update()
        
class ChangeFreeWidget(FreeWidget):
    def __init__(self, ui, note, changeWin):
        FreeWidget.__init__(self, ui, note)
        self.changeWin = changeWin
        
    def StartClick(self, widget, event):
        self.note.SetUse(True)
        self.note.CopyState(self.changeWin.currentNote)
        self.changeWin.currentNote.SetUse(False)
        self.changeWin.destroy() 
        self.ui.Update()
        
class GetWidget(FreeWidget):
    def Update(self):
        self.stateLabel.set_markup(ReprBigStr('Ноутбук %s был выключен\nзаберите у клиента' % (self.note.name, ), use_markup=False))
        return True

    def StartClick(self, widget, event):
        self.note.get = False
        self.ui.Update() 

class ChangeNoteWnd(gtk.Window):
    def __init__(self, currentNote, ui, bill_if_cancel=False):
        
        self.currentNote = currentNote
        self.ui = ui
        self.nc = ui.nc
        self.noteChoise = [name for name, note in self.nc.notes.items()
                           if (not note.inuse) and (not note.broken)]
        self.noteChoise.sort()
        
        self.cnt = len(self.noteChoise)
        rowsPerWidget = 3
        rowsCloseBtn = 1
        self.cols = GetSqrtCnt(self.cnt)
        self.rows = self.cols* rowsPerWidget + rowsCloseBtn
        fullWidgCnt = self.cols*self.cols
        if (self.cnt == 0):
            self.bad = True
            return
        self.bad = False
        
        gtk.Window.__init__(self, type=gtk.WINDOW_POPUP)
        self.set_modal(True)
        self.set_keep_above(True)
        
        step_y=50
        step_x=100
        
        scr_w = gtk.gdk.screen_width() #@UndefinedVariable
        scr_h = gtk.gdk.screen_height() #@UndefinedVariable
        
        width = scr_w-step_x*2
        height = scr_h-step_y*2
        
        maxBtnSize_x = scr_w/4
        maxBtnSize_y = scr_h/4
        if (width/self.cols > maxBtnSize_x or height/self.cols > maxBtnSize_y):
            width = self.cols * maxBtnSize_x
            height = self.cols * maxBtnSize_y
            step_x = (scr_w-width)/2
            step_y = (scr_h-height)/2
        
        self.set_default_size(width, height)
        self.move(step_x, step_y)
        
        self.connect("delete_event", self.delete_event)
        self.btn_box = gtk.VBox()
        self.table = gtk.Table(self.rows, self.cols, True)
        
        self.grid_widgets = []
        for name in self.noteChoise:
            self.grid_widgets.append(ChangeFreeWidget(ui, self.nc.notes[name], self))
            gobject.timeout_add(logInterval*msec_in_sec, self.grid_widgets[-1].Update)
            self.grid_widgets[-1].Update()
        for i in xrange(self.cnt, fullWidgCnt):
            self.grid_widgets.append(gtk.Frame(label=None))
            
        self.add(self.btn_box)
        #self.ttl = gtk.Button("Выберите ноутбук на замену")
        #self.btn_box.pack_start(self.ttl)
        self.closeBtn = gtk.Button("Закрыть")
        SetDefFocus(self.closeBtn)
        #self.closeBtn.set_size_request(width/20, height)
        self.closeBtn.connect("clicked", self.CloseBtnClick, self)
        
        self.btn_box.pack_start(self.table)
        
        self.table.attach(self.closeBtn, 0, self.cols, 0, rowsCloseBtn)
        for i, widg in enumerate(self.grid_widgets):
            y,x = divmod(i, self.cols)
            
            self.table.attach(widg, x, x+1, y*rowsPerWidget+rowsCloseBtn, (y+1)*rowsPerWidget+rowsCloseBtn)
            
        #self.logWatch = gobject.timeout_add(logInterval*1000, self.LogWatcher)
        self.bill_if_cancel = bill_if_cancel
        self.show_all()
        self.Update()
        
    def CloseBtnClick(self, widget, event):
        if (self.bill_if_cancel):
            #self.currentNote.SetUse(False)
            PrintCheckForNote(self.currentNote)
        self.destroy()
        
    def LogWatcher(self):
        self.nc.Update()
        self.Update()
        return True
    
    def delete_event(self, widget, event, data=None):
        #self.ui.win.set_keep_above(True)
        return False
        
    def Update(self):
        for wdg in self.grid_widgets:
            try:
                wdg.Update()
            except AttributeError:
                # ''' This widget is not ours '''
                continue

class TurnedOffInUseWidget(TurnedOffWidget):
    def __init__(self, ui, note):
        self.rows = 3
        self.cols = 3
        gtk.Table.__init__(self, self.rows, self.cols, True)
        
        self.ui = ui
        self.note = note
        
        self.panel = gtk.Button()
        SetDefFocus(self.panel)
        self.mainLbl = gtk.Label()
        self.mainLbl.set_justify(gtk.JUSTIFY_CENTER)
        self.mainLbl.set_use_markup(True)
        self.mainLbl.set_markup('Нет сигнала от ноубука\n%s\nПроверьте состояние'%(self.note.name,))
        self.panel.add(self.mainLbl)
        self.attach(self.panel, 0, self.cols-1, 0, self.rows)
        
        self.brokenBtn = gtk.Button("Ноутбук\nсломан")
        SetDefFocus(self.brokenBtn)
        self.attach(self.brokenBtn, self.cols-1, self.cols, 0, 1)
        self.brokenBtn.connect("clicked", self.BrokenClick, self)
        
        self.clientBtn = gtk.Button("Ноутбук\nу клиента")
        SetDefFocus(self.clientBtn)
        self.attach(self.clientBtn, self.cols-1, self.cols, 1, 2)
        self.clientBtn.connect("clicked", self.ClientClick, self)
        
        self.endBtn = gtk.Button("Закончить\nработу")
        SetDefFocus(self.endBtn)
        self.attach(self.endBtn, self.cols-1, self.cols, 2, 3)
        self.endBtn.connect("clicked", self.EndClick, self)
        
        self.show_all()
    
            
    def BrokenClick(self, widget, event):
        self.note.SetBroken(True)
        StartChangeWin(self.note, self.ui, bill_if_none=True, bill_if_cancel=True)
        self.note.SetUse(False)
        self.ui.Update()

    def ClientClick(self, widget, event):
        self.note.ignoreTurnOff = True
        self.ui.Update()

    def EndClick(self, widget, event):
        #self.note.SetUse(False)
        PrintCheckForNote(self.note)
        self.ui.Update()

class LockBtn(gtk.Button):
    def __init__(self, ui):
        gtk.Button.__init__(self, 'Заблокировать')
        SetDefFocus(self)
        self.ui = ui
        self.connect("clicked", self.LockClick, self)
        self.show_all()
        
    def LockClick(self, widget, event):
        self.ui.lockScr()

def GetWidgetType(note):
    if note.broken:
        return BrokenWidget
    if note.get:
        return GetWidget
    if note.inuse:
        if note.turnedOn or (not note.turnedOn and note.ignoreTurnOff):
            return InUseWidget
        else:
            return TurnedOffInUseWidget
    if not note.turnedOn:
        return TurnedOffWidget
    return FreeWidget

class StatForm(gtk.Window):
    def __init__(self, log, parent=None):
        now  = datetime.now()
        end_date = datetime(year=now.year, month=now.month, day=now.day, hour=now.hour, minute=now.minute)
        
        if (end_date.hour < coffe_open_hour):
            now  = datetime.now()-timedelta(days=1)
            start_date = datetime(year=now.year, 
                              month=now.month, 
                              day=now.day, 
                              hour=coffe_open_hour)
        else:
            start_date = datetime(year=end_date.year, 
                                  month=end_date.month, 
                                  day=end_date.day, 
                                  hour=coffe_open_hour)
        #log = LogParser()
        stat = log.GetStatAfterDate( start_date )
        stattext = ['Ноутбук %s: Использовался %s. Окончание: %s. %s' % (ReprName(stat_line['name'], False),
                                                          ReprSeconds(stat_line['time_used']),
                                                          str(datetime.fromtimestamp(stat_line['session_end']).time()),
                                                          ReprMoney(stat_line['money'])) 
        for stat_line in stat]
        
        gtk.Window.__init__(self, type=gtk.WINDOW_POPUP)
        self.connect("delete_event", self.delete_event)
        
#        gtk.Dialog.__init__(self, 
#                            parent = parent,
#                            title = 'Статистика с %s по %s'%(start_date, end_date),
#                            buttons=(gtk.STOCK_CLOSE,0))
        #self.vbox = gtk.VBox()
        
        one_line_heigth = 40
        
        rows = (gtk.gdk.screen_height()/2 / one_line_heigth) #@UndefinedVariable
        cols = 1
        self.table = gtk.Table(rows, cols, True)
        self.add(self.table)
         
        self.set_size_request(-1, gtk.gdk.screen_height()/2) #@UndefinedVariable 
        self.set_modal(True)
        self.set_keep_above(True)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_border_width(10)
        self.set_has_frame(True)
        
        ttl = 'Статистика с %s по %s'%(start_date, end_date)
        self.ttl_label = gtk.Label(ReprBigStr(ttl, use_markup=True))
        self.ttl_label.set_use_markup(True)
        self.ttl_label.set_size_request(-1, one_line_heigth)
        self.ttl_label.show()
        self.table.attach(self.ttl_label, 0, 1, 0, 1)
        #self.vbox.pack_start(self.ttl_label)
        
        self.scr_wnd = gtk.ScrolledWindow()
        self.text = gtk.TextView()
        self.scr_wnd.add(self.text)
        self.text.set_editable(False)
        self.text.set_cursor_visible(False)
        self.textbuf = self.text.get_buffer()
        self.textbuf.set_text('\n'.join(stattext))
        self.text.show()
        self.table.attach(self.scr_wnd, 0, 1, 1, rows-2)
        #self.vbox.pack_start(self.scr_wnd)
        
        self.close_btn = gtk.Button("Закрыть")
        self.close_btn.connect_object("clicked", gtk.Widget.destroy, self)
        self.close_btn.set_size_request(-1, one_line_heigth*2)
        self.close_btn.show()
        self.table.attach(self.close_btn, 0, 1, rows-2, rows)
        #self.vbox.pack_start(self.close_btn)
        
        self.show_all()
        
    def delete_event(self, widget, event, data=None):
        return False

class StatWidget(gtk.Button):
    def __init__(self, log, ui):
        gtk.Button.__init__(self)
        self.ui = ui
        
        self.stat_label = gtk.Label()
        self.stat_label.set_justify(gtk.JUSTIFY_CENTER)
        self.stat_label.set_use_markup(True)
        
        self.add(self.stat_label)
        #self.stat_label.show()
        
        self.connect("clicked", self.ShowStatClick, self)
        
        self.log  = log
        
        self.set_stat_id = gobject.timeout_add(logInterval*msec_in_sec, self.SetStat)
        
        self.show_all()
        self.SetStat()
        
    def ShowStatClick(self, widget, event):
        wnd = StatForm(self.log, self.ui.win)
        wnd.show()
    
    def SetStat(self):
        try:
            stat = self.log.GetLastNStat(stat_lines)
            logger.debug("Stat: %s" % (str(stat),))
            if (not stat):
                self.stat_label.set_markup('Статистика пуста')
                return True
            txt = [] 
            for ses in stat:
                txt.append('Ноутбук %s. %s' % (ReprName(ses['name'], use_markup=False) , ReprMoney(ses['money'])))
            self.stat_label.set_markup('\n'.join(txt))
        except Exception, e:
            logger.error("Can't set stat: %s" % (e.message,))
        return True
        

class UI(object):
    class __impl:
        def __init__(self, nc):
            self.nc = nc
            
            self.win = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.win.set_keep_above(True)
            self.win.connect("delete_event", delete_event)
            self.win.connect("destroy", destroy)
            self.btn_box = gtk.VBox()
            
            gtk.Window.fullscreen(self.win)
            self.win.add(self.btn_box)
            self.btn_box.show()
            self.grid_widgets = []
            try:
                self.ConstructWidgets()
            except Exception, e:
                logger.error('ConstructWidgets (UI.__init___). %s' % (e.message,))
            
            self.logWatch_id = gobject.timeout_add(logInterval*msec_in_sec, self.LogWatcher)
            self.win.show()
            
            self.win.realize()
            try:
                self.Update()
            except Exception, e:
                logger.error('Update UI (UI.__init___). %s' % (e.message,))
            try:
                self.lock = Locker(unlockPass)
            except Exception, e:
                logger.error('Create Locker (UI.__init___). %s' % (e.message,))
            #self.lockScr() 
            #self.lockWatch_id = gobject.timeout_add(msec_in_sec, self.LockWatcher)
            
            
        def main(self):
            gtk.main()
            
        def LogWatcher(self):
            #self.nc.Update()
            try:
                PingIP('10.2.44.1')
            except Exception, e:
                logger.error('Error in ping (LogWatch). %s' % (e.message,))
            try:
                self.Update()
            except Exception, e:
                logger.error('Error in update UI (LogWatch). %s' % (e.message,))
            return True
        
        def lockScr(self):
            # lock keyboard
            #self.lock.Lock()
            self.lockState = Locker.stateLocked
            
            self.grid_widgets[-1].destroy()
            self.grid_widgets[-1] = gtk.Frame(label=None)
            y,x = divmod(self.cnt-1, self.cols)
            self.table.attach(self.grid_widgets[-1], x, x+1, y, y+1)
            self.grid_widgets[-1].show()
            
        
        def LockWatcher(self):
            ''' Watch for Locker object status '''
            if (self.lockState == Locker.stateUnlocked):
                return True
            st = self.lock.Status()
            if (st == Locker.stateUnlocked):
                # Unlocked
                self.lockState = Locker.stateUnlocked
                
                self.grid_widgets[-1].destroy()
                self.grid_widgets[-1] = LockBtn()
                y,x = divmod(self.cnt-1, self.cols)
                self.table.attach(self.grid_widgets[-1], x, x+1, y, y+1)
                self.grid_widgets[-1].show()
            return True
            
        def Update(self):
            try:
                self.nc.Update()
            except Exception, e:
                logger.error('nc not updated')
            if set(self.nc.noteNames) != set(self.names):
                self.ConstructWidgets()
    
    #        update_pool = []
            for i, wdg in enumerate(self.grid_widgets):
                try:
                    note = wdg.note
                except AttributeError:
                    # ''' This widget is not note '''
                    continue
                
                needType = GetWidgetType(note)
                try:
                    if (type(wdg) is not needType):
                        self.grid_widgets[i].destroy()
                        self.grid_widgets[i] = needType(self, note)
                        y,x = divmod(i, self.cols)
                        self.table.attach(self.grid_widgets[i], x, x+1, y, y+1)
                        self.grid_widgets[i].show()
                        gobject.timeout_add(logInterval*msec_in_sec, self.grid_widgets[i].Update)
                        #update_pool.append(self.grid_widgets[i].Update) #, args=(self.grid_widgets[i],))
                        self.grid_widgets[i].Update()
                    #else:
                    #    update_pool.append(wdg.Update)#, args=(wdg,))
                        #wdg.Update()
                except Exception,e:
                    logger.error("Error while updating UI. %s" % (e.message,))
    #        for upd in update_pool:
    #            th = Thread(target=upd)
    #            th.start()
            #self.stat_widg.Update()
            try:
                with open(contacts_file) as f:
                    self.contacts.set_markup(f.read())
            except Exception, e:
                logger.error("Can't load contact file. %s" % (e.message,))
                    
        def AddContacts(self, container):
            self.contacts_text = None
            if not path.exists(contacts_file):
                logger.error('contacts file not found')
                return
            self.contacts = gtk.Label()
            #self.contacts.set_editable(False)
            #self.contacts.set_cursor_visible(False)
            #self.contacts.set_wrap_mode(gtk.WRAP_WORD)
            self.contacts.set_use_markup(True)
            #self.contacts.set_tabs(False)
            #self.contacts_text = self.contacts.get_buffer()
            
            container.add(self.contacts)
            self.contacts.show()
            
        def AddStat(self, container):
            self.stat_widg = StatWidget(self.nc.log, self)
            container.add(self.stat_widg)
            self.stat_widg.show()
        
        def ConstructWidgets(self):
            self.cnt = len(self.nc.notes)
            
            if (self.cnt <= 10):
                self.rows = 4
                self.cols = 3
            else:
                self.rows = GetSqrtCnt(self.cnt+2)
                self.cols = self.rows
    
            for wgt in self.grid_widgets: 
                wgt.destroy()
    
            try:
                self.table.resize(self.rows, self.cols)
            except:
                self.table = gtk.Table(self.rows, self.cols, True)
                self.table.set_col_spacings(5)
                self.table.set_row_spacings(5)
                self.btn_box.pack_start(self.table)
                self.table.show()
    
            #self.box.pack_start(self.table)
            #self.table.show()
    
            self.grid_widgets = []
            self.names = self.nc.noteNames[:]
            for name in self.nc.noteNames:
                widgType = GetWidgetType(self.nc.notes[name])
                self.grid_widgets.append(widgType(self, self.nc.notes[name]))
                gobject.timeout_add(logInterval*msec_in_sec, self.grid_widgets[-1].Update)
                self.grid_widgets[-1].Update()
            for i in xrange(len(self.nc.noteNames), self.rows*self.cols):
                self.grid_widgets.append(gtk.Frame(label=None))
                
            self.AddContacts(self.grid_widgets[-1])
            self.AddStat(self.grid_widgets[-2])
    
            for i, widg in enumerate(self.grid_widgets):
                y,x = divmod(i, self.cols)
                self.table.attach(widg, x, x+1, y, y+1)
                widg.show()
                
        
    # storage for the instance reference
    __instance = None

    def __init__(self, nc = None):
        """ Create singleton instance """
        # Check whether we already have an instance
        if UI.__instance is None:
            # Create and remember instance
            if (nc == None):
                raise Exception()
            UI.__instance = UI.__impl(nc)

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = UI.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)

    
def main():
    '''test cases'''
    NC = NoteControl("test.ini")
    window = UI(NC)
    print window.grid_widgets
    window.grid_widgets.index(window.grid_widgets[5])
    #window.main()

if __name__ == '__main__':
    main()
    
