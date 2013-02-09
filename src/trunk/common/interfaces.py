#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: App level interfaces
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui

MOVIE_MODE = "movie"
TV_MODE = "tv"

VALID_MODES = (MOVIE_MODE, TV_MODE)

# --------------------------------------------------------------------------------------------------------------------
class WorkBenchActions:
  """ not used at the moment """
  OPEN_LOCATION = "Open location"
  LAUNCH = "Launch"
  DELETE = "Delete"
  EDIT_MOVIE = "Edit Movie"
  EDIT_SEASON = "Edit Season"
  EDIT_EPISODE = "Edit Episode"

# --------------------------------------------------------------------------------------------------------------------
class ActionInterface(object):
  """ all the input, output and work bench widgets must implement these interfaces """
  def __init__(self):
    super(ActionInterface, self).__init__()

  def startExploring(self):
    raise NotImplementedError("ActionInterface.startExploring not implemented")

  def stopExploring(self):
    raise NotImplementedError("ActionInterface.stopExploring not implemented")

  def startActioning(self):
    raise NotImplementedError("ActionInterface.startActioning not implemented")

  def stopActioning(self):
    raise NotImplementedError("ActionInterface.stopActioning not implemented")

  def getConfig(self):
    raise NotImplementedError("ActionInterface.getConfig not implemented")

  def setConfig(self, data):
    raise NotImplementedError("ActionInterface.setConfig not implemented")

# --------------------------------------------------------------------------------------------------------------------
class ActionWidgetInterface(QtGui.QWidget):
  def __init__(self, config_name, parent=None):
    super(ActionWidgetInterface, self).__init__(parent)
    self.config_name = config_name
