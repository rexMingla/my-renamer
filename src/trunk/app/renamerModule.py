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

# --------------------------------------------------------------------------------------------------------------------
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

# --------------------------------------------------------------------------------------------------------------------
class RenameThread(MyThread):  
  def __init__(self, mode, actioner, items):
    super(RenameThread, self).__init__()
    utils.verifyType(actioner, moveItemActioner.MoveItemActioner)
    utils.verifyType(items, list)
    self._mode = mode
    self._actioner = actioner
    self._items = items
    
  def run(self):
    results = {} #hist
    for i, item in enumerate(self._items):
      source, dest = item
      res = self._actioner.performAction(source, dest)
      self._onLog(moveItemActioner.MoveItemActioner.resultToLogItem(res, source, dest))
      if not res in results:
        results[res] = 0  
      results[res] += 1  
      self._onProgress(int(100 * (i + 1) / len(self._items)))
      if self.userStopped:
        self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                     self._mode,
                                     "User cancelled. %d of %d files actioned." % (i, len(self._items))))              
        break
    self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                 self._mode,
                                 moveItemActioner.MoveItemActioner.summaryText(results)))      
    
# --------------------------------------------------------------------------------------------------------------------
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
    self._callback(self)
    
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
  def __init__(self, mode, outFormat, model, exploreFunctor, inputWidget_, outputWidget_, workBenchWidget_, logWidget_, parent=None):
    super(RenamerModule, self).__init__(parent)
    
    assert(mode in VALID_MODES)
    utils.verifyType(inputWidget_, inputWidget.InputWidget)
    utils.verifyType(outputWidget_, outputWidget.OutputWidget)
    utils.verifyType(workBenchWidget_, workBenchWidget.WorkBenchWidget)
    utils.verifyType(logWidget_, logWidget.LogWidget)

    self.mode = mode
    self._outFormat = outFormat
    self._inputWidget = inputWidget_
    self._outputWidget = outputWidget_
    self._workBenchWidget = workBenchWidget_
    self._logWidget = logWidget_
    
    self._workerThread = None
    self._isShuttingDown = False
    self._config = {}
    self._isActive = False
    self._exploreFunctor = exploreFunctor
    self._model = model
    
  def __del__(self):
    self._isShuttingDown = True
    self._stopThread()
    
  def _explore(self):
    self._enableControls(False)
    self._model.clear()
    self._inputWidget.startSearching()
    assert(not self._workerThread or not self._workerThread.isRunning())
    data = self._inputWidget.getConfig()
    self._workerThread = self._exploreFunctor(data["folder"], 
                                              data["recursive"], 
                                              extension.FileExtensions(data["extensions"].split()))
    self._workerThread.progressSignal.connect(self._updateSearchProgress)
    self._workerThread.newDataSignal.connect(self._onDataFound)
    self._workerThread.logSignal.connect(self._addMessage)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()   
    
  def _rename(self):
    self._enableControls(False)
    self._logWidget.onRename()
    formatSettings = self._outputWidget.getConfig()
    filenames = self._getRenameItems()
    actioner = moveItemActioner.MoveItemActioner(canOverwrite= not formatSettings["dontOverwrite"], \
                                                 keepSource=not formatSettings["move"])
    assert(not self._workerThread or not self._workerThread.isRunning())
    self._addMessage(logModel.LogItem(logModel.LogLevel.INFO, "Starting...", ""))
    
    self._outputWidget.startActioning()
    self._workerThread = RenameThread(self.mode, actioner, filenames)
    self._workerThread.progressSignal.connect(self._updateRenameProgress)
    self._workerThread.logSignal.connect(self._addMessage)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()
    
  def _getRenameItems(self):  
    raise NotImplementedError("RenamerModule._getRenameItems()")
    
  def setActive(self):
    self._outputWidget.setOutputFormat(self._outFormat) #dodgy... again.
    conf = self.getConfig()
    
    self._isActive = True
    self._outputWidget.renameSignal.connect(self._rename)
    self._inputWidget.exploreSignal.connect(self._explore)
    self._inputWidget.stopSignal.connect(self._stopSearch)
    self._workBenchWidget.setCurrentModel(self._model)
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
    self._workBenchWidget.setCurrentModel(None)    
    self._stopThread() #TODO: maybe prompt? In future, run in background.
    self._outputWidget.setOutputFormat(None)
    
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
    
  def _onDataFound(self, data):
    utils.verify(data, "Must have data!")
    if data:
      self._model.addItem(data)    

