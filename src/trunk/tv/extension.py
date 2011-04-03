#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import sys 
import os
sys.path.insert(0, os.path.abspath(__file__+"/../../"))
import re

import app

class FileExtensions:
  _extensions_ = []
  
  @staticmethod
  def delimiter():
    return " "

  @staticmethod
  def setExtensionsFromString(s):
    app.utils.verifyType(s, str)
    setExtensionsFromList(s.split(delimiter()))

  @staticmethod
  def setExtensionsFromList(l):
    app.utils.verifyType(l, list)
    isAll = False
    for item in l:
      if item in ["*", "*.*", ".*"]:
        isAll = True
        break
    if isAll:
      FileExtensions._extensions_ = [".*"]
    else:
      FileExtensions._extensions_ = l
  
  @staticmethod
  def extensionString():
    return delimiter().join(_extensions_)
  
  @staticmethod
  def escapedFileTypeString():
    ret = ""
    if FileExtensions._extensions_ == [".*"]:
      ret = "(?:\\..*)"
    else:
      temp = []
      for item in FileExtensions._extensions_:
        temp.append(re.escape(item))
        ret = "(?:%s)" % "|".join(temp)
    return ret
      