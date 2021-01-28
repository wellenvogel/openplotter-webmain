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
import importlib
import logging
import os

import yaml


class AppPath:
  def __init__(self,name,base,handler,isMain=False,startUrl='index.html',isSetting=False,icon=None,displayName=None):
    self.path='/apps/'+name+'/' if not isMain else '/'+name+'/'
    self.base=base
    self.handler=handler
    self.isMain=isMain
    self.startUrl=startUrl
    self.isSetting=isSetting
    self.icon=icon
    self.displayName=displayName


class AppHandler(object):

  def __init__(self,basedir=None):
    self.baseDir = basedir if basedir is not None else os.path.join(os.path.dirname(__file__),'..','..','apps')

  def scanApps(self):
    rt=[]
    if not os.path.isdir(self.baseDir):
      logging.debug("AppHandler: baseDir %s not found",self.baseDir)
      return rt
    for dir in os.listdir(self.baseDir):
      if dir == '.' or dir == '..':
        continue
      fname=os.path.join(self.baseDir,dir)
      if not os.path.isdir(fname):
        continue
      configFile=os.path.join(fname,'app.yaml')
      if not os.path.isfile(configFile):
        logging.info("AppHandler: not app.yaml for %s",fname)
        continue
      config={}
      with open(configFile,'r') as f:
        config=yaml.safe_load(f)
      appEntry=AppPath(dir,fname,None)
      handler=config.get('handler')
      if handler is not None:
        try:
          handlerModule=importlib.import_module(handler)
        except Exception as e:
          logging.error("AppHandler: %s unable to import module %s: %s",dir,handler,str(e))
          continue
        appEntry.handler=handlerModule
      baseDir=config.get('baseDir')
      if baseDir is None:
        baseDir=fname
      else:
        if not os.path.exists(baseDir):
          logging.error("AppHandler: %s baseDir %s not found", dir,baseDir)
          continue
      appEntry.base=baseDir
      icon=config.get('icon')
      if icon is None:
        logging.error("AppHandler: %s no icon defined", dir)
        continue
      iconFile=os.path.join(appEntry.base,icon)
      if not os.path.exists(iconFile):
        logging.error("AppHandler: %s icon %s not found", dir,iconFile)
        continue
      appEntry.icon=icon
      mainPage=config.get('mainPage')
      if mainPage is not None:
        appEntry.startUrl=mainPage
      if not mainPage.startswith('http'):
        mainFile=os.path.join(appEntry.base,appEntry.startUrl)
        if not os.path.exists(mainFile):
          logging.error("AppHandler: %s startUrl %s not found", dir, mainFile)
          continue
      type=config.get('type')
      ALLOWED_TYPES=['main','settings']
      if not type in ALLOWED_TYPES:
        logging.error("AppHandler: %s type %s is not in %s",dir,type,",".join(ALLOWED_TYPES))
        continue
      if type == 'settings':
        appEntry.isSetting=True
      rt.append(appEntry)
    return rt