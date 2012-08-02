#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module responsible for the renaming of tv series
# --------------------------------------------------------------------------------------------------------------------
from common import fileHelper
from common import outputFormat
from common import thread
from common import logModel
from common import utils

from tv import seasonHelper

import config
import renamerModule

# --------------------------------------------------------------------------------------------------------------------
class SeriesExploreThread(renamerModule.ExploreThread): 
  def run(self):
    dirs = seasonHelper.SeasonHelper.getFolders(self._folder, self._isRecursive)
    folderCount = 0
    for i, d in enumerate(dirs):
      s = seasonHelper.SeasonHelper.getSeasonForFolder(d, self._ext, self._minFileSize)
      if s:
        self._onData(s)
        folderCount += 1
      if self.userStopped:
        self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                     "Search", 
                                     "User cancelled. {} of {} folders processed.".format(i, len(dirs))))              
        break
      self._onProgress(int(100 * (i + 1) / len(dirs)))
    
    self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                 "Search", 
                                 "Search complete. {} folders processed in {}".format(folderCount, 
                                                                                      thread.prettyTime(self.startTime))))

# --------------------------------------------------------------------------------------------------------------------
class SeriesRenamerModule(renamerModule.RenamerModule):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, inputWidget, outputWidget, workbenchWidget, logWidget, parent=None):
    super(SeriesRenamerModule, self).__init__(renamerModule.Mode.TV_MODE, 
                                              workbenchWidget.tvModel,
                                              SeriesExploreThread,
                                              inputWidget, 
                                              outputWidget, 
                                              workbenchWidget, 
                                              logWidget, 
                                              parent)
    
  def _getRenameItems(self):
    filenames = []
    seasons = self._model.items()
    utils.verify(seasons, "Must have seasons to have gotten this far")
    formatSettings = self._outputWidget.getConfig()
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
    
