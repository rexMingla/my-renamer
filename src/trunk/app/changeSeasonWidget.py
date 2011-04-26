#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore, QtGui, uic

#from tv import episode, moveItem, outputFormat, season

import utils

# --------------------------------------------------------------------------------------------------------------------
class ChangeSeasonWidget(QtGui.QDialog):
  def __init__(self, parent=None):
    super(QtGui.QDialog, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_ChangeSeason.ui", self)
    self.setWindowModality(True)
    
  def showEvent(self, event):
    self.setMaximumHeight(self.sizeHint().height())
    self.setMinimumHeight(self.sizeHint().height())
  
  def setData(self, folder, seasonName, seasonNum):
    utils.verifyType(folder, str)
    utils.verifyType(seasonName, str)
    utils.verifyType(seasonNum, int)
    self._ui_.folderLabel_.setText(folder)
    self._ui_.seasonEdit_.setText(seasonName)
    self._ui_.seasonSpin_.setValue(seasonNum)
    
  def seasonName(self):
    return self._ui_.seasonEdit_.text()

  def seasonNumber(self):
    return self._ui_.seasonSpin_.value()

  