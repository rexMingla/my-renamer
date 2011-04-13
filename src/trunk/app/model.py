#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

from tv import season

import utils

class Columns:
  COL_OLD_NAME = 0
  COL_NEW_NAME = 1
  COL_SELECTED = 2
  COL_STATUS   = 3
  NUM_COLS     = 4

  
class TreeItem(object):
  def __init__(self, data, parent=None):
    self.parentItem = parent
    self.itemData = data
    self.childItems = []

  def appendChild(self, item):
    self.childItems.append(item)

  def child(self, row):
    return self.childItems[row]

  def childCount(self):
    return len(self.childItems)

  def columnCount(self):
    return len(self.itemData)

  def data(self, column):
    try:
      return self.itemData[column]
    except IndexError:
      return None

  def parent(self):
    return self.parentItem

  def row(self):
    if self.parentItem:
      return self.parentItem.childItems.index(self)

    return 0


class TreeModel(QtCore.QAbstractItemModel):
  def __init__(self, parent=None):
    super(TreeModel, self).__init__(parent)
    
    self.rootItem_ = TreeItem(("",""))
  
  def columnCount(self, parent):
    if parent.isValid():
      return parent.internalPointer().columnCount()
    else:
      return self.rootItem_.columnCount()

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
      return self.rootItem_.data(section)

    return None

  def index(self, row, column, parent):
    if not self.hasIndex(row, column, parent):
      return QtCore.QModelIndex()

    if not parent.isValid():
      parentItem = self.rootItem_
    else:
      parentItem = parent.internalPointer()

    childItem = parentItem.child(row)
    if childItem:
      return self.createIndex(row, column, childItem)
    else:
      return QtCore.QModelIndex()

  def parent(self, index):
    if not index.isValid():
      return QtCore.QModelIndex()

    childItem = index.internalPointer()
    parentItem = childItem.parent()

    if parentItem == self.rootItem_:
      return QtCore.QModelIndex()

    return self.createIndex(parentItem.row(), 0, parentItem)

  def rowCount(self, parent):
    if parent.column() > 0:
      return 0

    if not parent.isValid():
      parentItem = self.rootItem_
    else:
      parentItem = parent.internalPointer()

    return parentItem.childCount()
  
  def setSeasons(self, seasons):
    #self.modelAboutToBeReset()
    self.rootItem_ = TreeItem(("",""))
    #self.modelReset()
    
    if seasons:
      self.beginInsertRows(QtCore.QModelIndex(), 0, len(seasons) - 1)
      for season in seasons:
        ti = TreeItem(("Season","Series"), self.rootItem_)
        self.rootItem_.appendChild(ti)
        for mi in season.moveItems_:
          ti.appendChild(TreeItem(("w","t"), ti))    
      self.endInsertRows()
