#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import fileHelper
import logModel
import utils
  
# --------------------------------------------------------------------------------------------------------------------
class MoveItemActioner:
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
    self.canOverwrite_ = canOverwrite
    self.keepSource_ = keepSource
    self.percentageCompleteCallback_ = None
    self.messageCallback_ = None
  
  def setPercentageCompleteCallback(self, cb):
    self.percentageCompleteCallback_ = cb
    
  def setMessageCallback(self, cb):
    self.messageCallback_ = cb
    
  def sendMessage(self, msg):
    if self.messageCallback_:
      self.messageCallback_(message)
      
  def summaryText(self, results):
    utils.verifyType(results, dict)
    ret = ""
    count = 0
    for key in results.keys():
      ret += "%s (%d) " % (MoveItemActioner.resultStr(key), results[key])
      count += 1
    ret += "Total (%d)" % count
    return ret

  def performActions(self, items):
    results = {}
    utils.verifyType(items, list)
    count = len(items)
    for i in range(count):
      item = items[i]
      res = self.performAction(item[0], item[1])
      if not results.has_key(res):
        results[res] = 0  
      results[res] += 1
      if self.percentageCompleteCallback_:
        prog = 100 * (i + 1) / count
        self.percentageCompleteCallback_(prog)
      if self.messageCallback_:
        longText = "%s -> %s" % (item[0], item[1]) 
        shortText = "%s -> %s" % (fileHelper.FileHelper.basename(item[0]), fileHelper.FileHelper.basename(item[1]))
        level = logModel.LogLevel.INFO
        if res <> MoveItemActioner.SUCCESS:
          level = logModel.LogLevel.ERROR
        self.messageCallback_(logModel.LogItem(level, \
                                               MoveItemActioner.resultStr(res), \
                                               shortText, \
                                               longText))
    if self.messageCallback_:
      self.messageCallback_(logModel.LogItem(logModel.LogLevel.INFO, "Complete", self.summaryText(results)))      
    return results
  
  def performAction(self, source, dest):
    utils.verifyType(source, str)
    utils.verifyType(dest, str)
    #sanity checks
    if not fileHelper.FileHelper.fileExists(source):
      return MoveItemActioner.SOURCE_DOES_NOT_EXIST
    if not fileHelper.FileHelper.isValidFilename(dest):
      return MoveItemActioner.INVALID_FILENAME
    elif source == dest:
      return MoveItemActioner.SUCCESS
    elif fileHelper.FileHelper.fileExists(dest) and not self.canOverwrite_:
      return MoveItemActioner.COULD_NOT_OVERWRITE    

    if self.keepSource_:
      return self._copyFile(source, dest)
    else:
      return self._moveFile(source, dest)    
    return ret
  
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
    