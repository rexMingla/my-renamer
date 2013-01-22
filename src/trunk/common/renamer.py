#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Class responsible for the moving/copying of files
# --------------------------------------------------------------------------------------------------------------------
import abc

import extension
import file_helper
import formatting
import utils

# --------------------------------------------------------------------------------------------------------------------
class BaseRenameItemGenerator(object):
  """ converts an item a BaseRenamer object """
  __metaclass__ = abc.ABCMeta
  
  def __init__(self, inputValues=None, config=None):
    super(BaseRenameItemGenerator, self).__init__()
    self.inputValues = inputValues
    self.config = config or {}
    
  @abc.abstractmethod
  def getRenameItem(self, item):
    pass

# --------------------------------------------------------------------------------------------------------------------
class RenameItemGenerator(BaseRenameItemGenerator):
  """ converts an item a BaseRenamer object """
  
  def __init__(self, formatter=None, config=None):
    super(RenameItemGenerator, self).__init__()
    self._formatter = formatter
    self.config = config or {}
    
  def getRenameItem(self, item):
    if self.config.getOutputFolder():
      item.outputFolder = self.config.getOutputFolder()
    name = file_helper.FileHelper.sanitizeFilename(self._formatter.getName(self.config.format, item))
    return FileRenamer(item.filename, name, canOverwrite=not self.config.dontOverwrite, 
                                            keepSource=not self.config.isMove,
                                            subtitleExtensions=self.config.getSubtitles())
    
# --------------------------------------------------------------------------------------------------------------------    
class BaseRenamer(object):
  """ performs rename on file """
  __metaclass__ = abc.ABCMeta
  def __init__(self):
    super(BaseRenamer, self).__init__()
    
  @abc.abstractmethod
  def performAction(self, progressCb=None):
    pass
    
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

  def __init__(self, source, dest, canOverwrite, keepSource, subtitleExtensions=None):
    super(FileRenamer, self).__init__()
    self.source = source
    self.dest = dest
    self.canOverwrite = canOverwrite
    self.keepSource = keepSource
    self.subtitleExtensions = subtitleExtensions or []
    
  def resultToLogItem(self, res):
    longText = "{} -> {}".format(self.source, self.dest) 
    shortText = "{} -> {}".format(file_helper.FileHelper.basename(self.source), file_helper.FileHelper.basename(self.dest))
    numExtFiles = len(self._extensionFiles())
    if res == FileRenamer.SUCCESS and numExtFiles:
      longText += " #subtitle files:{}".format(numExtFiles)
      shortText += " #subtitle files:{}".format(numExtFiles)
    level = utils.LogLevel.INFO
    if res != FileRenamer.SUCCESS:
      level = utils.LogLevel.ERROR
    return utils.LogItem(level, FileRenamer.resultStr(res), shortText, longText)
  
  def performAction(self, progressCb=None):
    """ Move/Copy a file from source to destination. """
    #sanity checks
    if not file_helper.FileHelper.fileExists(self.source):
      return FileRenamer.SOURCE_DOES_NOT_EXIST
    if not file_helper.FileHelper.isValidFilename(self.dest):
      return FileRenamer.INVALID_FILENAME
    elif self.source == self.dest:
      return FileRenamer.SUCCESS
    elif file_helper.FileHelper.fileExists(self.dest) and not self.canOverwrite:
      return FileRenamer.COULD_NOT_OVERWRITE    

    if self.keepSource:
      return self._copyFile(progressCb)
    else:
      return self._moveFile(progressCb)    
    
  def _extensionFiles(self):
    ret = []
    for ext in self.subtitleExtensions:
      sub = file_helper.FileHelper.changeExtension(self.source, ext)
      if sub != self.source and file_helper.FileHelper.fileExists(sub):
        ret.append(sub)
    return ret
  
  def _moveFile(self, progressCb):
    if file_helper.FileHelper.moveFile(self.source, self.dest, progressCb):
      for sub in self._extensionFiles():
        file_helper.FileHelper.moveFile(sub, file_helper.FileHelper.changeExtension(self.dest, 
                                                                                  file_helper.FileHelper.extension(sub)))
      return FileRenamer.SUCCESS
    else:
      return FileRenamer.FAILED
    
  def _copyFile(self, progressCb):
    if file_helper.FileHelper.copyFile(self.source, self.dest, progressCb):
      for sub in self._extensionFiles():
        file_helper.FileHelper.copyFile(sub, file_helper.FileHelper.changeExtension(self.dest, 
                                                                                  file_helper.FileHelper.extension(sub)))
      return FileRenamer.SUCCESS
    else:
      return FileRenamer.FAILED
    