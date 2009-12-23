#!/usr/bin/python
#-*- coding: utf-8 -*-
'''
Created on 09.12.2009

@author: andrey
'''
from datetime import datetime
import time
import gobject

import gtk
from repr_stuff import ReprBigStr, ReprSeconds
from common_config import *

class ButtonsArrange(object):
    Vertical = 0
    Horizontal = 1
    
class NoSuchArrangeError(Exception): pass

class BtnRef(object):
    def __init__(self, wgt, name, proc, arg):
        self.widget = wgt
        self.name = name
        self.proc = proc
        self.arg = arg

class BtnStack(gtk.Window):
    def __init__(self, btns, title=None, btn_arr=ButtonsArrange.Horizontal):
        '''btns - tuple of (name1, {'proc':connected_procedure1, 'arg':arg1}, name2, {'proc':connected_procedure2, 'arg':arg2}...)'''
        gtk.Window.__init__(self, type=gtk.WINDOW_POPUP)
        #self.set_border_width(10)
        #self.set_has_frame(True)
        self.connect("delete_event", self.delete_event)
        
        #self.frame = gtk.Frame()
        self.btn_arr = btn_arr
        if self.btn_arr == ButtonsArrange.Vertical:
            self.btn_box = gtk.VBox(homogeneous=True, spacing=0)
        elif self.btn_arr == ButtonsArrange.Horizontal:
            self.btn_box = gtk.HBox(homogeneous=True, spacing=0)
        else:
            raise NoSuchArrangeError()
        
        self.btns = {}
        
        for i in range(0, len(btns), 2 ):
            self.btns[btns[i]] = BtnRef(gtk.Button(btns[i]), btns[i], btns[i+1]['proc'], btns[i+1]['arg'])
            self.btns[btns[i]].widget.connect("clicked", self.AnyBtnClick, self)
            self.btns[btns[i]].widget.connect_object("clicked", gtk.Widget.destroy, self)
            self.btn_box.pack_start(self.btns[btns[i]].widget)
        
        if(title):
            self.ttl_text = title
            self.ttl = gtk.Label(ReprBigStr(title))
            self.ttl.set_use_markup(True)
            self.titled_box = gtk.VBox(homogeneous=False, spacing=0)
            self.titled_box.pack_start(self.ttl)
            self.titled_box.pack_start(self.btn_box)
            self.titled_box.show_all()
            self.add(self.titled_box)
        self.btn_box.show_all()
        
        # Center it!
        self.set_position( gtk.WIN_POS_CENTER )
        self.set_modal(True)
        self.set_keep_above(True)
        
        self.show_all()
        
    def AnyBtnClick(self, widget, event):
        proc = self.btns[widget.get_label()].proc
        arg =  self.btns[widget.get_label()].arg
        if (arg != None):
            proc(arg)
        else:
            proc()
        
    
    def delete_event(self, widget, event, data=None):
        return False
    
class BtnStackTimer(BtnStack):
    def __init__(self, btns, timer_end_func, timer, title=None, btn_arr=ButtonsArrange.Horizontal):
        BtnStack.__init__(self, btns, title, btn_arr)
        
        self.timer_end_func = timer_end_func
        self.start_time = int(time.time())
        self.end_time = self.start_time + timer + sec_in_min -1
        self.timer_end_id = gobject.timeout_add(timer*msec_in_sec, self.TimeEnd)
        self.update_id = gobject.timeout_add(msec_in_sec, self.Update)
        self.Update()
        
    def Update(self):
        self.ttl.set_markup(self.GetTitle())
        return True
    
    def GetTitle(self):
        time_el = self.end_time - int(time.time())
        repr_time = ReprSeconds(time_el, big=False)
        if (self.ttl_text):
            res = self.ttl_text + " (%s мин.)" % (repr_time, )
            res = ReprBigStr(res)
        else:
            res = "Осталось %s мин." % (repr_time,)
            
        return ReprBigStr(res, use_markup=True) 
    
    def TimeEnd(self):
        if (self.timer_end_func['arg'] != None):
            self.timer_end_func['proc'](self.timer_end_func['arg'])
        else:
            self.timer_end_func['proc']()
        self.destroy()
        return False


    def AnyBtnClick(self, widget, event):
        gobject.source_remove(self.timer_end_id)
        gobject.source_remove(self.update_id)
        BtnStack.AnyBtnClick(self, widget, event)
    
class POCClass(object):
    def __init__(self, name):
        self.name = name
        
    def POC(self):
        print self.name
        
class MainWnd:
    def POC(self, widget, event):
        p1 = POCClass('bnt1')
        p2 = POCClass('bnt2')
        btns_ref =('btn1', {'proc':p1.POC, 'arg':None}, 'btn2', {'proc':p2.POC, 'arg':None}, 'timer_end', {'proc': None, 'arg': None})
        self.stack = BtnStackTimer(btns_ref, timer=2*sec_in_min, title='POC', btn_arr=ButtonsArrange.Horizontal)
        self.stack.show()
        
        
    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        return False

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        gtk.main_quit()

    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_border_width(10)
    
        # Creates a new button with the label "Hello World".
        self.button = gtk.Button("POC")
    
        # When the button receives the "clicked" signal, it will call the
        # function hello() passing it None as its argument.  The hello()
        # function is defined above.
        self.button.connect("clicked", self.POC, None)
    
        # This will cause the window to be destroyed by calling
        # gtk_widget_destroy(window) when "clicked".  Again, the destroy
        # signal could come from here, or the window manager.
        #self.button.connect_object("clicked", gtk.Widget.destroy, self.window)
    
        # This packs the button into the window (a GTK container).
        self.window.add(self.button)
    
        # The final step is to display this newly created widget.
        self.button.show()
    
        # and the window
        self.window.show()

    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

# If the program is run directly or passed as an argument to the python
# interpreter then create a MainWnd instance and show it
if __name__ == "__main__":
    hello = MainWnd()
    hello.main()
