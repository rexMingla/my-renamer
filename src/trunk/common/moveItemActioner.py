#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Class responsible for the moving/copying of files
# --------------------------------------------------------------------------------------------------------------------
import fileHelper
import logModel
import utils
  
# --------------------------------------------------------------------------------------------------------------------
class MoveItemActioner:
  """ Class responsible for the moving/copying of files from source to destination """ 
  SOURCE_DOES_NOT_EXIST = -4
  COULD_NOT_OVERWRITE   = -3
  FAILED                = -2
  INVALID_FILENAME      = -1
  SUCCESS               = 1
  
  @staticmethod
  def resultStr(res):
    if res == MoveItemActioner.SOURCE_DOES_NOT_EXIST: return "Source does not exist"
    elif res == MoveItemActioner.COULD_NOT_OVERWRITE: return "Could not overwrite"
    elif res == MoveItemActioner.FAILED:              return "Failed"
    elif res == MoveItemActioner.INVALID_FILENAME:    return "Destination file invalid"
    else:
      utils.verify(res == MoveItemActioner.SUCCESS, "Invalid res")
      return "Success"

  def __init__(self, canOverwrite, keepSource):
    utils.verifyType(canOverwrite, bool)
    utils.verifyType(keepSource, bool)
    self.canOverwrite = canOverwrite
    self.keepSource = keepSource
  
  @staticmethod
  def resultToLogItem(res, source, dest):
    longText = "{} -> {}".format(source, dest) 
    shortText = "{} -> {}".format(fileHelper.FileHelper.basename(source), fileHelper.FileHelper.basename(dest))
    level = logModel.LogLevel.INFO
    if res != MoveItemActioner.resultStr(MoveItemActioner.SUCCESS):
      level = logModel.LogLevel.ERROR
    return logModel.LogItem(level, res, shortText, longText)
  
  def performAction(self, source, dest):
    """ Move/Copy a file from source to destination. """
    utils.verifyType(source, str)
    utils.verifyType(dest, str)
    #sanity checks
    if not fileHelper.FileHelper.fileExists(source):
      return MoveItemActioner.SOURCE_DOES_NOT_EXIST
    if not fileHelper.FileHelper.isValidFilename(dest):
      return MoveItemActioner.INVALID_FILENAME
    elif source == dest:
      return MoveItemActioner.SUCCESS
    elif fileHelper.FileHelper.fileExists(dest) and not self.canOverwrite:
      return MoveItemActioner.COULD_NOT_OVERWRITE    

    if self.keepSource:
      return self._copyFile(source, dest)
    else:
      return self._moveFile(source, dest)    
  
  def _moveFile(self, source, dest):
    utils.verifyType(source, str)
    utils.verifyType(dest, str)
    if fileHelper.FileHelper.moveFile(source, dest):
      return MoveItemActioner.SUCCESS
    else:
      return MoveItemActioner.FAILED
    
  def _copyFile(self, source, dest):
    utils.verifyType(source, str)
    utils.verifyType(dest, str)
    if fileHelper.FileHelper.copyFile(source, dest):
      return MoveItemActioner.SUCCESS
    else:
      return MoveItemActioner.FAILED
    

    