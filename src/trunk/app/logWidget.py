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
    uic.loadUi("ui/ui_LogWidget.ui", self)
    self.clearButton.clicked.connect(self._clearLog)
    self.clearButton.setEnabled(True)

    self._model = logModel.LogModel(self)
    self.logView.setModel(self._model)
    self.logView.horizontalHeader().setResizeMode(logModel.LogColumns.COL_ACTION, QtGui.QHeaderView.Interactive)
    self.logView.horizontalHeader().resizeSection(logModel.LogColumns.COL_ACTION, 75)
    self.logView.horizontalHeader().setResizeMode(logModel.LogColumns.COL_MESSAGE, QtGui.QHeaderView.Interactive)
    self.logView.horizontalHeader().setStretchLastSection(True)
    
    self._isUpdating = False
    
  def onRename(self):
    if self.autoClearCheckBox.isChecked():
      self._clearLog()
    
  def appendMessage(self, item):
    utils.verifyType(item, logModel.LogItem)
    self._model.addItem(item)
    
  def _clearLog(self):
    self._model.clearItems()
    
  def setConfig(self, data):
    """ Update from settings """
    self.autoClearCheckBox.setChecked(data.get("autoClear", False))
  
  def getConfig(self):
    return {"autoClear" : self.autoClearCheckBox.isChecked()}
    
