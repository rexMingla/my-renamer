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

from common import file_helper
from common import utils

jsonpickle.set_encoder_options("simplejson", indent=2)

# --------------------------------------------------------------------------------------------------------------------
class ConfigManager(object):
  """ serializes / deserializes jsonpickle to / from file """

  def __init__(self):
    self._data = {}
    
  def getData(self, key, default=""):
    return self._data.get(key, default)
  
  def setData(self, key, value):
    self._data[key] = value
    
  def loadConfig(self, filename):
    self._data = {}
    if file_helper.FileHelper.fileExists(filename):
      f = open(filename, "r")
      try:
        self._data = jsonpickle.decode(f.read())
      except (ValueError, TypeError, IndexError, KeyError) as e:
        utils.logWarning("loadConfig error: {}".format(e))
    if not isinstance(self._data, dict):
      self._data = {}
  
  def saveConfig(self, filename):
    tmpFile = "{}.bak".format(filename)
    try:
      #write a temp file and swap on success
      f = open(tmpFile, "w")
      f.write(jsonpickle.encode(self._data))
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
