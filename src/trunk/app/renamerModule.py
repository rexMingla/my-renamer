#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Base module responsible for the renaming of movies and tv series
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

from common import extension
from common import interfaces
from common import thread
from common import utils

from movie import movieManager

import factory

# --------------------------------------------------------------------------------------------------------------------
class RenameThread(thread.AdvancedWorkerThread):  
  def __init__(self, name, renameVisitor):
    super(RenameThread, self).__init__(name)
    self._renameVisitor = renameVisitor
    
  def _getAllItems(self):
    return self._renameVisitor.getRenamerItems()
   
  def _applyToItem(self, item):
    ret = item.performAction(self._onPercentageComplete)
    return thread.WorkItem(item, item.resultStr(ret), item.resultToLogItem(ret))
  
  def _onPercentageComplete(self, percentage):
    overall = int((percentage + 100.0 * self._i) / self._numItems)
    self._onProgress(overall)
    return not self._userStopped
  
# --------------------------------------------------------------------------------------------------------------------
class SearchThread(thread.AdvancedWorkerThread):  
  def __init__(self, mode, manager, config):
    super(SearchThread, self).__init__("search {}".format(mode))
    self._manager = manager
    self._config = config

# --------------------------------------------------------------------------------------------------------------------
class TvSearchThread(SearchThread):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, manager, config):
    super(TvSearchThread, self).__init__(interfaces.Mode.TV_MODE, manager, config)  
    
  def _getAllItems(self):
    return self._manager.getFolders(self._config["folder"], self._config["recursive"])
    
  def _applyToItem(self, item):
    ext = extension.FileExtensions(["*"] if self._config["allExtensions"] else self._config["extensions"].split())
    minSize = 0 if self._config["allFileSizes"] else self._config["minFileSizeBytes"]
    season = self._manager.getSeasonForFolder(item, ext, minSize) 
    ret = None
    if season:
      ret = thread.WorkItem(season, season.resultStr(season.status))
    return ret
  
# --------------------------------------------------------------------------------------------------------------------
class MovieSearchThread(SearchThread):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, manager, config):
    super(MovieSearchThread, self).__init__(interfaces.Mode.MOVIE_MODE, manager, config)
   
  def _getAllItems(self):
    ext = extension.FileExtensions(["*"] if self._config["allExtensions"] else self._config["extensions"].split())
    minSize = 0 if self._config["allFileSizes"] else self._config["minFileSizeBytes"]
    return self._manager.helper.getFiles(self._config["folder"], ext, self._config["recursive"], minSize)
    
  def _applyToItem(self, item):
    item = self._manager.processFile(item)
    ret = None
    if item:
      ret = thread.WorkItem(item, movieManager.Result.resultStr(item.result))
    return ret

def getSearchThread(mode, manager, config):
  if mode == interfaces.Mode.MOVIE_MODE:
    return MovieSearchThread(manager, config)
  else:
    return TvSearchThread(manager, config)
    
# --------------------------------------------------------------------------------------------------------------------
class RenamerModule(QtCore.QObject):
  """ Class responsible for the input, output and workbench components and manages their interactions. """  
  logSignal = QtCore.pyqtSignal(object)
  
  def __init__(self, mode, parent=None):
    super(RenamerModule, self).__init__(parent)
    
    self.mode = mode
    self.editSourcesWidget = factory.Factory.getEditSourceWidget(mode, parent)
    self.editSourcesWidget.setVisible(False)    
    self.inputWidget = factory.Factory.getInputWidget(mode, parent)
    self.outputWidget = factory.Factory.getOutputWidget(mode, parent)
    self.workBenchWidget = factory.Factory.getWorkBenchWidget(mode, parent)
    self._manager = factory.Factory.getManager(mode)
    self._renamerItemGenerator = factory.Factory.getRenameItemGenerator(mode)
    self._widgets = (self.inputWidget, self.outputWidget, self.workBenchWidget)
    
    self.workBenchWidget.workBenchChangedSignal.connect(self.outputWidget.renameButton.setEnabled)
    self.outputWidget.renameSignal.connect(self._rename)
    self.outputWidget.stopSignal.connect(self._stopRename)
    self.workBenchWidget.showEditSourcesSignal.connect(self.editSourcesWidget.show)
    self.inputWidget.showEditSourcesSignal.connect(self.editSourcesWidget.show)
    self.editSourcesWidget.accepted.connect(self.inputWidget.onSourcesWidgetFinished)
    
    self.inputWidget.exploreSignal.connect(self._explore)
    self.inputWidget.stopSignal.connect(self._stopSearch)    
    
    self._workerThread = None
    self._isShuttingDown = False
    
  def __del__(self):
    self._isShuttingDown = True
    self._stopThread()
    
  def _explore(self):
    if self._workerThread and self._workerThread.isRunning():
      return

    for w in self._widgets:
      w.startExploring()
      
    self._workerThread = getSearchThread(self.mode, self._manager, self.inputWidget.getConfig()) 
    self._workerThread.progressSignal.connect(self.inputWidget.progressBar.setValue)
    self._workerThread.newDataSignal.connect(self.workBenchWidget.addItem)
    self._workerThread.logSignal.connect(self.logSignal)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()
    
  def _getExploreItems(self):
    raise NotImplementedError("RenamerModule._getExploreItems not implemented")
    
  def _transformExploreItem(self, item):
    raise NotImplementedError("RenamerModule._transformExploreItem not implemented")
    
  def _rename(self):
    if self._workerThread and self._workerThread.isRunning():
      return
    
    for w in self._widgets:
      w.startActioning()

    self._renamerItemGenerator.config = self.outputWidget.getConfig()
    self._renamerItemGenerator.items = self.workBenchWidget.actionableItems()
    self._workerThread = RenameThread("rename {}".format(self.mode), self._renamerItemGenerator)
    self._workerThread.progressSignal.connect(self.outputWidget.progressBar.setValue)
    self._workerThread.logSignal.connect(self.logSignal)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()
    
  def setActive(self):
    pass
        
  def setInactive(self):
    self._stopThread() #TODO: maybe prompt? In future, run in background.
    
  def _stopThread(self):
    if self._workerThread:
      self._workerThread.join()
    
  def _onThreadFinished(self):    
    if not self._isShuttingDown:
      for w in self._widgets:
        w.stopExploring()
        w.stopActioning()
      
  def _stopRename(self):
    self.outputWidget.stopButton.setEnabled(False)
    self._stopThread()
   
  def _stopSearch(self):
    self.inputWidget.stopButton.setEnabled(False)
    self._stopThread()     
