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
import logModel
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
  progressSignal = QtCore.pyqtSignal(int)
  logSignal = QtCore.pyqtSignal(object)
  newDataSignal = QtCore.pyqtSignal(object)

  def __init__(self, name):
    super(WorkerThread, self).__init__()
    utils.verifyType(name, str)
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
class AdvancedWorkerThread(WorkerThread):
  def __init__(self, name, getAllItemsCb=None, applyToItemCb=None, formatLogItemCb=None):
    super(AdvancedWorkerThread, self).__init__(name)
    self._getAllItemsCb = getAllItemsCb
    self._applyToItemCb = applyToItemCb
    self._formatLogItemCb = formatLogItemCb

  def _getAllItems(self):
    if self._getAllItemsCb:
      return self._getAllItemsCb()
    else:
      raise NotImplementedError("WorkerThreadBase._getAllItems not implemented")

  def _applyToItem(self, item):
    if self._applyToItemCb:
      return self._applyToItemCb(item)
    else:
      raise NotImplementedError("WorkerThreadBase._applyToItem not implemented")
    
  def _formatLogItem(self, item, result):
    if self._formatLogItemCb:
      return self._formatLogItemCb(item, result)
    else:
      #fullLog = "{} {}".format(item, result)
      #shortLog = " ".join([ word if os.path.isabs(word) else os.path.basename(word) for word in fullLog.split()])
      return None#return logModel.LogItem(logModel.LogLevel.INFO, self._name, shortLog, fullLog) 
    
  def run(self):
    """ obfuscation for the win!! wow. this is madness. sorry """
    items = self._getAllItems()
    itemCount = 0
    numItems = len(items)
    results = collections.defaultdict(int)
    for i, inputItem in enumerate(items):
      item, result = self._applyToItem(inputItem)
      if item != None:
        self._onData(item)
        itemCount += 1
        log = self._formatLogItem(item, result)
        if log:
          self._onLog(log)
        results[result] += 1
      if self._userStopped:
        self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                     self._name,
                                     "User cancelled. {} of {} processed.".format(i + 1, numItems)))              
        break
      self._onProgress(int(100.0 * (i + 1) / numItems))
    
    results["Total"] = sum(v for _, v in results.items())
    summaryText = " ".join([("{}:{}".format(key, results[key])) 
                            for key in sorted(results, key=lambda k: results[k] + 1 if k == "Total" else 0)])
    self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                 self._name, 
                                 "Action complete. {} processed in {}. Summary: {}".format(itemCount, 
                                                                                           prettyTime(self.startTime),
                                                                                           summaryText)))    
