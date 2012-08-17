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
from common import utils
from common import thread

from tv import seasonHelper
from movie import movieHelper

import config
import inputWidget
import outputWidget
import workBenchWidget

# --------------------------------------------------------------------------------------------------------------------
class ModuleFactory:
  @staticmethod
  def createModule(mode, parent):
    if mode == Mode.MOVIE_MODE:
      return MovieRenamerModule(inputWidget.InputWidget(mode, parent), 
                                outputWidget.OutputWidget(mode, outputFormat.MovieInputMap, parent),
                                workBenchWidget.MovieWorkBenchWidget(parent))
    else:
      return TvRenamerModule(inputWidget.InputWidget(mode, parent), 
                             outputWidget.OutputWidget(mode, outputFormat.TvInputMap, parent),
                             workBenchWidget.TvWorkBenchWidget(parent))

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
                                 "Duration: {}. {}".format(thread.prettyTime(self.startTime),
                                                           moveItemActioner.MoveItemActioner.summaryText(results))))   
    
# --------------------------------------------------------------------------------------------------------------------
class ExploreThread(thread.WorkerThread):
  def __init__(self, getExploreItemsCb, transformExploreItemCb):
    super(ExploreThread, self).__init__()
    self._getExploreItemsCb = getExploreItemsCb
    self._transformExploreItemCb = transformExploreItemCb
    
  def run(self):
    items = self._getExploreItemsCb()
    itemCount = 0
    for i, item in enumerate(items):
      item = self._transformExploreItemCb(item)
      if item:
        self._onData(item)
        itemCount += 1
      if self.userStopped:
        self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                     "Search",
                                     "User cancelled. {} of {} items processed.".format(i, len(items))))              
        break
      self._onProgress(int(100.0 * (i + 1) / len(items)))
    
    self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                 "Search", 
                                 "Search complete. {} items processed in {}".format(itemCount, 
                                                                                    thread.prettyTime(self.startTime))))    
    
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
  
  def __init__(self, mode, inputWidget_, outputWidget_, workBenchWidget_, parent=None):
    super(RenamerModule, self).__init__(parent)
    
    self.mode = mode
    self.inputWidget = inputWidget_
    self.workBenchWidget = workBenchWidget_
    self.outputWidget = outputWidget_
    self.workBenchWidget.workBenchChangedSignal.connect(self.outputWidget.renameButton.setEnabled)     
    
    self.inputWidget = inputWidget_
    self.outputWidget = outputWidget_
    self.workBenchWidget = workBenchWidget_
    self._widgets = (self.inputWidget, self.outputWidget, self.workBenchWidget)
    
    self.outputWidget.renameSignal.connect(self._rename)
    self.outputWidget.stopSignal.connect(self._stopRename)
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
    self._workerThread = ExploreThread(self._getExploreItems, self._transformExploreItem)
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

    formatSettings = self.outputWidget.getConfig()
    filenames = self._getRenameItems()
    actioner = moveItemActioner.MoveItemActioner(canOverwrite= not formatSettings["dontOverwrite"], \
                                                 keepSource=not formatSettings["move"])    
    self.outputWidget.startActioning()
    self._workerThread = RenameThread(self.mode, actioner, filenames)
    self._workerThread.progressSignal.connect(self.outputWidget.progressBar.setValue)
    self._workerThread.logSignal.connect(self.logSignal)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()
    
  def _getRenameItems(self):  
    raise NotImplementedError("RenamerModule._getRenameItems()")
    
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
  def __init__(self, inputWidget_, outputWidget_, workbenchWidget_, parent=None):
    super(TvRenamerModule, self).__init__(Mode.TV_MODE, 
                                          inputWidget_, 
                                          outputWidget_, 
                                          workbenchWidget_, 
                                          parent)
    
  def _getRenameItems(self):
    filenames = []
    seasons = self.workBenchWidget.actionableItems()
    utils.verify(seasons, "Must have seasons to have gotten this far")
    formatSettings = self.outputWidget.getConfig()
    for season in seasons:
      outputFolder = formatSettings["folder"]
      if outputFolder == config.USE_SOURCE_DIRECTORY:
        outputFolder = season.inputFolder
      oFormat = outputFormat.OutputFormat(formatSettings["format"])
      for ep in season.moveItemCandidates:
        if ep.performMove:
          im = outputFormat.TvInputMap(fileHelper.FileHelper.replaceSeparators(season.seasonName), 
                                       season.seasonNum, 
                                       ep.destination.epNum, 
                                       fileHelper.FileHelper.replaceSeparators(ep.destination.epName))
          newName = oFormat.outputToString(im, ep.source.extension_, outputFolder)
          newName = fileHelper.FileHelper.sanitizeFilename(newName)
          filenames.append((ep.source.filename, newName))
    utils.verify(filenames, "Must have files to have gotten this far")
    return filenames      
    
  def _getExploreItems(self):
    data = self.inputWidget.getConfig()
    return seasonHelper.SeasonHelper.getFolders(data["folder"], data["recursive"])
    
  def _transformExploreItem(self, item):
    data = self.inputWidget.getConfig()
    return seasonHelper.SeasonHelper.getSeasonForFolder(item, 
                                                        extension.FileExtensions(data["extensions"].split()), 
                                                        data["minFileSizeBytes"]) 
  
# --------------------------------------------------------------------------------------------------------------------
class MovieRenamerModule(RenamerModule):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, inputWidget, outputWidget, workbenchWidget, parent=None):
    super(MovieRenamerModule, self).__init__(Mode.MOVIE_MODE, 
                                             inputWidget, 
                                             outputWidget, 
                                             workbenchWidget, 
                                             parent)
    
  def _getRenameItems(self):
    filenames = []
    movies = self.workBenchWidget.actionableItems()
    utils.verify(movies, "Must have movies to have gotten this far")
    formatSettings = self.outputWidget.getConfig()
    oFormat = outputFormat.OutputFormat(formatSettings["format"])
    for movie in movies:
      outputFolder = formatSettings["folder"]
      if outputFolder == config.USE_SOURCE_DIRECTORY:
        outputFolder = fileHelper.FileHelper.dirname(movie.filename)
      genre = movie.genre("unknown")
      im = outputFormat.MovieInputMap(fileHelper.FileHelper.replaceSeparators(movie.title), 
                                      movie.year, 
                                      fileHelper.FileHelper.replaceSeparators(genre), movie.part)
      newName = oFormat.outputToString(im, movie.ext, outputFolder)
      newName = fileHelper.FileHelper.sanitizeFilename(newName)
      filenames.append((movie.filename, newName))
    return filenames   
  
  def _getExploreItems(self):
    data = self.inputWidget.getConfig() 
    return movieHelper.MovieHelper.getFiles(data["folder"], 
                                            extension.FileExtensions(data["extensions"].split()), 
                                            data["recursive"],
                                            data["minFileSizeBytes"])
    
  def _transformExploreItem(self, item):
    return movieHelper.MovieHelper.processFile(item) 