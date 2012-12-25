#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Class responsible for the moving/copying of files
# --------------------------------------------------------------------------------------------------------------------
import extension
import fileHelper
import logModel
import outputFormat
import utils
  
# --------------------------------------------------------------------------------------------------------------------
class BaseRenameItem(object):
  def __init__(self):
    super(BaseRenameItem, self).__init__()
    
  def itemToInfo(self):
    return NotImplementedError("BaseRenameItem.itemToInfo not implemented")      
    
# --------------------------------------------------------------------------------------------------------------------
class BaseRenameItemGenerator(object):
  """ generates list of item actioner """
  def __init__(self, config=None, items=None):
    super(BaseRenameItemGenerator, self).__init__()
    self.config = config or {}
    self.items = items or []
    
  def getRenamerItems(self):
    ret = []
    for item in self.items:
      ret.extend(self._getRenameItems(item))
    return ret
  
  def _getRenameItems(self, item):
    raise NotImplementedError("BaseRenameItemGenerator._getRenameItems not implemented")
    
# --------------------------------------------------------------------------------------------------------------------
class MovieRenameItemGenerator(BaseRenameItemGenerator):
  def _getRenameItems(self, movie):
    ret = []
    oFormat = outputFormat.OutputFormat(self.config["format"])
    outputFolder = self.config["folder"] or fileHelper.FileHelper.dirname(movie.filename)
    genre = movie.genre("unknown")
    im = outputFormat.MovieInputMap(fileHelper.FileHelper.replaceSeparators(movie.title), 
                                    movie.year, 
                                    fileHelper.FileHelper.replaceSeparators(genre), movie.part, movie.series)
    newName = oFormat.outputToString(im, movie.ext, outputFolder)
    newName = fileHelper.FileHelper.sanitizeFilename(newName)
    ret.append(FileRenamer(movie.filename, newName, canOverwrite=not self.config["dontOverwrite"], 
                                                    keepSource=not self.config["move"]))
    return ret   
  
# --------------------------------------------------------------------------------------------------------------------
class TvRenameItemGenerator(BaseRenameItemGenerator):
  def _getRenameItems(self, tv):
    ret = []
    outputFolder = self.config["folder"] or tv.inputFolder
    oFormat = outputFormat.OutputFormat(self.config["format"])
    for ep in tv.moveItemCandidates:
      if ep.performMove:
        im = outputFormat.TvInputMap(fileHelper.FileHelper.replaceSeparators(tv.seasonName), 
                                     tv.seasonNum, 
                                     ep.destination.epNum, 
                                     fileHelper.FileHelper.replaceSeparators(ep.destination.epName))
        newName = oFormat.outputToString(im, ep.source.ext, outputFolder)
        newName = fileHelper.FileHelper.sanitizeFilename(newName)
        ret.append(FileRenamer(ep.source.filename, newName, canOverwrite=not self.config["dontOverwrite"], 
                                                            keepSource=not self.config["move"]))
    return ret    
    
# --------------------------------------------------------------------------------------------------------------------    
class BaseRenamer(object):
  def __init__(self):
    super(BaseRenamer, self).__init__()
    
  def performAction(self, progressCb=None):
    raise NotImplementedError("BaseRenamer.performAction not implemented")
    
# --------------------------------------------------------------------------------------------------------------------
class FileRenamer(BaseRenamer):
  """ Class responsible for the moving/copying of files from source to destination """ 
  SOURCE_DOES_NOT_EXIST = -4
  COULD_NOT_OVERWRITE   = -3
  FAILED                = -2
  INVALID_FILENAME      = -1
  SUCCESS               = 1
  
  @staticmethod
  def resultStr(res):
    if res == FileRenamer.SOURCE_DOES_NOT_EXIST: return "Source does not exist"
    elif res == FileRenamer.COULD_NOT_OVERWRITE: return "Could not overwrite"
    elif res == FileRenamer.FAILED:              return "Failed"
    elif res == FileRenamer.INVALID_FILENAME:    return "Destination file invalid"
    else:
      utils.verify(res == FileRenamer.SUCCESS, "Invalid res")
      return "Success"

  def __init__(self, source, dest, canOverwrite, keepSource):
    super(FileRenamer, self).__init__()
    self.source = source
    self.dest = dest
    self.canOverwrite = canOverwrite
    self.keepSource = keepSource
    
  def resultToLogItem(self, res):
    longText = "{} -> {}".format(self.source, self.dest) 
    shortText = "{} -> {}".format(fileHelper.FileHelper.basename(self.source), fileHelper.FileHelper.basename(self.dest))
    level = logModel.LogLevel.INFO
    if res != FileRenamer.SUCCESS:
      level = logModel.LogLevel.ERROR
    return logModel.LogItem(level, FileRenamer.resultStr(res), shortText, longText)
  
  def performAction(self, progressCb=None):
    """ Move/Copy a file from source to destination. """
    #sanity checks
    if not fileHelper.FileHelper.fileExists(self.source):
      return FileRenamer.SOURCE_DOES_NOT_EXIST
    if not fileHelper.FileHelper.isValidFilename(self.dest):
      return FileRenamer.INVALID_FILENAME
    elif self.source == self.dest:
      return FileRenamer.SUCCESS
    elif fileHelper.FileHelper.fileExists(self.dest) and not self.canOverwrite:
      return FileRenamer.COULD_NOT_OVERWRITE    

    if self.keepSource:
      return self._copyFile(progressCb)
    else:
      return self._moveFile(progressCb)    
  
  def _moveFile(self, progressCb):
    if fileHelper.FileHelper.moveFile(self.source, self.dest, progressCb):
      return FileRenamer.SUCCESS
    else:
      return FileRenamer.FAILED
    
  def _copyFile(self, progressCb):
    if fileHelper.FileHelper.copyFile(self.source, self.dest, progressCb):
      return FileRenamer.SUCCESS
    else:
      return FileRenamer.FAILED
    