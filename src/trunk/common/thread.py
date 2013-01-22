#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Thread abstraction
# --------------------------------------------------------------------------------------------------------------------
import time

from PyQt4 import QtCore

import collections
import utils

# --------------------------------------------------------------------------------------------------------------------
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
  """ base thread intended for use on a list of tasks where it can periodically signal progress, log and new data """ 
  progressSignal = QtCore.pyqtSignal(int)
  logSignal = QtCore.pyqtSignal(object)
  newDataSignal = QtCore.pyqtSignal(object)

  def __init__(self, name):
    super(WorkerThread, self).__init__()
    #utils.verifyType(name, str)
    self._name = name
    self._userStopped = False
    self.startTime = time.clock()
  
  def __del__(self):
    self.join()
    
  def join(self):
    self._userStopped = True
    
  def _onLog(self, msg):
    self.logSignal.emit(msg)
  
  def _onProgress(self, percentage):
    self.progressSignal.emit(percentage)
    
  def _onData(self, data):
    self.newDataSignal.emit(data)

# --------------------------------------------------------------------------------------------------------------------
class WorkItem(object):
  """ result and object. assumed result is human readible """
  def __init__(self, obj, result, log=None):
    super(WorkItem, self).__init__()
    self.obj = obj
    self.result = result
    self.log = log
    
# --------------------------------------------------------------------------------------------------------------------
class AdvancedWorkerThread(WorkerThread):
  """ 'simplified' version of WorkerThread were all summary messages are handled consistently """ 
  def __init__(self, name):
    super(AdvancedWorkerThread, self).__init__(name)

  def _getAllItems(self):
    raise NotImplementedError("WorkerThreadBase._getAllItems not implemented")

  def _applyToItem(self, item):
    raise NotImplementedError("WorkerThreadBase._applyToItem not implemented")
    
  def run(self):
    """ obfuscation for the win!! wow. this is madness. sorry """
    items = self._getAllItems()
    itemCount = 0
    self._numItems = len(items)
    results = collections.Counter()
    for self._i, inputItem in enumerate(items):
      item = self._applyToItem(inputItem)
      if item:
        if item.obj != None:
          self._onData(item.obj)
          itemCount += 1
        if item.log:
          self._onLog(item.log)
        results[item.result] += 1
      if self._userStopped:
        self._onLog(utils.LogItem(utils.LogLevel.INFO, 
                                     self._name,
                                     "User cancelled. {} of {} processed.".format(self._i + 1, self._numItems)))              
        break
      self._onProgress(int(100.0 * (self._i + 1) / self._numItems))
    
    results["Total"] = sum(v for _, v in results.items())
    summaryText = " ".join([("{}:{}".format(key, results[key])) 
                            for key in sorted(results, key=lambda k: results[k] + 1 if k == "Total" else 0)])
    self._onLog(utils.LogItem(utils.LogLevel.INFO, 
                                 self._name, 
                                 "Action complete. {} processed in {}. Summary: {}".format(itemCount, 
                                                                                           prettyTime(self.startTime),
                                                                                           summaryText)))    
