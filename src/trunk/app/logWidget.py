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
class LogSettings():
  """"""
  def __init__(self):
    self.autoClear_ = True

  def toDictionary(self):
    return {"autoClear":utils.toString(self.autoClear_)}

  def fromDictionary(self, dic):
    utils.verifyType(dic, dict)
    if dic.has_key("autoClear") and isinstance(dic["autoClear"], str):  
      self.autoClear_ = utils.strToBool(dic["autoClear"])

# --------------------------------------------------------------------------------------------------------------------
class LogWidget(QtGui.QWidget):
  """"""
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_LogWidget.ui", self)
    self._ui_.clearButton_.clicked.connect(self._clearLog)
    self._ui_.clearButton_.setEnabled(True)

    self._ui_.autoClearCheckBox_.toggled.connect(self._readbackGUI)
    
    self.logSettings_ = LogSettings()
    self.dataItem_ = serializer.DataItem(self.logSettings_.toDictionary())
    self.dataItem_.onChangedSignal_.connect(self._onStateChanged)
    self._onStateChanged()
    
    self._isUpdating = False
    
  def onRename(self):
    if self.logSettings_.autoClear_:
      self._clearLog()
    
  def appendMessage(self, message):
    utils.verifyType(message, str)
    text = self._ui_.logText_.toPlainText()
    text += message + "\n"
    self._ui_.logText_.setText(text)
    
  def _clearLog(self):
    self._ui_.logText_.clear()
    
  def _onStateChanged(self):
    self._isUpdating = False
    self.logSettings_.fromDictionary(self.dataItem_.data_)
    self._ui_.autoClearCheckBox_.setChecked(self.logSettings_.autoClear_)
    self._isUpdating  = False
  
  def _readbackGUI(self):
    if not self._isUpdating:
      self.logSettings_.autoClear_ = self._ui_.autoClearCheckBox_.isChecked()
      self.dataItem_.setData(self.logSettings_.toDictionary())      
    
