#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

from tv import season, moveItem

import utils

class Columns:
  COL_OLD_NAME = 0
  COL_NEW_NAME = 1
  COL_STATUS   = 2
  NUM_COLS     = 3

  
class TreeItem(object):
  def __init__(self, rowData, rawData=None, parent=None):
    self.parent_ = parent
    self.rowData_ = rowData
    self.raw_ = rawData
    self.childItems_ = []

  def appendChild(self, item):
    self.childItems_.append(item)

  def child(self, row):
    return self.childItems_[row]

  def childCount(self):
    return len(self.childItems_)

  def columnCount(self):
    return len(self.rowData_)

  def data(self, column):
    try:
      return self.rowData_[column]
    except IndexError:
      return None

  def parent(self):
    return self.parent_

  def row(self):
    if self.parent_:
      return self.parent_.childItems_.index(self)
    return 0
  
  def isSeason(self):
    return isinstance(self.raw_, season.Season)
  
  def isMoveItem(self):
    return isinstance(self.raw_, moveItem.MoveItem)
  
  def canCheck(self):
    if not self.childItems_:
      return self.raw_.canMove_
    else:
      return True
  
  def checkState(self):
    cs = QtCore.Qt.Checked
    if self.isMoveItem():
      if not self.raw_.performMove_:
        cs = QtCore.Qt.Unchecked
    elif self.isSeason():
      checkCount = 0
      uncheckCount = 0
      for c in self.childItems_:
        if c.canCheck():
          if c.checkState() == QtCore.Qt.Unchecked:
            uncheckCount += 1
          else:
            checkCount += 1
      if checkCount and not uncheckCount:
        cs = QtCore.Qt.Checked
      elif not checkCount and uncheckCount:
        cs = QtCore.Qt.Unchecked
      else:
        cs = QtCore.Qt.PartiallyChecked
    return cs
  
  def setCheckState(self, cs):
    isChecked = cs == QtCore.Qt.Checked
    if self.isMoveItem() and self.raw_.canMove_:
      self.raw_.performMove_ = isChecked
    elif self.isSeason():
      self.raw_.performMove_ = isChecked

class TreeModel(QtCore.QAbstractItemModel):
  def __init__(self, parent=None):
    super(TreeModel, self).__init__(parent)
    self._seasons_ = []
    self.rootItem_ = TreeItem(("",))  
    
  def columnCount(self, parent):
    return Columns.NUM_COLS

  def data(self, index, role):
    if not index.isValid():
      return None
    
    item = index.internalPointer()
    if role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      return item.checkState()
    elif role == QtCore.Qt.DisplayRole:
      return item.data(index.column())
    else:
      return None
    
  def setData(self, index, value, role):
    if not index.isValid():
      return False

    if role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      item = index.internalPointer()
      item.setCheckState(value)
      self.dataChanged.emit(index, index)
      if item.isSeason():
        for child in item.childItems_:
          child.setCheckState(value)
          changedIndex = index.child(Columns.COL_OLD_NAME, child.row())
          self.dataChanged.emit(changedIndex, changedIndex)
      elif item.isMoveItem():
        self.dataChanged.emit(index.parent(), index.parent())
      return True
    return False

  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags
    
    item = index.internalPointer()
    
    f = QtCore.Qt.ItemIsSelectable
    if item.canCheck():
      f |= QtCore.Qt.ItemIsEnabled 
      if index.column() == Columns.COL_OLD_NAME:
        f |= QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsTristate
    return f

  def headerData(self, section, orientation, role):
    if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
      if section == Columns.COL_OLD_NAME:
        return "Existing File"
      elif section == Columns.COL_NEW_NAME:
        return "New Name"
      elif section == Columns.COL_STATUS:
        return "Status"
    return None

  def index(self, row, column, parent):
    if not self.hasIndex(row, column, parent):
      return QtCore.QModelIndex()

    if not parent.isValid():
      parent_ = self.rootItem_
    else:
      parent_ = parent.internalPointer()

    childItem = parent_.child(row)
    if childItem:
      return self.createIndex(row, column, childItem)
    else:
      return QtCore.QModelIndex()

  def parent(self, index):
    if not index.isValid():
      return QtCore.QModelIndex()

    childItem = index.internalPointer()
    parent_ = childItem.parent()

    if parent_ == self.rootItem_:
      return QtCore.QModelIndex()

    return self.createIndex(parent_.row(), 0, parent_)

  def rowCount(self, parent):
    if parent.column() > 0:
      return 0

    if not parent.isValid():
      parent_ = self.rootItem_
    else:
      parent_ = parent.internalPointer()

    return parent_.childCount()
  
  def setSeasons(self, seasons):
    if self._seasons_:
      self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self._seasons_) - 1)
      self.rootItem_ = TreeItem(("",))
      self.endRemoveRows()
    
    self._seasons_ = seasons
    if seasons:
      self.beginInsertRows(QtCore.QModelIndex(), 0, len(self._seasons_) - 1)
      for season in self._seasons_:
        name = "Season: %s #: %d" % (season.seasonName_, season.seasonNum_)
        ti = TreeItem((name,), season, self.rootItem_)
        self.rootItem_.appendChild(ti)
        for mi in season.moveItems_:
          ti.appendChild(TreeItem((mi.oldName_, mi.newName_, moveItem.MoveItem.typeStr(mi.matchType_)), mi, ti))   
      self.endInsertRows()
