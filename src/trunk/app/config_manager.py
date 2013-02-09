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
      file_obj = open(filename, "r")
      try:
        self._data = jsonpickle.decode(file_obj.read())
      except (ValueError, TypeError, IndexError, KeyError) as ex:
        utils.logWarning("loadConfig error: {}".format(ex))
    if not isinstance(self._data, dict):
      self._data = {}

  def saveConfig(self, filename):
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
