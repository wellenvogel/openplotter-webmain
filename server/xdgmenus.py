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
import re

import xdg.Menu
import xdg.IconTheme

class XdgUrl:
  def __init__(self,displayName,iconFile,url):
    self.displayName=displayName
    self.icon =iconFile
    self.url=url

  def toDict(self):
    return self.__dict__

class XdgMenus(object):
  def __init__(self,baseMenu='lxde-pi-applications.menu'):
    self.baseMenu=baseMenu

  def _appendIfMatching(self,list,entry,category):
    if isinstance(entry, xdg.Menu.MenuEntry):
      desktopEntry = entry.DesktopEntry
      if desktopEntry is not None:
        if category in desktopEntry.getCategories():
          list.append(desktopEntry)

  def _getEntriesFromMenu(self,menu,category):
    rt=[]
    for entry in list(menu.getEntries()):
      if isinstance(entry,xdg.Menu.Menu):
        rt.extend(self._getEntriesFromMenu(entry,category))
        continue
      self._appendIfMatching(rt,entry,category)
    return rt

  def getEntries(self,category):
    '''
    get a list of xdg.Menu.DesktopEntry matching the category
    :param category:
    :return:
    '''
    rt=[]
    base=xdg.Menu.parse(self.baseMenu)
    if base is None:
      logging.debug("no entries for base menu %s",self.baseMenu)
      return rt
    for m in list(base.getEntries()):
      if isinstance(m,xdg.Menu.Menu):
        rt.extend(self._getEntriesFromMenu(m,category))
      else:
        self._appendIfMatching(rt,m,category)
    return rt


  def getEntriesWithUrls(self,category):
    entries=self.getEntries(category)
    rt=[]
    for entry in entries:
      exec=entry.getExec()
      if exec is not None and exec.startswith('x-www-browser'):
        url=re.sub('.* http','http',exec)
        icon=entry.getIcon()
        displayName=entry.getName()
        rt.append(XdgUrl(displayName,icon,url))
    return rt

  def getIconPath(self,iconName):

    return xdg.IconTheme.getIconPath(iconName)