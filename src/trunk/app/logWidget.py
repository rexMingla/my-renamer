#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: The input widget and settings
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore, QtGui, uic

from common import logModel, logStyledDelegate, serializer, utils

# --------------------------------------------------------------------------------------------------------------------
class LogSettings():
  """ Settings serialized on application start up/shut down."""
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
  """ Widget allowing for the configuration of output """
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
    
    self._model_ = logModel.LogModel(self)
    self._ui_.logView_.setModel(self._model_)
    self._ui_.logView_.setItemDelegate(logStyledDelegate.LogStyledDelegate())
    self._ui_.logView_.horizontalHeader().setResizeMode(logModel.LogColumns.COL_ACTION, QtGui.QHeaderView.Fixed)
    self._ui_.logView_.horizontalHeader().resizeSection(logModel.LogColumns.COL_ACTION, 75);
    self._ui_.logView_.horizontalHeader().setResizeMode(logModel.LogColumns.COL_MESSAGE, QtGui.QHeaderView.Stretch)
    self._ui_.logView_.horizontalHeader().setStretchLastSection(True)
    
    self._isUpdating = False
    
  def onRename(self):
    if self.logSettings_.autoClear_:
      self._clearLog()
    
  def appendMessage(self, item):
    utils.verifyType(item, logModel.LogItem)
    self._model_.addItem(item)
    
  def _clearLog(self):
    self._ui_._model_.clearItems()
    
  def _onStateChanged(self):
    """ Update from settings """
    self._isUpdating = False
    self.logSettings_.fromDictionary(self.dataItem_.data_)
    self._ui_.autoClearCheckBox_.setChecked(self.logSettings_.autoClear_)
    self._isUpdating  = False
  
  def _readbackGUI(self):
    if not self._isUpdating:
      self.logSettings_.autoClear_ = self._ui_.autoClearCheckBox_.isChecked()
      self.dataItem_.setData(self.logSettings_.toDictionary())      
    
