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
  COL_ACTION  = 2
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
  def __init__(self, parent):
    super(QtCore.QAbstractTableModel, self).__init__(parent)
    self.items_ = []
      
  def rowCount(self, parent):
    return len(self.items_)

  def columnCount(self, parent):
    return LogColumns.NUM_COLS
  
  def data(self, index, role):
    if not index.isValid() or (role <> QtCore.Qt.DisplayRole and role <> QtCore.Qt.ToolTipRole):
      return None
    
    item = self.items_[index.row()]
    #if index.column() == LogColumns.COL_LEVEL: 
    #  return logging.getLevelName(item.logLevel_)
    if index.column() == LogColumns.COL_ACTION:
      return item.action_
    elif index.column() == LogColumns.COL_MESSAGE: 
      if role == QtCore.Qt.DisplayRole:
        return item.shortMessage_
      else:
        return item.longMessage_
    else: 
      return None  
  
  def headerData(self, section, orientation, role):
    if role <> QtCore.Qt.DisplayRole or orientation == QtCore.Qt.Vertical:
      return None
    
    #if section == LogColumns.COL_LEVEL: 
    #  return "Type"
    if section == LogColumns.COL_ACTION:
      return "Action"
    elif section == LogColumns.COL_MESSAGE: 
      return "Message"
  
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
  
  