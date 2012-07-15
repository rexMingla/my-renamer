#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Website:             http://code.google.com/p/dps-x509/
# Purpose of document: Log related classes
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui
import logging

import utils

# --------------------------------------------------------------------------------------------------------------------
class LogStyledDelegate(QtGui.QStyledItemDelegate):
  """ Display error message in the log in a noticable fashion. """
  def paint(self, painter, option, index):
    level, isOk = index.model().data(index, LogModel.LOG_LEVEL_ROLE).toInt()
    utils.verify(isOk, "Cast to int ok")
    if level >= LogLevel.ERROR:
      text = index.model().data(index, QtCore.Qt.DisplayRole).toString()
      painter.save()
      painter.setPen(QtCore.Qt.red)
      painter.setBrush(QtCore.Qt.blue)
      painter.setBackground(QtCore.Qt.green)
      painter.drawText(option.rect, QtCore.Qt.AlignLeft, text)
      painter.restore()    
    else:
      QtGui.QStyledItemDelegate.paint(self, painter, option, index)

# --------------------------------------------------------------------------------------------------------------------
class LogLevel:
  """ Log levels copied from logging. """
  CRITICAL = 50
  FATAL = CRITICAL
  ERROR = 40
  WARNING = 30
  WARN = WARNING
  INFO = 20
  DEBUG = 10
  NOTSET = 0

# --------------------------------------------------------------------------------------------------------------------
class LogColumns:
  """ Columns used in log model. """
  #COL_LEVEL   = 0
  COL_ACTION  = 0
  COL_MESSAGE = 1
  NUM_COLS    = 2

# --------------------------------------------------------------------------------------------------------------------
class LogItem:
  """ Information contained in a log entry. """
  def __init__(self, logLevel, action, shortMessage, longMessage=""):
    utils.verifyType(logLevel, int)
    utils.verifyType(action, str)
    utils.verifyType(shortMessage, str)
    utils.verifyType(longMessage, str)
    self.logLevel = logLevel
    self.action = action
    self.shortMessage = shortMessage
    self.longMessage = longMessage or shortMessage

# --------------------------------------------------------------------------------------------------------------------
class LogModel(QtCore.QAbstractTableModel):
  """ Collection of LogItems wrapped in a QAbstractTableModel """
  LOG_LEVEL_ROLE = QtCore.Qt.UserRole + 1
  
  def __init__(self, parent):
    super(QtCore.QAbstractTableModel, self).__init__(parent)
    self.items_ = []
      
  def rowCount(self, parent):
    return len(self.items_)

  def columnCount(self, parent):
    return LogColumns.NUM_COLS
  
  def data(self, index, role):
    if not index.isValid():
      return None
    
    if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole, LogModel.LOG_LEVEL_ROLE):
      return None
    
    item = self.items_[index.row()]
    if role == LogModel.LOG_LEVEL_ROLE:
      return QtCore.QVariant(item.logLevel)
    #if index.column() == LogColumns.COL_LEVEL: 
    #  return logging.getLevelName(item.logLevel)
    if index.column() == LogColumns.COL_ACTION:
      return QtCore.QVariant(item.action)
    elif index.column() == LogColumns.COL_MESSAGE: 
      if role == QtCore.Qt.DisplayRole:
        return QtCore.QVariant(item.shortMessage)
      else:
        return QtCore.QVariant(item.longMessage)
    else: 
      return None  
  
  def headerData(self, section, orientation, role):
    if role <> QtCore.Qt.DisplayRole or orientation == QtCore.Qt.Vertical:
      return None
    
    #if section == LogColumns.COL_LEVEL: 
    #  return "Type"
    if section == LogColumns.COL_ACTION:
      return QtCore.QVariant("Action")
    elif section == LogColumns.COL_MESSAGE: 
      return QtCore.QVariant("Message")
  
  def addItem(self, item):
    utils.verifyType(item, LogItem)
    count = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), count, count)
    self.items_.append(item)
    self.endInsertRows()
    
  def clearItems(self):
    count = self.rowCount(QtCore.QModelIndex())
    if count:
      self.beginRemoveRows(QtCore.QModelIndex(), 0, count-1)
      self.items_ = []
      self.endRemoveRows()
  
  