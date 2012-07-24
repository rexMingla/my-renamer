#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Model and other classes pertaining to the set of tv seasons to be modified in the workbench
# --------------------------------------------------------------------------------------------------------------------
import copy

from PyQt4 import QtCore
from PyQt4 import QtGui

from common import fileHelper
from common import utils
import episode
import moveItemCandidate
import season
import seasonHelper

# --------------------------------------------------------------------------------------------------------------------
class Columns:
  """ Columns used in workbench model. """
  COL_OLD_NAME = 0
  COL_NEW_NUM  = 1
  COL_NEW_NAME = 2
  COL_STATUS   = 3
  NUM_COLS     = 4

RAW_DATA_ROLE = QtCore.Qt.UserRole + 1
  
# --------------------------------------------------------------------------------------------------------------------
class TreeItem(object):
  """ Individual item in the workbench model. The item may represent a season or a moveItemCandidate. """ 
  def __init__(self, rawData=None, parent=None):
    self.parent = parent
    self.raw = rawData
    self.childItems = []

  def appendChild(self, item):
    self.childItems.append(item)

  def child(self, row):
    return self.childItems[row]

  def childCount(self):
    return len(self.childItems)

  def columnCount(self):
    return len(self.rowData_)

  def data(self, column, role=QtCore.Qt.DisplayRole):
    if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole, QtCore.Qt.ForegroundRole):
      return None
    
    if self.isMoveItemCandidate():
      if role == QtCore.Qt.ForegroundRole and self.raw.matchType() == moveItemCandidate.MoveItemCandidate.MISSING_NEW:
        return QtGui.QBrush(QtCore.Qt.red)       
      if column == Columns.COL_OLD_NAME:
        if role == QtCore.Qt.ToolTipRole:
          return self.raw.source.filename
        else:
          return fileHelper.FileHelper.basename(self.raw.source.filename)
      elif column == Columns.COL_NEW_NUM:
        if self.raw.destination.epNum == episode.UNRESOLVED_KEY:
          return None
        else:
          return self.raw.destination.epNum
      elif column == Columns.COL_NEW_NAME:
        return self.raw.destination.epName
      elif column == Columns.COL_STATUS:
        return moveItemCandidate.MoveItemCandidate.typeStr(self.raw.matchType())
    elif self.isSeason():
      isResolved = self.raw.seasonNum == episode.UNRESOLVED_KEY
      if role == QtCore.Qt.ForegroundRole and isResolved:
        return QtGui.QBrush(QtCore.Qt.red)      
      elif column == Columns.COL_OLD_NAME:
        if role == QtCore.Qt.ToolTipRole:
          return "Folder: {}".format(self.raw.inputFolder)
        else:        
          if isResolved:
            return "Season: {} #: <Unknown>".format(self.raw.seasonName)
          else:
            return "Season: {} #: {}".format(self.raw.seasonName, self.raw.seasonNum)
    return None
    
  def parent(self):
    return self.parent

  def row(self):
    if self.parent:
      return self.parent.childItems.index(self)
    return 0
  
  def isSeason(self):
    return isinstance(self.raw, season.Season)
  
  def isMoveItemCandidate(self):
    return isinstance(self.raw, moveItemCandidate.MoveItemCandidate)
  
  def canCheck(self):
    if self.isMoveItemCandidate():
      return self.raw.canMove
    else:
      for c in self.childItems:
        if c.canCheck():
          return True
      return False
  
  def checkState(self):
    cs = QtCore.Qt.Checked
    if self.isMoveItemCandidate():
      if not self.raw.performMove:
        cs = QtCore.Qt.Unchecked
    elif self.isSeason():
      checkCount = 0
      uncheckCount = 0
      for c in self.childItems:
        if c.canCheck():
          if c.checkState() == QtCore.Qt.Unchecked:
            uncheckCount += 1
          else:
            checkCount += 1
      if not checkCount:
        cs = QtCore.Qt.Unchecked
      elif checkCount and not uncheckCount:
        cs = QtCore.Qt.Checked
      else:
        cs = QtCore.Qt.PartiallyChecked
    return cs
  
  def setCheckState(self, cs):
    isChecked = cs == QtCore.Qt.Checked
    if self.isMoveItemCandidate() and self.raw.canMove:
      self.raw.performMove = isChecked
    elif self.isSeason():
      self.raw.performMove = isChecked
      
# --------------------------------------------------------------------------------------------------------------------
class TvModel(QtCore.QAbstractItemModel):
  """ 
  Represents 0 or more tv seasons. Each folder (season) contains a collection of moveItemCandiates. 
  At the moment folder can not be nested, but it is foreseeable that this this would be handy in the future.
  """
  workBenchChangedSignal = QtCore.pyqtSignal(bool)
  
  def __init__(self, parent=None):
    super(TvModel, self).__init__(parent)
    self._seasons = []
    self.rootItem = TreeItem(("",))
    self._bulkProcessing = False
    
  def columnCount(self, parent):
    return Columns.NUM_COLS

  def data(self, index, role):
    if not index.isValid():
      return None
    if role == RAW_DATA_ROLE:
      item = index.internalPointer()
      return (copy.copy(item.raw), item.isMoveItemCandidate()) #wow. this is confusing as hell..
    
    item = index.internalPointer()
    if role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      if item.canCheck():
        return item.checkState()
      return None
    else:
      return item.data(index.column(), role)
    
  def setData(self, index, value, role):
    if not index.isValid():
      return False
    ret = False
    
    if role == RAW_DATA_ROLE:
      item = index.internalPointer()
      if item.isMoveItemCandidate():
        parentItem = item.parent
        parentIndex = index.parent()
        utils.verify(parentItem.isSeason(), "Not a Season")
        
        self.beginRemoveRows(parentIndex, 0, parentItem.childCount() - 1)
        newSourceMap = copy.copy(parentItem.raw.source)
        intVal, isOk = value.toInt()
        utils.verify(isOk, "cast value to int")
        newSourceMap.setKeyForFilename(intVal, item.raw.source.filename)
        parentItem.raw.updateSource(newSourceMap)
        parentItem.childItems = []
        for mi in parentItem.raw.moveItemCandidates:
          parentItem.appendChild(TreeItem(mi, parentItem))
        self.endRemoveRows()
        self.beginInsertRows(parentIndex, 0, parentItem.childCount() - 1)
        self.endInsertRows()              
        ret = True
      else:
        self.beginRemoveRows(index, 0, item.childCount() - 1)
        item.raw = value
        item.childItems = []
        for mi in item.raw.moveItemCandidates:
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
        for child in item.childItems:
          child.setCheckState(value)
          changedIndex = index.child(Columns.COL_OLD_NAME, child.row())
          self.dataChanged.emit(changedIndex, changedIndex)
      elif item.isMoveItemCandidate():
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
      #elif index.column() == Columns.COL_NEW_NAME and item.isMoveItemCandidate() and item.raw.oldName_:
      #  f |= QtCore.Qt.ItemIsEditable
    elif item.isMoveItemCandidate() and item.raw.canEdit:
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
      parent = self.rootItem
    else:
      parent = parent.internalPointer()

    childItem = parent.child(row)
    if childItem:
      return self.createIndex(row, column, childItem)
    else:
      return QtCore.QModelIndex()

  def parent(self, index):
    if not index.isValid():
      return QtCore.QModelIndex()

    childItem = index.internalPointer()
    p = childItem.parent

    if p == self.rootItem:
      return QtCore.QModelIndex()

    return self.createIndex(p.row(), 0, p)

  def rowCount(self, parent):
    if parent.column() > 0:
      return 0

    if not parent.isValid():
      parent = self.rootItem
    else:
      parent = parent.internalPointer()

    return parent.childCount()
  
  def addItem(self, s):
    utils.verifyType(s, season.Season)
    #check if already in list
    self.beginInsertRows(QtCore.QModelIndex(), len(self._seasons), len(self._seasons))
    ti = TreeItem(s, self.rootItem)
    self.rootItem.appendChild(ti)
    for mi in s.moveItemCandidates:
      ti.appendChild(TreeItem(mi, ti))  
    self._seasons.append(s)
    self.endInsertRows()      
    self._emitWorkBenchChanged()
    
  def clear(self):
    self.beginResetModel()
    self._seasons = []
    self.rootItem = TreeItem(("",))  
    self.endResetModel()
    self._emitWorkBenchChanged()
    
  def items(self):
    seasons = []
    for i in range(self.rootItem.childCount()):
      seasonItem = self.rootItem.child(i)
      utils.verify(seasonItem.isSeason(), "Not a Season")
      raw = seasonItem.raw
      if seasonItem.checkState() != QtCore.Qt.Unchecked:
        seasons.append(raw)
    return seasons
  
  def overallCheckedState(self):
    filteredItems = [i for i in self.rootItem.childItems if i.canCheck()]
    if not filteredItems:
      return None
    
    ret = QtCore.Qt.PartiallyChecked
    if all(i.checkState() == QtCore.Qt.Checked for i in filteredItems):
      ret = QtCore.Qt.Checked 
    elif all(i.checkState() == QtCore.Qt.Unchecked for i in filteredItems):
      ret = QtCore.Qt.Unchecked 
    return ret
  
  def setOverallCheckedState(self, isChecked):
    utils.verifyType(isChecked, bool)
    self._bulkProcessing = True
    cs = QtCore.Qt.Checked
    if not isChecked:
      cs = QtCore.Qt.Unchecked
    for i in range(self.rootItem.childCount()):
      idx = self.index(i, Columns.COL_OLD_NAME, QtCore.QModelIndex())
      self.setData(idx, cs, QtCore.Qt.CheckStateRole)
    self._bulkProcessing = False
    self._emitWorkBenchChanged()
  
  def _hasMoveableItems(self):
    ret = False
    for i in range(self.rootItem.childCount()):
      seasonItem = self.rootItem.child(i)
      if seasonItem.checkState() != QtCore.Qt.Unchecked:
        ret = True
        break
    return ret

  def _emitWorkBenchChanged(self):
    hasItems = self._hasMoveableItems()
    self.workBenchChangedSignal.emit(hasItems)