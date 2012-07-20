#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Class associated with all things FileExtensions
# --------------------------------------------------------------------------------------------------------------------
import utils

# --------------------------------------------------------------------------------------------------------------------
class FileExtensions:
  """ 
  Handling of file extensions. Extensions can be loaded from a string or a list. 
  Strings will be FileExtensions.delimiter separated before being cleaned as follows (using mpg as the example extension):
  *.mpg -> .mpg
  .mpg  -> .mpg
  mpg   -> .mpg
  Additionally, an extension list that contains "", "*", "*.*", ".*" will be resolved to FileExtensions.ALL_FILES
  for the entire list.
  """
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
      if item in ["", "*", "*.*", ".*"]:
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
  
  def filterFiles(self, files):
    """ Return list of files matching extension filter """
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
DEFAULT_VIDEO_EXTENSIONS = FileExtensions([".avi", ".divx", ".mkv", ".mpg", ".mp4", ".wmv"])