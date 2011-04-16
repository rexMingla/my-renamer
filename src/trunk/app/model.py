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
  COL_SELECTED = 2
  COL_STATUS   = 3
  NUM_COLS     = 4

  
class TreeItem(object):
  def __init__(self, data, parent=None):
    self.parent_ = parent
    self.rowData_ = data
    self.childItems = []

  def appendChild(self, item):
    self.childItems.append(item)

  def child(self, row):
    return self.childItems[row]

  def childCount(self):
    return len(self.childItems)

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
      return self.parent_.childItems.index(self)

    return 0


class TreeModel(QtCore.QAbstractItemModel):
  def __init__(self, parent=None):
    super(TreeModel, self).__init__(parent)
    self._seasons_ = []
    self.rootItem_ = TreeItem(("",))  
    
  def columnCount(self, parent):
    return Columns.NUM_COLS
    #if parent.isValid():
    #  return parent.internalPointer().columnCount()
    #else:
    #  return self.rootItem_.columnCount()

  def data(self, index, role):
    if not index.isValid():
      return None

    if role != QtCore.Qt.DisplayRole:
      return None

    item = index.internalPointer()

    return item.data(index.column())

  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags

    return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

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
        ti = TreeItem((name,), self.rootItem_)
        self.rootItem_.appendChild(ti)
        for mi in season.moveItems_:
          ti.appendChild(TreeItem((mi.oldName_, mi.newName_, moveItem.MoveItem.typeStr(mi.matchType_)), ti))   
      self.endInsertRows()
