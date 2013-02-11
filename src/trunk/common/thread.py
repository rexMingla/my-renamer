#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Thread abstraction
# --------------------------------------------------------------------------------------------------------------------
import time

from PyQt4 import QtCore

from common import utils

import collections

# --------------------------------------------------------------------------------------------------------------------
def prettyTime(start_time):
  secs = time.clock() - start_time
  utils.verify(secs >= 0, "Can't be negative")
  if secs < 60:
    return "{:.1f} secs".format(secs)
  mins = secs / 60
  if mins < 60:
    return "{:.1f} mins".format(mins)
  hours = secs / (60 * 60)
  return "{:.1f} hours".format(hours)

# --------------------------------------------------------------------------------------------------------------------
class WorkerThread(QtCore.QThread):
  """ base thread intended for use on a list of tasks where it can periodically signal progress, log and new data """
  progress_signal = QtCore.pyqtSignal(int)
  log_signal = QtCore.pyqtSignal(object)
  new_data_signal = QtCore.pyqtSignal(object)

  def __init__(self, name):
    super(WorkerThread, self).__init__()
    #utils.verifyType(name, str)
    self._name = name
    self._user_stopped = False
    self.start_time = None

  def run(self):
    self._user_stopped = False
    self.start_time = time.clock()
    self._run()
    
  def _run(self):
    raise NotImplementedError("WorkerThread._run not implemented")
    
  def __del__(self):
    self.join()

  def join(self):
    self._user_stopped = True

  def _onLog(self, msg):
    self.log_signal.emit(msg)

  def _onProgress(self, percentage):
    self.progress_signal.emit(percentage)

  def _onData(self, data):
    self.new_data_signal.emit(data)

# --------------------------------------------------------------------------------------------------------------------
class WorkItem(object):
  """ result and object. assumed result is human readible """
  def __init__(self, obj, result):
    super(WorkItem, self).__init__()
    self.obj = obj
    self.result = result

# --------------------------------------------------------------------------------------------------------------------
class AdvancedWorkerThread(WorkerThread):
  """ 'simplified' version of WorkerThread were all summary messages are handled consistently """
  def __init__(self, name):
    super(AdvancedWorkerThread, self).__init__(name)
    self._i = 0
    self._num_items = 0

  def _getAllItems(self):
    raise NotImplementedError("AdvancedWorkerThread._getAllItems not implemented")

  def _applyToItem(self, item):
    raise NotImplementedError("AdvancedWorkerThread._applyToItem not implemented")

  def _run(self):
    """ obfuscation for the win!! wow. this is madness. sorry """
    items = self._getAllItems()
    item_count = 0
    self._num_items = len(items)
    results = collections.Counter()
    for self._i, input_item in enumerate(items):
      item = self._applyToItem(input_item)
      if item:
        if item.obj != None:
          self._onData(item.obj)
          item_count += 1
        results[item.result] += 1
      if self._user_stopped:
        """self._onLog(utils.LogItem(utils.LogLevel.INFO,
                                     self._name,
                                     "User cancelled. {} of {} processed.".format(self._i + 1, self._num_items)))"""
        break
      self._onProgress(int(100.0 * (self._i + 1) / self._num_items))

    results["Total"] = sum(v for _, v in results.items())
    summary_text = " ".join([("{}:{}".format(key, results[key]))
                            for key in sorted(results, key=lambda k: results[k] + 1 if k == "Total" else 0)])
    """self._onLog(utils.LogItem(utils.LogLevel.INFO,
                                 self._name,
                                 "Action complete. {} processed in {}. Summary: {}".format(item_count,
                                                                                           prettyTime(self.start_time),
                                                                                           summary_text)))"""
