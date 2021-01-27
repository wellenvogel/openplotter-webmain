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
import subprocess
import threading
import time
import traceback


class Commands:
  def __init__(self,console):
    self.runningCommand=None
    self.lastReturn=None
    self.commandList=[]
    self.currentIndex=0
    self.busy=False
    self.lock=threading.Lock()
    self.stdoutLogger=None
    self.stderrLogger=None
    self.finishCallback=None
    self.continueOnError=True
    self.console=console

  def runCommands(self,commands,stdoutcallback=None,stderrcallback=None,startcallback=None,finishCallback=None,continueOnError=True):
    '''
    start execution of an action
    it will not start an if currently busy and return False
    :param commands: the list of commands
    :param startcallback: if set, this will get called back before the action is really started
    :param stdoutcallback: a callback that is called with every line of stdout
                           if not provided data is written to the console
    :param stderrcallback: a callback for every line of stderr
                           if not provided data is written to stdout
    :param finishCallback: called back when the last command finished
    :param continueOnError: if True (default) continue on error
    :return: True if successfully started, False if another command is running
    '''
    busy=False
    self.lock.acquire()
    try:
      busy=self.busy
      if not busy:
        self.busy=True
    finally:
      self.lock.release()
    if busy:
      logging.info("unable to start %s as another action is running")
      return False
    rt=False
    try:
      self.commandList=commands
      self.currentIndex=0
      self.stdoutLogger=stdoutcallback
      if self.stdoutLogger is None:
        self.stdoutLogger=self._logConsole
      self.stderrLogger=stderrcallback if stderrcallback is not None else self.stdoutLogger
      self.finishCallback=finishCallback
      self.continueOnError=continueOnError
      if startcallback is not None:
        startcallback()
      rt=self._runCommand()
    except Exception as e:
      self.busy=False
      raise
    if rt:
      checker = threading.Thread(target=self._autoCheck)
      checker.setDaemon(True)
      checker.start()
      return True
    return False

  def _logConsole(self,line):
    if self.console is not None:
      self.console.add(line)

  def _runCommand(self):
    if self.currentIndex >= len(self.commandList) or self.currentIndex < 0:
      raise Exception("internal error, command index out of range")
    command = self.commandList[self.currentIndex]
    try:
      self.stdoutLogger("starting %s"%" ".join(command))
      stderr=subprocess.PIPE if self.stderrLogger != self.stdoutLogger else subprocess.STDOUT
      self.runningCommand=subprocess.Popen(command,close_fds=True,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=stderr)
    except Exception as e:
      self.stderrLogger("Exception when starting %s:%s"%(" ".join(command),str(e)))
      return False
    stdoutReader=threading.Thread(target=self._readStdout)
    stdoutReader.setDaemon(True)
    stdoutReader.start()
    if self.stdoutLogger != self.stderrLogger:
      stderrReader=threading.Thread(target=self._readStderr)
      stderrReader.setDaemon(True)
      stderrReader.start()
    return True

  def _autoCheck(self,updateSequence=False):
    while self.busy:
      try:
        rt=self._checkRunning()
        if rt is not None:
          break
        time.sleep(0.2)
      except Exception as e:
        logging.error("error in command handler: %s",traceback.format_exc())
        time.sleep(0.2)
    self.busy=False

  def _readStdout(self):
    while True:
      line=self.runningCommand.stdout.readline()
      if len(line) == 0:
        break
      self.stdoutLogger(line.rstrip())

  def _readStderr(self):
    while True:
      line = self.runningCommand.stderr.readline()
      if len(line) == 0:
        break
      self.stderrLogger(line.rstrip())

  def hasRunningCommand(self):
    return self.busy

  def _checkNextCommand(self):
    if self.currentIndex >= (len(self.commandList) -1):
      return False
    self.currentIndex+=1
    return self._runCommand()

  def _checkRunning(self):
    '''
    check if the current command is still running
    and potentially start a new one
    :return: None if the command is still running, return code otherwise
    '''
    if not self.runningCommand:
      return
    rt=self.runningCommand.poll()
    if rt is None:
      return
    self.stdoutLogger("command finished with return code %d" % rt)
    self.stdoutLogger("")
    if rt == 0 or rt != 0:
      next=self._checkNextCommand()
      if next:
        return None
    self.lastReturn = rt
    self.runningCommand = None
    self.busy=False
    if self.finishCallback is not None:
      self.finishCallback(rt)
    return rt

