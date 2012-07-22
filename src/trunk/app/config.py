#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Config singleton
# --------------------------------------------------------------------------------------------------------------------
import jsonpickle
jsonpickle.set_encoder_options("simplejson", indent=2)

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
    f = open(filename, "w")
    f.write(jsonpickle.encode(_CONFIG))
    f.close()