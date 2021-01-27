# -*- coding: utf-8 -*-
# vim: ts=2 sw=2 et ai
###############################################################################
# Copyright (c) 2021 Andreas Vogel andreas@wellenvogel.net
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
#
###############################################################################
import logging

import pydbus

class UnitInfo:
  def __init__(self,name,status,commandline):
    self.name=name
    self.status=status
    self.commandline=commandline

class Systemd:
  def __init__(self):
    self.bus = pydbus.SystemBus()

  def _getObject(self,path):
    return self.bus.get(
        'org.freedesktop.systemd1',
        path
    )


  def getUnitInfo(self,units):
    '''
    get the name and running state for units
    :param units: a list of unit names
    :return: a list of tuples (name,running)
    '''
    rt = []
    systemd= self._getObject('/org/freedesktop/systemd1')
    if systemd is None:
      return rt
    manager=systemd['org.freedesktop.systemd1.Manager']

    if units is None or not isinstance(units,list):
      return rt
    try:
      for unit in manager.ListUnits():
        name=unit[0]
        state=unit[4]
        if name in units:
          cmd=None
          try:
            extended = self._getObject(unit[6])
            cmd=extended.ExecStart
            logging.debug("extended info for %s: %s,cmd=%s",name,str(extended),str(cmd[0][1]))
          except:
            pass
          rt.append(UnitInfo(name,state,cmd[0][1] if cmd is not None else []))
    except Exception as e:
      logging.error("Systemd: unable to list units: %s",str(e))
      raise
    return rt