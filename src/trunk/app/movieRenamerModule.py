#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module responsible for the renaming of movies
# --------------------------------------------------------------------------------------------------------------------
from common import fileHelper
from common import logModel
from common import outputFormat
from common import utils
from movie import movieHelper

import config
import renamerModule
import outputWidget

# --------------------------------------------------------------------------------------------------------------------
class MovieExploreThread(renamerModule.ExploreThread):
  def run(self):
    files = movieHelper.MovieHelper.getFiles(self._folder, self._ext, self._isRecursive)
    hist = {} #result histogram
    i = 0
    for i, file in enumerate(files):
      movie = movieHelper.MovieHelper.processFile(file)
      self._onNewData(movie)
      self._onProgress(int(100 * (i + 1) / len(files)))
      if self.userStopped:
        self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                     "Search", 
                                     "User cancelled. %d of %d files processed." % (i + 1, len(files))))              
        break
    self._onLog(logModel.LogItem(logModel.LogLevel.INFO, 
                                 "Search", 
                                 "Search complete. %d files processed in %s." % (i + 1,
                                                                                 renamerModule.prettyTime(self.startTime))))

# --------------------------------------------------------------------------------------------------------------------
class MovieRenamerModule(renamerModule.RenamerModule):
  """ 
  Class responsible for the input, output, working and logging components.
  This class manages all interactions required between the components.
  """  
  def __init__(self, inputWidget, outputWidget, workbenchWidget, logWidget, parent=None):
    super(MovieRenamerModule, self).__init__(renamerModule.Mode.MOVIE_MODE, 
                                             workbenchWidget.movieModel,
                                             MovieExploreThread,
                                             inputWidget, 
                                             outputWidget, 
                                             workbenchWidget, 
                                             logWidget, 
                                             parent)
    
  def _getRenameItems(self):
    filenames = []
    movies = self._model.items()
    utils.verify(movies, "Must have movies to have gotten this far")
    formatSettings = self._outputWidget.getConfig()
    oFormat = outputFormat.OutputFormat(formatSettings["format"])
    for movie in movies:
      outputFolder = formatSettings["folder"]
      if outputFolder == config.USE_SOURCE_DIRECTORY:
        outputFolder = movie.inPath
      genre = movie.genre("unknown")
      im = outputFormat.MovieInputMap(movie.title, movie.year, genre)
      newName = oFormat.outputToString(im, movie.ext, outputFolder)
      newName = fileHelper.FileHelper.sanitizeFilename(newName)
      filenames.append((movie.filename, newName))
    return filenames   
    
