#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Base module responsible for the renaming of movies and tv series
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

from common import extension
from common import fileHelper
from common import logModel
from common import moveItemActioner
from common import utils

import inputWidget
import logWidget
import outputWidget
import workBenchWidget

class MyThread(QtCore.QThread):
  progressSignal = QtCore.pyqtSignal(int)
  logSignal = QtCore.pyqtSignal(object)
  newDataSignal = QtCore.pyqtSignal(object)

  def __init__(self):
    super(MyThread, self).__init__()
    self.userStopped = False
  
  def __del__(self):
    self.join()
    
  def join(self):
    self.userStopped = True
    
  def _onLog(self, msg):
    self.logSignal.emit(msg)
  
  def _onProgress(self, percentage):
    self.progressSignal.emit(percentage)
    
  def _onNewData(self, data):
    self.newDataSignal.emit(data)

"""class RenameThread(MyThread):  
  def __init__(self, actioner, items):
    super(RenameThread, self).__init__()
    utils.verifyType(actioner, moveItemActioner.MoveItemActioner)
    utils.verifyType(items, list)
    self._actioner = actioner
    self._items = items
    
  def run(self):
    results = {} #hist
    for i, item in enumerate(self._items):
      source, dest = item
      res = self._actioner.performAction(source, dest)
      self._onLog(moveItemActioner.MoveItemActioner.resultToLogItem(res, source, dest))
      if not results.has_key(res):
        results[res] = 0  
      results[res] += 1  
      self._onProgress(int(100 * (i + 1) / len(self._items)))
      if self.userStopped:
        self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                     "Rename / move",
                                     "User cancelled. %d of %d files actioned." % (i, len(self._items))))              
        break
    self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                 "Rename / move",
                                 moveItemActioner.MoveItemActioner.summaryText(results)))      
    
class ExploreThread(MyThread):
  def __init__(self, folder, isRecursive, ext):
    super(ExploreThread, self).__init__()
    utils.verifyType(folder, str)
    utils.verifyType(isRecursive, bool)
    utils.verifyType(ext, extension.FileExtensions)
    self._folder = folder
    self._isRecursive = isRecursive
    self._ext = ext
    
  def run(self):
    dirs = seasonHelper.SeasonHelper.getFolders(self._folder, self._isRecursive)
    for i, d in enumerate(dirs):
      s = seasonHelper.SeasonHelper.getSeasonForFolder(d, self._ext)
      if s:
        self._onNewData(s)
        if self.userStopped:
          self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                       "Search", 
                                       "User cancelled. %d of %d folders processed." % (i, len(dirs))))              
          break
      self._onProgress(int(100 * (i + 1) / len(dirs)))
    self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                 "Search", 
                                 "Search complete. %d folders processed." % (len(dirs))))"""

# --------------------------------------------------------------------------------------------------------------------
class Mode:
  MOVIE_MODE = "movie"
  TV_MODE = "tv"
  
VALID_MODES = (Mode.MOVIE_MODE, Mode.TV_MODE)

# --------------------------------------------------------------------------------------------------------------------
class RenamerModule(QtCore.QObject):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, mode, inputWidget_, outputWidget_, workBenchWidget_, logWidget_, parent=None):
    super(RenamerModule, self).__init__(parent)
    
    assert(mode in VALID_MODES)
    utils.verifyType(inputWidget_, inputWidget.InputWidget)
    utils.verifyType(outputWidget_, outputWidget.OutputWidget)
    utils.verifyType(workBenchWidget_, workBenchWidget.WorkBenchWidget)
    utils.verifyType(logWidget_, logWidget.LogWidget)

    self.mode = mode
    self._inputWidget = inputWidget_
    self._outputWidget = outputWidget_
    self._workBenchWidget = workBenchWidget_
    self._logWidget = logWidget_
    
    self._workerThread = None
    self._isShuttingDown = False
    self._config = {}
    self._isActive = False
    
  def __del__(self):
    self._isShuttingDown = True
    self._stopThread()
    
  def setActive(self):
    conf = self.getConfig()
    
    self._isActive = True
    self._outputWidget.renameSignal.connect(self._rename)
    self._inputWidget.exploreSignal.connect(self._explore)
    self._inputWidget.stopSignal.connect(self._stopSearch)
    self._workBenchWidget.workBenchChangedSignal.connect(self._outputWidget.enableControls)    
    self.setConfig(conf)
    self._setActive()
    
  def _setActive(self):
    raise NotImplementedError("RenamerModule._setActive not implemented")
    
  def setInactive(self):
    self.setConfig(self.getConfig()) #slightly hacky. we need to get the data out first before we are in active state
    
    self._isActive = False
    self._outputWidget.renameSignal.disconnect(self._rename)
    self._inputWidget.exploreSignal.disconnect(self._explore)
    self._inputWidget.stopSignal.disconnect(self._stopSearch)
    self._workBenchWidget.workBenchChangedSignal.disconnect(self._outputWidget.enableControls)
    
    self._setInactive()

  def _setInactive(self):
    raise NotImplementedError("RenamerModule._setActive not implemented")
    
  def setConfig(self, data):
    self._config = data
    if self._isActive:
      self._inputWidget.setConfig(self._config.get("input", {}))
      self._outputWidget.setConfig(self._config.get("output", {}))
      self._workBenchWidget.setConfig(self._config.get("workBench", {}))
    
  def getConfig(self):
    ret = self._config
    if self._isActive:
      ret = {"input" : self._inputWidget.getConfig(),
             "output" : self._outputWidget.getConfig(),
             "workBench" : self._workBenchWidget.getConfig()}
    return ret
    
  def _explore(self):
    raise NotImplementedError("RenamerModule._explore not implmemented")

  def _rename(self):
    raise NotImplementedError("RenamerModule._rename not implmemented")
    
  def _stopThread(self):
    if self._workerThread:
      self._workerThread.join()
    
  def _onThreadFinished(self):    
    if not self._isShuttingDown:
      self._inputWidget.stopSearching()
      self._outputWidget.stopActioning()
      self._enableControls(True)      
      
  def _stopRename(self):
    self._outputWidget.stopButton.setEnabled(False)
    self._stopThread()
   
  def _stopSearch(self):
    self._inputWidget.stopButton.setEnabled(False)
    self._stopThread()
    
  def _enableControls(self, isEnabled=True):
    self._inputWidget.enableControls(isEnabled)
    self._workBenchWidget.setEnabled(isEnabled)
    self._outputWidget.enableControls(isEnabled)    
    
  def _updateSearchProgress(self, percentageComplete):
    """ Update progress. Assumed to be main thread """
    utils.verifyType(percentageComplete, int)
    self._inputWidget.progressBar.setValue(percentageComplete)

  def _addMessage(self, msg):
    """ Add message to log. Assumed to be main thread """
    self._logWidget.appendMessage(msg)

  def _updateRenameProgress(self, percentageComplete):
    """ Update progress. Assumed to be main thread """
    utils.verifyType(percentageComplete, int)
    self._outputWidget.progressBar.setValue(percentageComplete)

