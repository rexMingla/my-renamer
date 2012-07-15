#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: The input widget and settings
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore, QtGui, uic

from common import logModel, logStyledDelegate, utils

# --------------------------------------------------------------------------------------------------------------------
class LogWidget(QtGui.QWidget):
  """ Widget allowing for the configuration of output """
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_LogWidget.ui", self)
    self._ui_.clearButton_.clicked.connect(self._clearLog)
    self._ui_.clearButton_.setEnabled(True)

    self._model_ = logModel.LogModel(self)
    self._ui_.logView_.setModel(self._model_)
    self._ui_.logView_.setItemDelegate(logStyledDelegate.LogStyledDelegate())
    self._ui_.logView_.horizontalHeader().setResizeMode(logModel.LogColumns.COL_ACTION, QtGui.QHeaderView.Fixed)
    self._ui_.logView_.horizontalHeader().resizeSection(logModel.LogColumns.COL_ACTION, 75);
    self._ui_.logView_.horizontalHeader().setResizeMode(logModel.LogColumns.COL_MESSAGE, QtGui.QHeaderView.Stretch)
    self._ui_.logView_.horizontalHeader().setStretchLastSection(True)
    
    self._isUpdating = False
    
  def onRename(self):
    if self._ui_.autoClearCheckBox_.isChecked():
      self._clearLog()
    
  def appendMessage(self, item):
    utils.verifyType(item, logModel.LogItem)
    self._model_.addItem(item)
    
  def _clearLog(self):
    self._ui_._model_.clearItems()
    
  def setConfig(self, data):
    """ Update from settings """
    self._ui_.autoClearCheckBox_.setChecked(data.get("autoClear", False))
  
  def getConfig(self):
    return {"autoClear" : self._ui_.autoClearCheckBox_.isChecked()}
    
