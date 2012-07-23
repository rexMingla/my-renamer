#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Base module responsible for the renaming of movies and tv series
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

import collections

from common import extension
from common import fileHelper
from common import logModel
from common import moveItemActioner
from common import utils
from common import thread

# --------------------------------------------------------------------------------------------------------------------
class RenameThread(thread.WorkerThread):  
  def __init__(self, mode, actioner, items):
    super(RenameThread, self).__init__()
    utils.verifyType(actioner, moveItemActioner.MoveItemActioner)
    utils.verifyType(items, list)
    self._mode = mode
    self._actioner = actioner
    self._items = items
    
  def run(self):
    results = collections.defaultdict(int) #hist
    for i, item in enumerate(self._items):
      source, dest = item
      res = self._actioner.performAction(source, dest)
      self._onLog(moveItemActioner.MoveItemActioner.resultToLogItem(res, source, dest))
      results[res] += 1
      self._onProgress(int(100 * (i + 1) / len(self._items)))
      if self.userStopped:
        self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                     self._mode,
                                     "User cancelled. {} of {} files actioned.".format(i + 1, len(self._items))))              
        break
    self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                 self._mode,
                                 "Duration: {}. {}".format(prettyTime(self.startTime),
                                                           moveItemActioner.MoveItemActioner.summaryText(results))))   
    
# --------------------------------------------------------------------------------------------------------------------
class ExploreThread(thread.WorkerThread):
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
  def __init__(self, mode, model, exploreFunctor, 
               inputWidget_, outputWidget_, workBenchWidget_, logWidget_, parent=None):
    super(RenamerModule, self).__init__(parent)
    
    self.mode = mode
    self._inputWidget = inputWidget_
    self._outputWidget = outputWidget_
    self._workBenchWidget = workBenchWidget_
    self._logWidget = logWidget_
    self._widgets = (self._inputWidget, self._outputWidget, self._workBenchWidget)
    
    self._workerThread = None
    self._isShuttingDown = False
    self._exploreFunctor = exploreFunctor
    self._model = model    
    
  def __del__(self):
    self._isShuttingDown = True
    self._stopThread()
    
  def _explore(self):
    if self._workerThread and self._workerThread.isRunning():
      return

    for w in self._widgets:
      w.startExploring()
      
    self._logWidget.onRename()      
    data = self._inputWidget.getConfig()
    self._workerThread = self._exploreFunctor(data["folder"], 
                                              data["recursive"], 
                                              extension.FileExtensions(data["extensions"].split()))
    self._workerThread.progressSignal.connect(self._inputWidget.progressBar.setValue)
    self._workerThread.newDataSignal.connect(self._onDataFound)
    self._workerThread.logSignal.connect(self._logWidget.appendMessage)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()   
    
  def _rename(self):
    if self._workerThread and self._workerThread.isRunning():
      return
    
    for w in self._widgets:
      w.startActioning()

    self._logWidget.onRename()
    
    formatSettings = self._outputWidget.getConfig()
    filenames = self._getRenameItems()
    actioner = moveItemActioner.MoveItemActioner(canOverwrite= not formatSettings["dontOverwrite"], \
                                                 keepSource=not formatSettings["move"])    
    self._outputWidget.startActioning()
    self._workerThread = RenameThread(self.mode, actioner, filenames)
    self._workerThread.progressSignal.connect(self._outputWidget.progressBar.setValue)
    self._workerThread.logSignal.connect(self._logWidget.appendMessage)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()
    
  def _getRenameItems(self):  
    raise NotImplementedError("RenamerModule._getRenameItems()")
    
  def setActive(self):
    for w in self._widgets:
      w.setMode(self.mode)    
        
    self._outputWidget.renameSignal.connect(self._rename)
    self._outputWidget.stopSignal.connect(self._stopRename)
    self._inputWidget.exploreSignal.connect(self._explore)
    self._inputWidget.stopSignal.connect(self._stopSearch)
        
  def setInactive(self):
    for w in self._widgets:
      w.setMode(None)    
    self._stopThread() #TODO: maybe prompt? In future, run in background.
    
    try:
      self._outputWidget.renameSignal.disconnect(self._rename)
      self._outputWidget.stopSignal.disconnect(self._stopRename)
      self._inputWidget.exploreSignal.disconnect(self._explore)
      self._inputWidget.stopSignal.disconnect(self._stopSearch)       
    except TypeError:
      pass #lazy. should be able to check for conns
    
  def _stopThread(self):
    if self._workerThread:
      self._workerThread.join()
    
  def _onThreadFinished(self):    
    if not self._isShuttingDown:
      for w in self._widgets:
        w.stopExploring()
        w.stopActioning()
      
  def _stopRename(self):
    self._outputWidget.stopButton.setEnabled(False)
    self._stopThread()
   
  def _stopSearch(self):
    self._inputWidget.stopButton.setEnabled(False)
    self._stopThread()  
    
  def _onDataFound(self, data):
    self._model.addItem(data)    

