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
  
  def start_exploring(self):
    raise NotImplementedError("ActionInterface.start_exploring not implemented")
  
  def stop_exploring(self):
    raise NotImplementedError("ActionInterface.stop_exploring not implemented")
  
  def start_actioning(self):
    raise NotImplementedError("ActionInterface.start_actioning not implemented")
  
  def stop_actioning(self):
    raise NotImplementedError("ActionInterface.stop_actioning not implemented")
  
  def get_config(self):
    raise NotImplementedError("ActionInterface.get_config not implemented")
  
  def set_config(self, data):
    raise NotImplementedError("ActionInterface.set_config not implemented")
  
# --------------------------------------------------------------------------------------------------------------------
class ActionWidgetInterface(QtGui.QWidget):
  def __init__(self, config_name, parent=None):
    super(ActionWidgetInterface, self).__init__(parent)
    self.config_name = config_name
