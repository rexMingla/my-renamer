#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module responsible for the renaming of tv series
# --------------------------------------------------------------------------------------------------------------------
import collections
from PyQt4 import QtCore, QtGui

from common import extension, fileHelper, moveItemActioner, logModel, utils
from tv import outputFormat, season, seasonHelper

import inputWidget
import logWidget
import outputWidget
import workBenchWidget

class MyThread(QtCore.QThread):
  progressSignal_ = QtCore.pyqtSignal(int)
  logSignal_ = QtCore.pyqtSignal(object)
  newDataSignal_ = QtCore.pyqtSignal(object)

  def __init__(self):
    super(MyThread, self).__init__()
    self.userStopped = False
  
  def __del__(self):
    self.join()
    
  def join(self):
    self.userStopped = True
    
  def _onLog(self, msg):
    self.logSignal_.emit(msg)
  
  def _onProgress(self, percentage):
    self.progressSignal_.emit(percentage)
    
  def _onNewData(self, data):
    self.newDataSignal_.emit(data)

class RenameThread(MyThread):  
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
      if self.userStopped:
        return
      res = self._actioner.performAction(source, dest)
      self._onLog(moveItemActioner.MoveItemActioner.resultToLogItem(res, source, dest))
      if not results.has_key(res):
        results[res] = 0  
      results[res] += 1  
      self._onProgress(int(100 * (i + 1) / len(self._items)))
    self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                 "Rename / move complete", 
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
      if self.userStopped:
        return
      s = seasonHelper.SeasonHelper.getSeasonForFolder(d, self._ext)
      if s:
        self._onNewData(s)
      self._onProgress(int(100 * (i + 1) / len(dirs)))
      
    """ Protected function of QThread.
    try:
      utils.out("running %s" % self.func_.func_name, 1)
      self.ret_ = self.func_(self.args_)
      utils.out("finished: %s success" % self.func_.func_name, 1)
    except:
      utils.out("finished: %s failed" % self.func_.func_name)
      pass"""

# --------------------------------------------------------------------------------------------------------------------
class SeriesRenamerModule(QtCore.QObject):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, parent=None):
    super(QtCore.QObject, self).__init__(parent)
    
    #input widget
    self.inputWidget_ = inputWidget.InputWidget(parent)
    self.inputWidget_.exploreSignal_.connect(self._explore)
    self.inputWidget_.stopSignal_.connect(self._stopSearch)
    
    #workbench widget
    self.workBenchWidget_ = workBenchWidget.WorkBenchWidget(parent)
    
    #output widget
    self.outputWidget_ = outputWidget.OutputWidget(parent)
    self.outputWidget_.renameSignal_.connect(self._rename)
    self.workBenchWidget_.workBenchChangedSignal_.connect(self.outputWidget_.enableControls)
    self.inputProgressBar_ = self.inputWidget_.progressBar_
    self.inputProgressBar_.setVisible(False)
    
    #progress widget
    self.outputProgressBar_ = self.outputWidget_.progressBar_
    self.outputProgressBar_.setVisible(False)
    
    #log widget
    self.logWidget_ = logWidget.LogWidget(parent)
    #self._postMessageSignal_.connect(self._postedAddMessage)
    self.lastLogMessage_ = None
    
    self._workerThread = None
    self._isShuttingDown = False
    
  def __del__(self):
    self._isShuttingDown = True
    self._stopThread()
    
  def _explore(self):
    self._enableControls(False)
    self.workBenchWidget_.setSeasons([])
    self.inputWidget_.startSearching()
    data = self.inputWidget_.getConfig()
    assert(not self._workerThread or not self._workerThread.isRunning())
    self._workerThread = ExploreThread(data["folder"], 
                                       data["recursive"], 
                                       extension.FileExtensions(data["extensions"].split()))
    self._workerThread.progressSignal_.connect(self._updateSearchProgress)
    self._workerThread.newDataSignal_.connect(self._onSeasonFound)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()    

  def _rename(self):
    self._enableControls(False)
    self.logWidget_.onRename()
    formatSettings = self.outputWidget_.getConfig()
    filenames = []
    seasons = self.workBenchWidget_.seasons()
    utils.verify(seasons, "Must have seasons to have gotten this far")
    for season in seasons:
      outputFolder = formatSettings["folder"]
      if outputFolder == outputWidget.USE_SOURCE_DIRECTORY:
        outputFolder = season.inputFolder_
      oFormat = outputFormat.OutputFormat(formatSettings["format"])
      for ep in season.moveItemCandidates_:
        if ep.performMove_:
          im = outputFormat.InputMap(season.seasonName_, 
                                     season.seasonNum_, 
                                     ep.destination_.epNum_, 
                                     ep.destination_.epName_)
          outputBaseName = oFormat.outputToString(im, ep.source_.extension_)
          newName = fileHelper.FileHelper.joinPath(outputFolder, outputBaseName)
          newName = fileHelper.FileHelper.sanitizeFilename(newName)
          filenames.append((ep.source_.filename_, newName))
    utils.verify(filenames, "Must have files to have gotten this far")
    actioner = moveItemActioner.MoveItemActioner(canOverwrite= not formatSettings["dontOverwrite"], \
                                                 keepSource=not formatSettings["move"])
    assert(not self._workerThread or not self._workerThread.isRunning())
    self._addMessage(logModel.LogItem(logModel.LogLevel.INFO, "Starting...", ""))
    
    self.outputWidget_.startActioning()
    self._workerThread = RenameThread(actioner, filenames)
    self._workerThread.progressSignal_.connect(self._updateRenameProgress)
    self._workerThread.logSignal_.connect(self._addMessage)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()
    
  def _stopThread(self):
    self._workerThread.join()
    
  def _onThreadFinished(self):    
    if not self._isShuttingDown:
      self.inputWidget_.stopSearching()
      self.outputWidget_.stopActioning()
      self._enableControls(True)      
      
  def _stopRename(self):
    self._stopThread()
   
  def _stopSearch(self):
    self._stopThread()
    
  def _enableControls(self, isEnabled=True):
    self.inputWidget_.enableControls(isEnabled)
    self.workBenchWidget_.setEnabled(isEnabled)
    self.outputWidget_.enableControls(isEnabled)
    
  def _onSeasonFound(self, season):
    if season:
      self.workBenchWidget_.addSeason(season)    
    
  def _updateSearchProgress(self, percentageComplete):
    """ Update progress. Assumed to be main thread """
    utils.verifyType(percentageComplete, int)
    self.inputProgressBar_.setValue(percentageComplete)

  def _addMessage(self, msg):
    """ Add message to log. Assumed to be main thread """
    self.logWidget_.appendMessage(msg)

  def _updateRenameProgress(self, percentageComplete):
    """ Update progress. Assumed to be main thread """
    utils.verifyType(percentageComplete, int)
    self.outputProgressBar_.setValue(percentageComplete)

