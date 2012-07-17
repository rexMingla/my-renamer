#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module responsible for the renaming of movies
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

from common import extension
from common import fileHelper
from common import moveItemActioner
from common import logModel
from common import utils
from common import outputFormat
#from tv import season
#from tv import seasonHelper
from movie import movieHelper

import renamerModule
import outputWidget

# --------------------------------------------------------------------------------------------------------------------
class MovieExploreThread(renamerModule.ExploreThread):
  def run(self):
    files = movieHelper.MovieHelper.getFiles(self._folder, self._isRecursive)
    hist = {} #result histogram
    for i, file in enumerate(files):
      result, movie = movieHelper.MovieHelper.processFile(file)
      if movie:
        self._onNewData(movie)
      if self.userStopped:
        self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                     "Search", 
                                     "User cancelled. %d of %d files processed." % (i, len(files))))              
        break
      self._onProgress(int(100 * (i + 1) / len(files)))
    self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                 "Search", 
                                 "Search complete. %d files processed." % (len(files))))

# --------------------------------------------------------------------------------------------------------------------
class MovieRenamerModule(renamerModule.RenamerModule):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, inputWidget, outputWidget, workbenchWidget, logWidget, parent=None):
    super(MovieRenamerModule, self).__init__(renamerModule.Mode.MOVIE_MODE, 
                                             outputFormat.MovieInputMap,
                                             workbenchWidget.movieModel,
                                             MovieExploreThread,
                                             inputWidget, 
                                             outputWidget, 
                                             workbenchWidget, 
                                             logWidget, 
                                             parent)
    self._setInactive()
    
  def _setActive(self):
    self._workBenchWidget.tvButton.setVisible(True)
    self._workBenchWidget.editMovieButton.setVisible(True)
    self._workBenchWidget.movieView.setVisible(True)
  
  def _setInactive(self):
    self._workBenchWidget.tvButton.setVisible(False)
    self._workBenchWidget.editMovieButton.setVisible(False)
    self._workBenchWidget.movieView.setVisible(False)
    
  def _getRenameItems(self):
    return []  
    
