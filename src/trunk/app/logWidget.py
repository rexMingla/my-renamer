#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: The input widget and settings
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui
from PyQt4 import uic

from common import logModel
from common import utils

# --------------------------------------------------------------------------------------------------------------------
class LogWidget(QtGui.QWidget):
  """ Widget allowing for the configuration of output """
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui = uic.loadUi("ui/ui_LogWidget.ui", self)
    self._ui.clearButton.clicked.connect(self._clearLog)
    self._ui.clearButton.setEnabled(True)

    self._model = logModel.LogModel(self)
    self._ui.logView.setModel(self._model)
    self._ui.logView.horizontalHeader().setResizeMode(logModel.LogColumns.COL_ACTION, QtGui.QHeaderView.Interactive)
    self._ui.logView.horizontalHeader().resizeSection(logModel.LogColumns.COL_ACTION, 75)
    self._ui.logView.horizontalHeader().setResizeMode(logModel.LogColumns.COL_MESSAGE, QtGui.QHeaderView.Interactive)
    self._ui.logView.horizontalHeader().setStretchLastSection(True)
    
    self._isUpdating = False
    
  def onRename(self):
    if self._ui.autoClearCheckBox.isChecked():
      self._clearLog()
    
  def appendMessage(self, item):
    utils.verifyType(item, logModel.LogItem)
    self._model.addItem(item)
    
  def _clearLog(self):
    self._ui._model.clearItems()
    
  def setConfig(self, data):
    """ Update from settings """
    self._ui.autoClearCheckBox.setChecked(data.get("autoClear", False))
  
  def getConfig(self):
    return {"autoClear" : self._ui.autoClearCheckBox.isChecked()}
    
