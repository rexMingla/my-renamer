#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Base module responsible for the renaming of movies and tv series
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

import collections

from common import outputFormat
from common import extension
from common import fileHelper
from common import logModel
from common import moveItemActioner
from common import manager
from common import utils
from common import thread

from tv import tvManager
from tv import tvInfoClient

from movie import movieManager
from movie import movieInfoClient

import config
import editSourcesWidget
import inputWidget
import outputWidget
import workBenchWidget

# --------------------------------------------------------------------------------------------------------------------
class ModuleFactory:
  @staticmethod
  def createModule(mode, mw):
    if mode == Mode.MOVIE_MODE:
      store = movieInfoClient.getStore()
      manager = movieManager.getManager()
      return MovieRenamerModule(editSourcesWidget.EditSourcesWidget(store, mw),
                                inputWidget.InputWidget(mode, store, mw), 
                                outputWidget.OutputWidget(mode, outputFormat.MovieInputMap, mw),
                                workBenchWidget.MovieWorkBenchWidget(manager, mw),
                                manager,
                                moveItemActioner.BaseRenameItemGeneratorVisitor)
    else:
      store = tvInfoClient.getStore()
      manager = tvManager.getManager()
      return TvRenamerModule(editSourcesWidget.EditSourcesWidget(store, mw),
                             inputWidget.InputWidget(mode, store, mw), 
                             outputWidget.OutputWidget(mode, outputFormat.TvInputMap, mw),
                             workBenchWidget.TvWorkBenchWidget(manager, mw),
                             manager,
                             moveItemActioner.BaseRenameItemGeneratorVisitor)

# --------------------------------------------------------------------------------------------------------------------
class RenameThread(thread.AdvancedWorkerThread):  
  def __init__(self, name, renameVisitor):
    super(RenameThread, self).__init__(name)
    self._renameVisitor = renameVisitor
    
  def _getAllItems(self):
    return self._renameVisitor.getRenamerItems()
   
  def _applyToItem(self, item):
    ret = item.performAction()
    return item, item.resultStr(ret)
    
  def _formatLogItem(self, item, result):
    return item.resultToLogItem(result)
    
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
  logSignal = QtCore.pyqtSignal(object)
  
  def __init__(self, mode, editSourcesWidget_, inputWidget_, outputWidget_, workBenchWidget_, manager_, renameVisitorFn_, 
               parent=None):
    super(RenamerModule, self).__init__(parent)
    
    self.mode = mode
    self.editSourcesWidget = editSourcesWidget_
    self.editSourcesWidget.setVisible(False)    
    self.inputWidget = inputWidget_
    self.outputWidget = outputWidget_
    self.workBenchWidget = workBenchWidget_
    self._manager = manager_
    self._renameVisitorFn = renameVisitorFn_
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
      
    data = self.inputWidget.getConfig()
    self._workerThread = thread.AdvancedWorkerThread("explore {}".format(self.mode), 
                                                     self._getExploreItems, 
                                                     self._transformExploreItem)
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

    renameVisitor = self._renameVisitorFn(self.outputWidget.getConfig(), self.workBenchWidget.actionableItems())
    self._workerThread = RenameThread("rename {}".format(self.mode), renameVisitor)
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

# --------------------------------------------------------------------------------------------------------------------
class TvRenamerModule(RenamerModule):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, editSourcesWidget, inputWidget, outputWidget, workbenchWidget, manager, renameVisitorFn, parent=None):
    super(TvRenamerModule, self).__init__(Mode.TV_MODE, 
                                          editSourcesWidget, 
                                          inputWidget, 
                                          outputWidget, 
                                          workbenchWidget, 
                                          manager,
                                          renameVisitorFn,
                                          parent)  
    
  def _getExploreItems(self):
    data = self.inputWidget.getConfig()
    return self._manager.helper.getFolders(data["folder"], data["recursive"])
    
  def _transformExploreItem(self, item):
    data = self.inputWidget.getConfig()
    season = self._manager.getSeasonForFolder(item, 
                                              extension.FileExtensions(data["extensions"].split()), 
                                              data["minFileSizeBytes"]) 
    if season:
      return season, season.resultStr(season.status)
    else:
      return None, None
  
# --------------------------------------------------------------------------------------------------------------------
class MovieRenamerModule(RenamerModule):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, editSourcesWidget, inputWidget, outputWidget, workbenchWidget, manager, renameVisitorFn, parent=None):
    super(MovieRenamerModule, self).__init__(Mode.MOVIE_MODE, 
                                             editSourcesWidget, 
                                             inputWidget, 
                                             outputWidget, 
                                             workbenchWidget, 
                                             manager,
                                             renameVisitorFn,
                                             parent)
   
  def _getExploreItems(self):
    data = self.inputWidget.getConfig()
    ext = extension.FileExtensions(["*"] if data["allExtensions"] else data["extensions"].split())
    minSize = 0 if data["allFileSizes"] else data["minFileSizeBytes"]
    return self._manager.helper.getFiles(data["folder"], ext, data["recursive"], minSize)
    
  def _transformExploreItem(self, item):
    item = self._manager.processFile(item)
    if item:
      return item, movieManager.Result.resultStr(item.result)
    else:
      return None, None
    