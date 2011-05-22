#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Website:             http://code.google.com/p/dps-x509/
# Purpose of document: All the generic functions that don't have a more appropriate home
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
import logging

import utils

# --------------------------------------------------------------------------------------------------------------------
class LogLevel:
  """ copied from logging for now """
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
  #COL_LEVEL   = 0
  COL_ACTION  = 0
  COL_MESSAGE = 1
  NUM_COLS    = 2

# --------------------------------------------------------------------------------------------------------------------
class LogItem:
  def __init__(self, logLevel, action, shortMessage, longMessage=""):
    utils.verifyType(logLevel, int)
    utils.verifyType(action, str)
    utils.verifyType(shortMessage, str)
    utils.verifyType(longMessage, str)
    self.logLevel_ = logLevel
    self.action_ = action
    self.shortMessage_ = shortMessage
    self.longMessage_ = longMessage or shortMessage

# --------------------------------------------------------------------------------------------------------------------
class LogModel(QtCore.QAbstractTableModel):
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
      return QtCore.QVariant(item.logLevel_)
    #if index.column() == LogColumns.COL_LEVEL: 
    #  return logging.getLevelName(item.logLevel_)
    if index.column() == LogColumns.COL_ACTION:
      return QtCore.QVariant(item.action_)
    elif index.column() == LogColumns.COL_MESSAGE: 
      if role == QtCore.Qt.DisplayRole:
        return QtCore.QVariant(item.shortMessage_)
      else:
        return QtCore.QVariant(item.longMessage_)
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
  
  