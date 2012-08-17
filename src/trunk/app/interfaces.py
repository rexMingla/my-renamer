#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: App level interfaces
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui

from common import extension
from common import fileHelper
from common import logModel
from common import moveItemActioner
from common import utils

import config

# --------------------------------------------------------------------------------------------------------------------
class Mode:
  MOVIE_MODE = "movie"
  TV_MODE = "tv"
  
VALID_MODES = (Mode.MOVIE_MODE, Mode.TV_MODE)

# --------------------------------------------------------------------------------------------------------------------
class LoadWidgetInterface(QtGui.QWidget):
  
  def __init__(self, configName, parent=None):
    super(LoadWidgetInterface, self).__init__()
    self.configName = configName
  
  def startExploring(self):
    raise NotImplementedError("LoadInterface.startExploring")
  
  def stopExploring(self):
    raise NotImplementedError("LoadInterface.stopExploring")

  def startActioning(self):
    raise NotImplementedError("LoadInterface.startActioning")
  
  def stopActioning(self):
    raise NotImplementedError("LoadInterface.stopActioning")
  
  def getConfig(self, mode):
    raise NotImplementedError("LoadInterface.getConfig")
  
  def setConfig(self, mode):
    raise NotImplementedError("LoadInterface.setConfig")
