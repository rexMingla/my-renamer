#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Serialization of object state to/from file
# --------------------------------------------------------------------------------------------------------------------
""" 
sample serialization:
>>> config = ConfigManager()
>>> config.setData("key", "value")
>>> config.saveConfig("temp.txt")

sample deserialization:
>>> config.loadConfig("temp.txt")
>>> config.getData("key")
value
"""
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
  """ manages serialization to / from file using json pickle """

  def __init__(self):
    """ """
    super(ConfigManager, self).__init__()
    self._data = {}

  def getData(self, key, default=""):
    """ retrieve value from data. assumes loadConfig() has already been performed """
    return self._data.get(key, default)

  def setData(self, key, value):
    """ sets data for key """ 
    self._data[key] = value

  def loadConfig(self, filename):
    """ deserializes the contents of the file with jsonpickle """
    self._data = {}
    if file_helper.FileHelper.fileExists(filename):
      file_obj = open(filename, "r")
      try:
        self._data = jsonpickle.decode(file_obj.read())
      except (ValueError, TypeError, IndexError, KeyError) as ex:
        utils.logWarning("loadConfig error: {}".format(ex))
    if not isinstance(self._data, dict):
      self._data = {}

  def saveConfig(self, filename):
    """ 
    serializes the data using jsonpickle. the data is first written to a temporary file (with .bak extension) and then
    swapped with the real file on success. 
    """
    tmp_file = "{}.bak".format(filename)
    try:
      #write a temp file and swap on success
      file_obj = open(tmp_file, "w")
      file_obj.write(jsonpickle.encode(self._data))
      file_obj.close()
      if os.path.exists(filename):
        os.remove(filename)
      os.rename(tmp_file, filename)
    except Exception as ex: #json pickle catches Exception so I guess we have to too
      message_box = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                             "An error occured", "Unable to save to settings file:\n{}".format(filename))
      error = ["Error:\n{}\n\n".format(str(ex)), "Exception:\n", "".join(traceback.format_exception(*sys.exc_info()))]
      message_box.setDetailedText("".join(error))
      message_box.exec_()
      #raise #for debugging
