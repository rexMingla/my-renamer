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
      