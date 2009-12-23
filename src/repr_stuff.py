#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common_config import *

def ReprBigStr(s, use_markup=True):
    if (use_markup):
        return '<span foreground="black" size="x-large">%s</span>' % (s,)
    return s

def ReprName(name, use_markup=True):
    return ReprBigStr(name, use_markup) 
    #return 'Ноутбук '+ name

def ReprSeconds(sec, big = False):
    ''' in HH:MM '''
    h, sec = divmod(sec, sec_in_hour)
    m, sec = divmod(sec, sec_in_min)
    
    s = '%02d:%02d' % (h,m)
    if (big):
        s = ReprBigStr(s, use_markup=True)
    return s
#    ''' in "1 час", "2 часа"... "5 часов"...'''
#    h, sec = divmod(sec, 3600)
#    if (sec != 0 or h==0):
#        h += 1
#    
#    if (h < 2):
#        hours = 'час'
#    elif (h < 5):
#        hours = 'часа'
#    else:
#        hours = 'часов'
#    
#    return '%d %s' % (h,hours)

def ReprSecondsWithTimer(note, big=True):
    if(note.has_timer):
        res = ReprBigStr("%s из %s" % (ReprSeconds(note.time), ReprSeconds(note.timer_val)), big)
    else:
        res = ReprBigStr("%s" % (ReprSeconds(note.time), ), big)
    return res

def ReprBatt(charge):
    return "Заряд: %d" % (charge,)

def ReprMoney(money):
    m = int(money)
    return "Сумма: %d руб." % (m,) 

