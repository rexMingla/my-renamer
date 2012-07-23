#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Thread abstraction
# --------------------------------------------------------------------------------------------------------------------
import time

from PyQt4 import QtCore

import utils

def prettyTime(startTime):
  secs = time.clock() - startTime
  utils.verify(secs >= 0, "Can't be negative")
  if secs < 60:
    return "{:.1f} secs".format(secs)
  mins = secs / 60
  if mins < 60:
    return "{:.1f} mins".format(mins)
  hours = seconds / (60 * 60)
  return "{:.1f} hours".format(hours)

# --------------------------------------------------------------------------------------------------------------------
class WorkerThread(QtCore.QThread):
  progressSignal = QtCore.pyqtSignal(int)
  logSignal = QtCore.pyqtSignal(object)
  newDataSignal = QtCore.pyqtSignal(object)

  def __init__(self):
    super(WorkerThread, self).__init__()
    self.userStopped = False
    self.startTime = time.clock()
  
  def __del__(self):
    self.join()
    
  def join(self):
    self.userStopped = True
    
  def _onLog(self, msg):
    self.logSignal.emit(msg)
  
  def _onProgress(self, percentage):
    self.progressSignal.emit(percentage)
    
  def _onData(self, data):
    self.newDataSignal.emit(data)