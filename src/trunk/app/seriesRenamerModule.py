#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module responsible for the renaming of tv series
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

from common import extension
from common import fileHelper
from common import moveItemActioner
from common import outputFormat
from common import logModel
from common import utils

from tv import season
from tv import seasonHelper

import renamerModule
import outputWidget     
    
# --------------------------------------------------------------------------------------------------------------------
class SeriesExploreThread(renamerModule.ExploreThread):
    
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
                                 "Search complete. %d folders processed." % (len(dirs))))

# --------------------------------------------------------------------------------------------------------------------
class SeriesRenamerModule(renamerModule.RenamerModule):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, inputWidget, outputWidget, workbenchWidget, logWidget, parent=None):
    super(SeriesRenamerModule, self).__init__(renamerModule.Mode.TV_MODE, 
                                              outputFormat.TvInputMap,
                                              workbenchWidget.tvModel,
                                              SeriesExploreThread,
                                              inputWidget, 
                                              outputWidget, 
                                              workbenchWidget, 
                                              logWidget, 
                                              parent)
    self._setInactive()
    #set model
  
  def _setActive(self):
    self._workBenchWidget.movieButton.setVisible(True)  
    self._workBenchWidget.editSeasonButton.setVisible(True)
    self._workBenchWidget.editEpisodeButton.setVisible(True)
    self._workBenchWidget.tvView.setVisible(True)
      
  def _setInactive(self):
    self._workBenchWidget.movieButton.setVisible(False)
    self._workBenchWidget.editSeasonButton.setVisible(False)
    self._workBenchWidget.editEpisodeButton.setVisible(False) 
    self._workBenchWidget.tvView.setVisible(False)

  def _getRenameItems(self):
    filenames = []
    seasons = self._model.items()
    utils.verify(seasons, "Must have seasons to have gotten this far")
    formatSettings = self._outputWidget.getConfig()
    for season in seasons:
      outputFolder = formatSettings["folder"]
      if outputFolder == outputWidget.USE_SOURCE_DIRECTORY:
        outputFolder = season.inputFolder_
      oFormat = outputFormat.OutputFormat(formatSettings["format"])
      for ep in season.moveItemCandidates:
        if ep.performMove:
          im = outputFormat.TvInputMap(season.seasonName, 
                                       season.seasonNum, 
                                       ep.destination.epNum, 
                                       ep.destination.epName)
          newName = oFormat.outputToString(im, ep.source.extension_, outputFolder)
          newName = fileHelper.FileHelper.sanitizeFilename(newName)
          filenames.append((ep.source.filename, newName))
    utils.verify(filenames, "Must have files to have gotten this far")
    return filenames      
    
