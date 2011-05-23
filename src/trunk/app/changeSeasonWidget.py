#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Allow the user to select an season for a given folder
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore, QtGui, uic

from common import utils

# --------------------------------------------------------------------------------------------------------------------
class ChangeSeasonWidget(QtGui.QDialog):
  """
  The widget allows the user to select an show name and season number for a given folder containing files.
  Unfortunately these is currently no way for the user to preview whether the show name and seaon number 
  are resovled by the web service.
  """
  def __init__(self, parent=None):
    super(QtGui.QDialog, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_ChangeSeason.ui", self)
    self.setWindowModality(True)
    
  def showEvent(self, event):
    """ protected Qt function """
    self.setMaximumHeight(self.sizeHint().height())
    self.setMinimumHeight(self.sizeHint().height())
  
  def setData(self, folder, seasonName, seasonNum):
    """ Fill the dialog with the data prior to being shown """
    utils.verifyType(folder, str)
    utils.verifyType(seasonName, str)
    utils.verifyType(seasonNum, int)
    self._ui_.folderLabel_.setText(folder)
    self._ui_.seasonEdit_.setText(seasonName)
    self._ui_.seasonSpin_.setValue(seasonNum)
    
  def showName(self):
    """ Returns the show name from the dialog. """
    return self._ui_.seasonEdit_.text()

  def seasonNumber(self):
    """ Returns the currently selected season number from the dialog. """
    return self._ui_.seasonSpin_.value()

  