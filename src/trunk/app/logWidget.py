#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore, QtGui, uic

import serializer
import utils

# --------------------------------------------------------------------------------------------------------------------
class LogWidget(QtGui.QWidget):
  """"""
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_LogWidget.ui", self)
    self._ui_.clearButton_.clicked.connect(self._clearLog)
    self._ui_.clearButton_.setEnabled(True)
    
  def _clearLog(self):
    self._ui_.logText_.clear()
    
  def appendMessage(self, message):
    utils.verifyType(message, str)
    text = self._ui_.logText_.toPlainText()
    text += message + "\n"
    self._ui_.logText_.setText(text)
    
