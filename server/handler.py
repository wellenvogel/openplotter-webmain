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
import http.server
import json
import logging
import os
import posixpath
import re
import shutil
import urllib.parse
from http import HTTPStatus


class Handler(http.server.SimpleHTTPRequestHandler):
  protocol_version = "HTTP/1.1" #necessary for websockets!

  @classmethod
  def getReturnData(cls, error=None, **kwargs):
    if error is not None:
      rt = {'status': error}
    else:
      rt = {'status': 'OK'}
    for k in list(kwargs.keys()):
      if kwargs[k] is not None:
        rt[k] = kwargs[k]
    return rt

  @classmethod
  def pathQueryFromUrl(cls, url):
    (path, sep, query) = url.partition('?')
    path = path.split('#', 1)[0]
    path = posixpath.normpath(urllib.parse.unquote(path))
    return (path, query)

  @classmethod
  def getRequestParam(cls,query):
    return urllib.parse.parse_qs(query, True)

  def setBaseDir(self,baseDir):
    self.baseDir=baseDir

  def getBaseDir(self):
    '''
    get the base dir for translate_path
    you can overwrite the default per request
    with setBaseDir
    :return:
    '''
    if hasattr(self,'baseDir'):
      return self.baseDir
    return os.path.join(os.path.dirname(__file__),'..','gui')


  def log_message(self, format, *args):
    logging.debug(format, *args)


  def translate_path(self, path):
    """Translate a /-separated PATH to the local filename syntax.

            Components that mean special things to the local file system
            (e.g. drive or directory names) are ignored.  (XXX They should
            probably be diagnosed.)

            """
    # abandon query parameters
    path = path.split('?', 1)[0]
    path = path.split('#', 1)[0]
    # Don't forget explicit trailing slash when normalizing. Issue17324
    trailing_slash = path.rstrip().endswith('/')
    try:
      path = urllib.parse.unquote(path, errors='surrogatepass')
    except UnicodeDecodeError:
      path = urllib.parse.unquote(path)
    path = posixpath.normpath(path)
    words = path.split('/')
    words = filter(None, words)
    path = self.getBaseDir()
    for word in words:
      if os.path.dirname(word) or word in (os.curdir, os.pardir):
        # Ignore components that are not a simple file/directory name
        continue
      path = os.path.join(path, word)
    if trailing_slash:
      path += '/'
    return path

  def sendJsonResponse(self,data):
    r=json.dumps(data).encode('utf-8')
    self.send_response(200)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(r)))
    self.send_header("Last-Modified", self.date_time_string())
    self.end_headers()
    self.wfile.write(r)

  def sendFile(self, filename, attachment=None, maxBytes=None,mimeType='text/plain'):
    if filename is None or not os.path.exists(filename):
      self.send_response(404,'not found')
      self.end_headers()
      self.close_connection=True
      return
    try:
      if mimeType is None:
        mimeType=self.server.guess_type(filename)
      if mimeType is None:
        mimeType='application/octet-stream'
      with open(filename,'rb') as f:
        self.send_response(HTTPStatus.OK)
        if attachment is not None:
          self.send_header('Content-Disposition',
                           'attachment;filename="%s"'%attachment)
        self.send_header("Content-type", mimeType)
        fs = os.fstat(f.fileno())
        seekBytes=0
        flen=fs[6]
        if maxBytes is not None:
          seekBytes=flen-maxBytes
          if seekBytes < 0:
            seekBytes=0
          flen-=seekBytes
          if seekBytes > 0:
            f.seek(seekBytes)
        self.send_header("Content-Length", str(flen))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        shutil.copyfileobj(f,self.wfile)
        self.wfile.close()
        return
    except:
      pass
    self.send_response(404, 'not found')
    self.end_headers()
    self.close_connection = True

  def _getRequestIp(self, default="localhost"):
    hostip = default
    try:
      host = self.headers.get('host')
      hostparts = host.split(':') #TODO: ipv6...
      hostip = hostparts[0]
    except:
      pass
    return hostip

  def do_GET(self):
    if not self.path.startswith("/api"):
      return super().do_GET()
    (request,query)=self.pathQueryFromUrl(self.path)
    request=request[len("/api/"):]
    requestParam=self.getRequestParam(query)
    if request.endswith("/"):
      request=request[:-1]
    if request == 'icon':
      name=requestParam.get('name')
      if name is None or len(name) < 1:
        logging.debug("missing parameter name in icon request")
        self.send_response(404, 'not found')
        self.end_headers()
        self.close_connection = True
      name=re.sub('[^0-9 a-zA-Z._-]*','',name[0]) #some security - only allow simple words
      iconFile=self.server.getIconFilePath(name)
      if iconFile is None:
        logging.debug("icon file not found for %s",name)
      self.sendFile(iconFile)
      return
    if request == 'mainEntries':
      requestIp=self._getRequestIp()
      entries=self.server.getUrlsFromMenus()
      for entry in entries:
        entry.icon='/api/icon?name='+urllib.parse.quote(entry.icon)
        if entry.url is not None:
          entry.url=entry.url.replace('localhost',requestIp).replace('127.0.0.1',requestIp)
      self.sendJsonResponse(self.getReturnData(data=list(map(lambda x:x.toDict(),entries))))
      return

    self.sendJsonResponse(self.getReturnData("unknown request %s"%request))

