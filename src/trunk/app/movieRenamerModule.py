#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module responsible for the renaming of movies
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

from common import extension, fileHelper, moveItemActioner, logModel, utils
from tv import outputFormat, season, seasonHelper

import renamerModule
import outputWidget

"""# --------------------------------------------------------------------------------------------------------------------
class RenameThread(renamerModule.MyThread):  
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
    
# --------------------------------------------------------------------------------------------------------------------
class ExploreThread(renamerModule.MyThread):
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
class MovieRenamerModule(renamerModule.RenamerModule):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, inputWidget, outputWidget, workbenchWidget, logWidget, parent=None):
    super(MovieRenamerModule, self).__init__(renamerModule.Mode.MOVIE_MODE, 
                                             inputWidget, 
                                             outputWidget, 
                                             workbenchWidget, 
                                             logWidget, 
                                             parent)
    self._setInactive()

  def _setActive(self):
    self._workBenchWidget.tvButton.setVisible(True)
    self._workBenchWidget.editMovieButton.setVisible(True)
  
  def _setInactive(self):
    self._workBenchWidget.tvButton.setVisible(False)
    self._workBenchWidget.editMovieButton.setVisible(False)
  
  def _explore(self):
    self._enableControls(False)
    self._workBenchWidget.setSeasons([])
    self._inputWidget.startSearching()
    data = self._inputWidget.getConfig()
    assert(not self._workerThread or not self._workerThread.isRunning())
    self._workerThread = ExploreThread(data["folder"], 
                                       data["recursive"], 
                                       extension.FileExtensions(data["extensions"].split()))
    self._workerThread.progressSignal_.connect(self._updateSearchProgress)
    self._workerThread.newDataSignal_.connect(self._onMovieFound)
    self._workerThread.logSignal_.connect(self._addMessage)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()    

  def _rename(self):
    self._enableControls(False)
    self._logWidget.onRename()
    formatSettings = self._outputWidget.getConfig()
    filenames = []
    movies = self._workBenchWidget.movies()
    utils.verify(movies, "Must have movies to have gotten this far")
    for movie in movies:
      pass 
    """outputFolder = formatSettings["folder"]
      if outputFolder == outputWidget.USE_SOURCE_DIRECTORY:
        outputFolder = season.inputFolder_
      oFormat = outputFormat.OutputFormat(formatSettings["format"])
      for ep in season.moveItemCandidates:
        if ep.performMove_:
          im = outputFormat.MovieInputMap(season.seasonName, 
                                         season.seasonNum, 
                                       ep.destination.epNum, 
                                       ep.destination.epName)
          outputBaseName = oFormat.outputToString(im, ep.source.extension_)
          newName = fileHelper.FileHelper.joinPath(outputFolder, outputBaseName)
          newName = fileHelper.FileHelper.sanitizeFilename(newName)
          filenames.append((ep.source.filename, newName))
    utils.verify(filenames, "Must have files to have gotten this far")
    actioner = moveItemActioner.MoveItemActioner(canOverwrite= not formatSettings["dontOverwrite"], \
                                                 keepSource=not formatSettings["move"])
    assert(not self._workerThread or not self._workerThread.isRunning())
    self._addMessage(logModel.LogItem(logModel.LogLevel.INFO, "Starting...", ""))
    
    self._outputWidget.startActioning()
    self._workerThread = RenameThread(actioner, filenames)
    self._workerThread.progressSignal_.connect(self._updateRenameProgress)
    self._workerThread.logSignal_.connect(self._addMessage)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()"""
    
  def _onMovieFound(self, movie):
    if movie:
      pass#self._workBenchWidget.addMovie(movie)    
    
