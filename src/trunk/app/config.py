#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Config singleton
# --------------------------------------------------------------------------------------------------------------------
import os
import jsonpickle
jsonpickle.set_encoder_options("simplejson", indent=2)

from PyQt4 import QtCore
from PyQt4 import QtGui

from common import fileHelper
from common import utils

# --------------------------------------------------------------------------------------------------------------------
#globals
_CONFIG = {} #filthy static

USE_SOURCE_DIRECTORY = ""

# --------------------------------------------------------------------------------------------------------------------
class ConfigManager(object):
  @staticmethod
  def getData(key, default=""):
    global _CONFIG
    return _CONFIG.get(key, default)
  
  @staticmethod
  def setData(key, value):
    global _CONFIG
    _CONFIG[key] = value

  @staticmethod    
  def loadConfig(filename):
    global _CONFIG    
    _CONFIG = {}
    if fileHelper.FileHelper.fileExists(filename):
      f = open(filename, "r")
      try:
        _CONFIG = jsonpickle.decode(f.read())
      except (ValueError, TypeError, KeyError) as e:
        utils.logWarning("loadConfig error: {}".format(e))
    if not isinstance(_CONFIG, dict):
      _CONFIG = {}
  
  @staticmethod
  def saveConfig(filename):
    global _CONFIG
    tmpFile = "{}.bak".format(filename)
    try:
      f = open(tmpFile, "w")
      f.write(jsonpickle.encode(_CONFIG))
      f.close()
      if os.path.exists(filename):
        os.remove(filename)
      os.rename(tmpFile, filename)
    except Exception as e: #json catches Exception so I guess we have to too
      mb = QtGui.QMessageBox(QtGui.QMessageBox.Information, 
                             "An error occured", "Unable to save to settings file:\n{}".format(filename))
      mb.setDetailedText("Error:\n{}".format(str(e)))
      mb.exec_()
