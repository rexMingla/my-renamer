#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import os
import re
import shutil
import string
import unicodedata

import logModel
import utils

# --------------------------------------------------------------------------------------------------------------------
class FileHelper:
  _VALID_BASENAME_CHARACTERS = "%s%s%s" % (string.ascii_letters, \
                                           string.digits, \
                                           " !#$%&'()*+,-./;=@[\]^_`{}~") # string.punctuation without \/:?"<>| 
  
  @staticmethod
  def isFile(f):
    utils.verifyType(f, str)
    return os.path.isfile(f)

  @staticmethod
  def isDir(d):
    utils.verifyType(d, str)
    return os.path.isdir(d)

  @staticmethod
  def dirname(f):
    utils.verifyType(f, str)
    return os.path.dirname(f)
  
  @staticmethod
  def basename(f):
    utils.verifyType(f, str)
    return os.path.basename(f)
  
  @staticmethod
  def splitDrive(p):
    utils.verifyType(p, str)
    return os.path.splitdrive(p)
  
  @staticmethod
  def joinPath(d, f):
    utils.verifyType(d, str)
    utils.verifyType(f, str)
    ret = os.path.join(d, f)
    return ret

  @staticmethod
  def dirExists(d):
    utils.verifyType(d, str)
    return os.path.exists(d) and FileHelper.isDir(d)
  
  @staticmethod
  def createDir(d):
    utils.verifyType(d, str)
    ret = True
    if not FileHelper.dirExists(d):
      try:
        os.makedirs(d)
      except:
        ret = False
    return ret
  
  @staticmethod
  def removeDir(d):
    utils.verifyType(d, str)
    ret = True
    if FileHelper.dirExists(d):
      try:
        shutil.rmtree(d)
      except shutil.Error:
        ret = False
    return ret

  @staticmethod
  def fileExists(f):
    utils.verifyType(f, str)
    return os.path.exists(f) and FileHelper.isFile(f)
 
  @staticmethod
  def isValidFilename(f):
    utils.verifyType(f, str)
    drive, tail = FileHelper.splitDrive(f)    
    validFilenameCharsRegex = "^([%s])+$" % re.escape(FileHelper._VALID_BASENAME_CHARACTERS)
    return not not re.match(validFilenameCharsRegex, tail)
    
  @staticmethod
  def sanitizeFilename(f, replaceChar="_"):
    utils.verifyType(f, str)
    utils.verifyType(replaceChar, str)
    ret = f
    if not FileHelper.isValidFilename(f):
      drive, tail = FileHelper.splitDrive(f)
      invalidFilenameCharsRegex = "[^%s]" % re.escape(FileHelper._VALID_BASENAME_CHARACTERS)
      tail = re.sub(invalidFilenameCharsRegex, replaceChar, tail)
      ret = FileHelper.joinPath(drive, tail)
    return ret
  
  @staticmethod
  def removeFile(f):
    utils.verifyType(f, str)
    ret = True
    if FileHelper.fileExists(f):
      try:
        os.remove(f)
      except:
        ret = False
    return ret

  @staticmethod
  def moveFile(source, dest):
    utils.verifyType(source, str)
    utils.verifyType(dest, str)
    ret = False
    if FileHelper.fileExists(source):
      destFolder = FileHelper.dirname(dest)
      if not destFolder or FileHelper.createDir(destFolder):
        try:
          shutil.move(source, dest)
          ret = True
        except:
          pass
    return ret
  
  @staticmethod
  def copyFile(source, dest):
    utils.verifyType(source, str)
    utils.verifyType(dest, str)
    ret = False
    if FileHelper.fileExists(source):
      destFolder = FileHelper.dirname(dest)
      if not destFolder or FileHelper.createDir(destFolder):
        try:
          shutil.copy2(source, dest)
          ret = True
        except:
          pass
    return ret
  
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
        longText = "%s: %s -> %s" % (MoveItemActioner.resultStr(res), item[0], item[1]) 
        shortText = "%s: %s -> %s" % (MoveItemActioner.resultStr(res), \
                                     FileHelper.basename(item[0]),
                                     FileHelper.basename(item[1])) 
        self.messageCallback_(logModel.LogItem(logModel.LogLevel.CRITICAL, shortText, longText))
    return results
  
  def performAction(self, source, dest):
    utils.verifyType(source, str)
    utils.verifyType(dest, str)
    #sanity checks
    if not FileHelper.fileExists(source):
      return MoveItemActioner.SOURCE_DOES_NOT_EXIST
    if not FileHelper.isValidFilename(dest):
      return MoveItemActioner.INVALID_FILENAME
    elif source == dest:
      return MoveItemActioner.SUCCESS
    elif FileHelper.fileExists(dest) and not self.canOverwrite_:
      return MoveItemActioner.COULD_NOT_OVERWRITE    

    if self.keepSource_:
      return self._copyFile(source, dest)
    else:
      return self._moveFile(source, dest)    
    return ret
  
  def _moveFile(self, source, dest):
    utils.verifyType(source, str)
    utils.verifyType(dest, str)
    if FileHelper.moveFile(source, dest):
      return MoveItemActioner.SUCCESS
    else:
      return MoveItemActioner.FAILED
    
  def _copyFile(self, source, dest):
    utils.verifyType(source, str)
    utils.verifyType(dest, str)
    if FileHelper.copyFile(source, dest):
      return MoveItemActioner.SUCCESS
    else:
      return MoveItemActioner.FAILED
    