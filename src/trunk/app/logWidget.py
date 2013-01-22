#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: The input widget and settings
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from common import utils

# --------------------------------------------------------------------------------------------------------------------
class LogWidget(QtGui.QWidget):
  """ Widget to display log messages to the user """
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    uic.loadUi("ui/ui_LogWidget.ui", self)
    self.clearButton.clicked.connect(self._clearLog)
    self.clearButton.setIcon(QtGui.QIcon("img/clear.png"))    
    self.clearButton.setEnabled(True)

    self._model = LogModel(self)
    self.logView.setModel(self._model)
    self.logView.horizontalHeader().setResizeMode(LogColumns.COL_ACTION, QtGui.QHeaderView.Interactive)
    self.logView.horizontalHeader().resizeSection(LogColumns.COL_ACTION, 75)
    self.logView.horizontalHeader().setResizeMode(LogColumns.COL_MESSAGE, QtGui.QHeaderView.Interactive)
    self.logView.horizontalHeader().setStretchLastSection(True)
    
    self._isUpdating = False
    
  def onRename(self):
    if self.autoClearCheckBox.isChecked():
      self._clearLog()
    
  def appendMessage(self, item):
    #utils.verifyType(item, LogItem)
    self._model.addItem(item)
    
  def _clearLog(self):
    self._model.clearItems()
    
  def setConfig(self, data):
    """ Update from settings """
    self.autoClearCheckBox.setChecked(data.get("autoClear", False))
  
  def getConfig(self):
    return {"autoClear" : self.autoClearCheckBox.isChecked()}

# --------------------------------------------------------------------------------------------------------------------
class LogColumns:
  """ Columns used in log model. """
  #COL_LEVEL   = 0
  COL_ACTION  = 0
  COL_MESSAGE = 1
  NUM_COLS    = 2

# --------------------------------------------------------------------------------------------------------------------
class LogModel(QtCore.QAbstractTableModel):
  """ Collection of LogItems wrapped in a QAbstractTableModel """
  LOG_LEVEL_ROLE = QtCore.Qt.UserRole + 1
  
  def __init__(self, parent):
    super(QtCore.QAbstractTableModel, self).__init__(parent)
    self.items = []
      
  def rowCount(self, parent):
    return len(self.items)

  def columnCount(self, parent):
    return LogColumns.NUM_COLS
  
  def data(self, index, role):
    if not index.isValid():
      return None
    
    if role not in (QtCore.Qt.ForegroundRole, QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole):
      return None
    
    item = self.items[index.row()]
    if role == QtCore.Qt.ForegroundRole and item.logLevel >= utils.LogLevel.ERROR:
      return QtGui.QBrush(QtCore.Qt.red)      
    elif role == LogModel.LOG_LEVEL_ROLE:
      return item.logLevel
    elif index.column() == LogColumns.COL_ACTION:
      return item.action
    elif index.column() == LogColumns.COL_MESSAGE: 
      if role == QtCore.Qt.DisplayRole:
        return item.shortMessage
      else:
        return item.longMessage
    else: 
      return None  
  
  def headerData(self, section, orientation, role):
    if role != QtCore.Qt.DisplayRole or orientation == QtCore.Qt.Vertical:
      return None
    
    #if section == LogColumns.COL_LEVEL: 
    #  return "Type"
    if section == LogColumns.COL_ACTION:
      return "Action"
    elif section == LogColumns.COL_MESSAGE: 
      return "Message"
    
  def addItem(self, item):
    #utils.verifyType(item, LogItem)
    utils.log(item.logLevel, msg=item.shortMessage, longMsg=item.longMessage, title=item.action)
    count = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), count, count)
    self.items.append(item)
    self.endInsertRows()
    
  def clearItems(self):
    count = self.rowCount(QtCore.QModelIndex())
    if count:
      self.beginResetModel()
      self.items = []
      self.endResetModel()
  
  