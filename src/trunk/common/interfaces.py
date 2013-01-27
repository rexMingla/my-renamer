#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: App level interfaces
# --------------------------------------------------------------------------------------------------------------------
import abc

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
  __metaclass__ = abc.ABCMeta
  
  def __init__(self):
    super(ActionInterface, self).__init__()
  
  @abc.abstractmethod
  def start_exploring(self):
    pass
  
  @abc.abstractmethod
  def stop_exploring(self):
    pass
  
  @abc.abstractmethod
  def start_actioning(self):
    pass
  
  @abc.abstractmethod
  def stop_actioning(self):
    pass
  
  @abc.abstractmethod
  def get_config(self):
    pass
  
  @abc.abstractmethod
  def set_config(self, data):
    pass
  
# --------------------------------------------------------------------------------------------------------------------
class ActionWidgetInterface(QtGui.QWidget):
  def __init__(self, config_name, parent=None):
    super(ActionWidgetInterface, self).__init__(parent)
    self.config_name = config_name

ActionInterface.register(ActionWidgetInterface)