#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import re

import utils

# --------------------------------------------------------------------------------------------------------------------
class FileExtensions:
  ALL_FILES = ".*"
  
  def __init__(self, extensions):
    utils.verifyType(extensions, list)
    self.setExtensionsFromList(extensions)
  
  @staticmethod
  def delimiter():
    return " "

  def setExtensionsFromString(self, s):
    utils.verifyType(s, str)
    self.setExtensionsFromList(s.split(FileExtensions.delimiter()))

  def setExtensionsFromList(self, l):
    utils.verifyType(l, list)
    isAll = not l
    sanitized = []
    for item in l:
      if item in ["*", "*.*", ".*"]:
        isAll = True
        break
      else:
        #leave in format of .ext
        if item.startswith("*"):
          sanitized.append(item[1:])
        elif not item.startswith("."):
          sanitized.append(".%s" % item)
        else:
          sanitized.append(item)
    if isAll:
      self._extensions_ = [FileExtensions.ALL_FILES] #make a copy
    else:
      self._extensions_ = sanitized
  
  def extensionString(self):
    return FileExtensions.delimiter().join(self._extensions_)
  
  def escapedFileTypeString(self):
    ret = ""
    if self == ALL_FILE_EXTENSIONS:
      ret = "(?:\\..*)"
    else:
      temp = []
      for item in self._extensions_:
        temp.append(re.escape(item))
        ret = "(?:%s)" % "|".join(temp)
    return ret
  
  def filterFiles(self, files):
    utils.verifyType(files, list)
    ret = []
    if self == ALL_FILE_EXTENSIONS:
      ret = files
    else:
      for f in files:
        for ext in self._extensions_:
          if f.endswith(ext):
            ret.append(f)
            break
    return ret
  
  def __eq__(self, other):
    return utils.listCompare(self._extensions_, other._extensions_)

ALL_FILE_EXTENSIONS      = FileExtensions([FileExtensions.ALL_FILES])
DEFAULT_VIDEO_EXTENSIONS = FileExtensions([".avi", ".mov"])