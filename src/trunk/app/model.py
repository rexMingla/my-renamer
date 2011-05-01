#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import copy
from PyQt4 import QtCore

from tv import season, moveItem, episode, seasonHelper

import utils

class Columns:
  COL_OLD_NAME = 0
  COL_NEW_NUM  = 1
  COL_NEW_NAME = 2
  COL_STATUS   = 3
  NUM_COLS     = 4

RAW_DATA_ROLE = QtCore.Qt.UserRole + 1
  
class TreeItem(object):
  def __init__(self, rawData=None, parent=None):
    self.parent_ = parent
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
    if self.isMoveItem():      
      if column == Columns.COL_OLD_NAME:
        return self.raw_.oldName_
      elif column == Columns.COL_NEW_NUM:
        return self.raw_.key_
      elif column == Columns.COL_NEW_NAME:
        return self.raw_.newName_
      elif column == Columns.COL_STATUS:
        return moveItem.MoveItem.typeStr(self.raw_.matchType_)
    elif self.isSeason():
      if column == Columns.COL_OLD_NAME:
        return "Season: %s #: %d" % (self.raw_.seasonName_, self.raw_.seasonNum_)
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
    if self.isMoveItem():
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
  workBenchChangedSignal_ = QtCore.pyqtSignal(bool)
  
  def __init__(self, parent=None):
    super(TreeModel, self).__init__(parent)
    self._seasons_ = []
    self.rootItem_ = TreeItem(("",))  
    
  def columnCount(self, parent):
    return Columns.NUM_COLS

  def data(self, index, role):
    if not index.isValid():
      return None
    if role == RAW_DATA_ROLE:
      item = index.internalPointer()
      return (item.raw_, item.isMoveItem())
    
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
    ret = False
    
    if role == RAW_DATA_ROLE:
      item = index.internalPointer()
      if item.isMoveItem():
        parentItem = item.parent()
        parentIndex = index.parent()
        utils.verify(parentItem.isSeason(), "Not a Season")
        
        self.beginRemoveRows(parentIndex, 0, parentItem.childCount() - 1)
        newSourceMap = copy.copy(parentItem.raw_.source_)
        intVal, isOk = value.toInt()
        utils.verify(isOk, "cast value to int")
        newSourceMap.setKeyForFilename(intVal, item.raw_.oldName_)
        parentItem.raw_.updateSource(newSourceMap)
        parentItem.childItems_ = []
        for mi in parentItem.raw_.moveItems_:
          parentItem.appendChild(TreeItem(mi, parentItem))
        self.endRemoveRows()
        self.beginInsertRows(parentIndex, 0, parentItem.childCount() - 1)
        self.endInsertRows()              
        ret = True
      else:
        self.beginRemoveRows(index, 0, item.childCount() - 1)
        params = value.toList()
        utils.verify(len(params) == 2, "Name and value must be in list")
        seasonName = utils.toString(params[0].toString())
        seasonNum, isOk = params[1].toInt()
        utils.verify(isOk, "cast value to int")
        newDestMap = seasonHelper.SeasonHelper.getDestinationEpisodeMapFromTVDB(seasonName, seasonNum)
        item.raw_.updateDestination(seasonName, seasonNum, newDestMap)
        item.childItems_ = []
        for mi in item.raw_.moveItems_:
          item.appendChild(TreeItem(mi, item))
        self.endRemoveRows()
        self.beginInsertRows(index, 0, item.childCount() - 1)
        self.endInsertRows()
        self.dataChanged.emit(index.sibling(index.row(), 0), index.sibling(index.row(), Columns.NUM_COLS-1))
        ret = True
    elif role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
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
      ret = True
    if ret:   
      self._emitWorkBenchChanged()
    return ret

  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags
    
    item = index.internalPointer()
    
    f = QtCore.Qt.ItemIsSelectable
    if item.canCheck():
      f |= QtCore.Qt.ItemIsEnabled 
      if index.column() == Columns.COL_OLD_NAME:
        f |= QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsTristate
      #elif index.column() == Columns.COL_NEW_NAME and item.isMoveItem() and item.raw_.oldName_:
      #  f |= QtCore.Qt.ItemIsEditable
    elif item.isMoveItem() and item.raw_.canEdit_:
      f |= QtCore.Qt.ItemIsEnabled       
    return f

  def headerData(self, section, orientation, role):
    if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
      if section == Columns.COL_OLD_NAME:
        return "Existing File"
      elif section == Columns.COL_NEW_NUM:
        return "Episode Num"
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
    utils.verifyType(seasons, list)
    if self._seasons_:
      self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self._seasons_) - 1)
      self.rootItem_ = TreeItem()
      self.endRemoveRows()
    
    self._seasons_ = seasons
    if seasons:
      self.beginInsertRows(QtCore.QModelIndex(), 0, len(self._seasons_) - 1)
      for season in self._seasons_:
        ti = TreeItem(season, self.rootItem_)
        self.rootItem_.appendChild(ti)
        for mi in season.moveItems_:
          ti.appendChild(TreeItem(mi, ti))   
      self.endInsertRows()      
    self._emitWorkBenchChanged()
    
  def moveItems(self):
    items = []
    for i in range(self.rootItem_.childCount()):
      seasonItem = self.rootItem_.child(i)
      utils.verify(seasonItem.isSeason(), "Not a Season")
      data = seasonItem.raw_
      for item in data.moveItems_:
        if item.performMove_:
          items.append(item)
    return items
  
  def _hasMoveableItems(self):
    ret = False
    for i in range(self.rootItem_.childCount()):
      seasonItem = self.rootItem_.child(i)
      if not seasonItem.checkState() == QtCore.Qt.Unchecked:
        ret = True
        break
    return ret

  def _emitWorkBenchChanged(self):
    hasItems = self._hasMoveableItems()
    self.workBenchChangedSignal_.emit(hasItems)