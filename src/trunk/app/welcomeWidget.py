#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Mode selection widget
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui
from PyQt4 import uic

import interfaces
from common import utils

# --------------------------------------------------------------------------------------------------------------------
class WelcomeWidget(QtGui.QDialog):
  """ First prompt seen by the user, to select movie / tv mode. """
  def __init__(self, mode, parent=None):
    utils.verify(mode in interfaces.VALID_MODES, "mode must be valid")
    super(WelcomeWidget, self).__init__(parent)
    self._ui = uic.loadUi("ui/ui_Welcome.ui", self)
    self.setWindowModality(True)
    
    if mode == interfaces.Mode.MOVIE_MODE:
      self._ui.movieRadio.setChecked(True)
    else:
      self._ui.tvRadio.setChecked(True)
  
  def mode(self):
    return interfaces.Mode.MOVIE_MODE if self._ui.movieRadio.isChecked() else interfaces.Mode.TV_MODE
  
  def isAutoStart(self):
    return self._ui.autoStartCheckBox.isChecked()
  