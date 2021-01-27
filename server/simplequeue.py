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


import threading


class SimpleQueue:
  def __init__(self,size):
    self.condition=threading.Condition()
    self.data=[]
    self.size=size
    self.sequence=0

  def getStartSequence(self):
    self.condition.acquire()
    try:
      if len(self.data) > 0:
        return self.data[0][0] -1
      return self.sequence -1
    finally:
      self.condition.release()

  def clear(self):
    self.condition.acquire()
    self.data=[]
    self.sequence+=1
    self.condition.notifyAll()
    self.condition.release()
  def add(self,item):
    self.condition.acquire()
    try:
      self.sequence+=1
      self.data.append((self.sequence,item))
      self.condition.notifyAll()
      if len(self.data) > self.size:
        self.data.pop(0)
    finally:
      self.condition.release()

  def read(self,lastSeq,timeout=1):
    rt=None
    loopCount=timeout*10
    while loopCount > 0:
      try:
        self.condition.acquire()
        for idx in range(len(self.data)-1,-1,-1):
          le=self.data[idx]
          if le[0] <= lastSeq:
            break
          rt=le
        if rt is not None:
          return rt
        self.condition.wait(0.1)
        loopCount=loopCount-1
      finally:
        self.condition.release()
    return lastSeq,None
