#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Config singleton
# --------------------------------------------------------------------------------------------------------------------
import jsonpickle
import os
import sys
import traceback

from PyQt4 import QtGui

from common import fileHelper
from common import utils

jsonpickle.set_encoder_options("simplejson", indent=2)
USE_SOURCE_DIRECTORY = "" #TODO: why is this here?

# --------------------------------------------------------------------------------------------------------------------
class ConfigManager(object):
  _data = {}
    
  @classmethod
  def getData(cls, key, default=""):
    return cls._data.get(key, default)
  
  @classmethod
  def setData(cls, key, value):
    cls._data[key] = value

  @classmethod
  def loadConfig(cls, filename):
    cls._data = {}
    if fileHelper.FileHelper.fileExists(filename):
      f = open(filename, "r")
      try:
        cls._data = jsonpickle.decode(f.read())
      except (ValueError, TypeError, KeyError) as e:
        utils.logWarning("loadConfig error: {}".format(e))
    if not isinstance(cls._data, dict):
      cls._data = {}
  
  @classmethod
  def saveConfig(cls, filename):
    tmpFile = "{}.bak".format(filename)
    try:
      #write a temp file and swap on success
      f = open(tmpFile, "w")
      f.write(jsonpickle.encode(cls._data))
      f.close()
      if os.path.exists(filename):
        os.remove(filename)
      os.rename(tmpFile, filename)
    except Exception as e: #json catches Exception so I guess we have to too
      mb = QtGui.QMessageBox(QtGui.QMessageBox.Information, 
                             "An error occured", "Unable to save to settings file:\n{}".format(filename))
      errorText = ["Error:\n{}\n\n".format(str(e)),
                   "Exception:\n",
                   "".join(traceback.format_exception(*sys.exc_info()))]
      mb.setDetailedText("".join(errorText))
      mb.exec_()
      #raise #for debugging
