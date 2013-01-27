#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Model and other classes pertaining to the set of tv seasons to be modified in the workbench
# --------------------------------------------------------------------------------------------------------------------
import abc
import copy

from PyQt4 import QtGui
from PyQt4 import QtCore

from media.base import model as base_model
from common import file_helper
from common import utils

from media.tv import types as tv_types
from media.tv import manager as tv_manager

# --------------------------------------------------------------------------------------------------------------------
class Columns:
  """ Columns used in workbench model. """
  COL_OLD_NAME  = 0
  COL_NEW_NUM   = 1
  COL_NEW_NAME  = 2
  COL_STATUS    = 3
  COL_FILE_SIZE = 4
  NUM_COLS      = 5

RAW_DATA_ROLE = QtCore.Qt.UserRole + 1

# --------------------------------------------------------------------------------------------------------------------
class BaseItem(object):
  """ Individual item in the workbench model. The item may represent a season or a moveItemCandidate. """ 
  __metaclass__ = abc.ABCMeta
  
  def __init__(self, rawData=None, parent=None):
    super(BaseItem, self).__init__()
    self.parent = parent
    self.raw = rawData
    self.childItems = []

  def appendChild(self, item):
    self.childItems.append(item)

  def child(self, row):
    return self.childItems[row]

  def childCount(self):
    return len(self.childItems)

  def parent(self):
    return self.parent

  def row(self):
    if self.parent:
      return self.parent.childItems.index(self)
    return 0

  def isSeason(self):
    return isinstance(self.raw, tv_types.Season)

  def isEpisode(self):
    return isinstance(self.raw, tv_types.EpisodeRenameItem)
  
  @abc.abstractmethod
  def setData(self, model, index, value, role):
    pass

  @abc.abstractmethod
  def data(self, index, role=QtCore.Qt.DisplayRole):
    pass

  @abc.abstractmethod
  def canCheck(self):
    pass

  @abc.abstractmethod
  def checkState(self):
    pass

  @abc.abstractmethod
  def setCheckState(self, cs):
    pass

  def canEdit(self):
    return False

# --------------------------------------------------------------------------------------------------------------------
class ContainerItem(BaseItem):
  """ Individual item in the workbench model. The item may represent a season or a moveItemCandidate. """ 
  def __init__(self, rawData=None, parent=None):
    super(ContainerItem, self).__init__(rawData, parent)
    
  def setData(self, model, index, value, role):
    if not index.isValid():
      ret = False
    
    if role == RAW_DATA_ROLE:
      model.beginRemoveRows(index, 0, self.childCount() - 1)
      self.raw = value
      self.childItems = []
      for mi in self.raw.episodeMoveItems:
        self.appendChild(LeafItem(mi, self))
      model.endRemoveRows()
      model.beginInsertRows(index, 0, self.childCount() - 1)
      #fix the check boxes
      for j in range(len(self.childItems)):
        idx = model.index(j, Columns.COL_NEW_NAME, index)
      model.endInsertRows()
      model.dataChanged.emit(index.sibling(index.row(), 0), index.sibling(index.row(), Columns.NUM_COLS-1))
      ret = True
    elif role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      self.setCheckState(value)
      model.dataChanged.emit(index, index)
      #HACK: shouldn't need this right?
      for child in self.childItems:
        child.setCheckState(value)
        changedIndex = index.child(Columns.COL_OLD_NAME, child.row())
        model.dataChanged.emit(changedIndex, changedIndex)
      ret = True
    return ret  

  def data(self, index, role=QtCore.Qt.DisplayRole):
    if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole, QtCore.Qt.ForegroundRole):
      return None

    isUnresolved = self.raw.info.seasonNum == tv_types.UNRESOLVED_KEY
    if role == QtCore.Qt.ForegroundRole and isUnresolved:
      return QtGui.QBrush(QtCore.Qt.red)      
    elif index.column() == Columns.COL_OLD_NAME:
      if role == QtCore.Qt.ToolTipRole:
        return "Folder: {}".format(self.raw.inputFolder)
      else:
        return str(self.raw)

  def canCheck(self):
    return any(c.canCheck() for c in self.childItems)

  def checkState(self):
    cs = None
    checkedItems = [c.checkState() == QtCore.Qt.Checked for c in self.childItems if c.canCheck()]
    if not checkedItems or all(not c for c in checkedItems):
      cs = QtCore.Qt.Unchecked
    elif all(checkedItems):
      cs = QtCore.Qt.Checked
    else:
      cs = QtCore.Qt.PartiallyChecked
    return cs

  def setCheckState(self, cs):
    pass
      
# --------------------------------------------------------------------------------------------------------------------
class LeafItem(BaseItem):
  """ Individual item in the workbench model. The item may represent a season or a moveItemCandidate. """ 
  def __init__(self, rawData=None, parent=None):
    super(LeafItem, self).__init__(rawData, parent)

  def data(self, index, role=QtCore.Qt.DisplayRole):
    if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole, QtCore.Qt.ForegroundRole):
      return None

    column = index.column()
    if role == QtCore.Qt.ForegroundRole:
      if self.raw.matchType() == tv_types.EpisodeRenameItem.MISSING_NEW:
        return QtGui.QBrush(QtCore.Qt.red)       
      elif self.raw.matchType() == tv_types.EpisodeRenameItem.MISSING_OLD:
        return QtGui.QBrush(QtCore.Qt.gray)       
    if column == Columns.COL_OLD_NAME:
      if role == QtCore.Qt.ToolTipRole:
        return self.raw.filename
      else:
        return file_helper.FileHelper.basename(self.raw.filename)
    elif column == Columns.COL_NEW_NUM:
      if self.raw.info.epNum == tv_types.UNRESOLVED_KEY:
        return None
      else:
        return self.raw.info.epNum
    elif column == Columns.COL_NEW_NAME:
      return self.raw.info.epName
    elif column == Columns.COL_STATUS:
      return tv_types.EpisodeRenameItem.typeStr(self.raw.matchType())
    elif column == Columns.COL_FILE_SIZE:
      if self.raw.matchType() != tv_types.EpisodeRenameItem.MISSING_OLD:
        return utils.bytesToString(self.raw.fileSize) 
    return None
  
  def setData(self, model, index, value, role):
    if not index.isValid():
      return False
    ret = False

    if role == RAW_DATA_ROLE:
      parentItem = self.parent
      parentIndex = index.parent()
      utils.verify(parentItem.isSeason(), "Not a Season")

      model.beginRemoveRows(parentIndex, 0, parentItem.childCount() - 1)
      parentItem.raw.setEpisodeForFilename(value, self.raw.filename)
      parentItem.childItems = []
      for mi in parentItem.raw.episodeMoveItems:
        parentItem.appendChild(LeafItem(mi, parentItem))
      model.endRemoveRows()
      ret = True
    elif role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      self.setCheckState(value)
      model.dataChanged.emit(index, index)
      #model.dataChanged.emit(index.parent(), index.parent())
      ret = True
    return ret

  def canCheck(self):
    return self.raw.canMove

  def checkState(self):
    cs = None
    if self.canCheck():
      cs = QtCore.Qt.Checked if self.raw.performMove else QtCore.Qt.Unchecked
    return cs

  def setCheckState(self, cs):    
    self.raw.performMove = cs == QtCore.Qt.Checked

  def canEdit(self):
    return bool(self.raw.filename)

# --------------------------------------------------------------------------------------------------------------------
class TvModel(QtCore.QAbstractItemModel):
  """ 
  Represents 0 or more tv seasons. Each folder (season) contains a collection of moveItemCandiates. 
  At the moment folder can not be nested, but it is foreseeable that this this would be handy in the future.
  """
  workBenchChangedSignal = QtCore.pyqtSignal(bool)
  beginUpdateSignal = QtCore.pyqtSignal()
  endUpdateSignal = QtCore.pyqtSignal()  
  
  ALL_ACTIONS = (base_model.BaseWorkBenchModel.ACTION_DELETE,
                 base_model.BaseWorkBenchModel.ACTION_LAUNCH,
                 base_model.BaseWorkBenchModel.ACTION_OPEN,
                 base_model.BaseWorkBenchModel.ACTION_EPISODE,
                 base_model.BaseWorkBenchModel.ACTION_SEASON)

  def __init__(self, parent=None):
    super(QtCore.QAbstractItemModel, self).__init__(parent)
    self.rootItem = None
    self._bulkProcessing = False
    self.clear()
    #self._view = parent # hack

  def columnCount(self, parent):
    return Columns.NUM_COLS
  
  def getFile(self, index):
    if not index.isValid():
      return None

    item = self._getItem(index)
    ret = ""
    if item.isEpisode():
      ret = item.raw.filename 
    return ret
  
  def getFolder(self, index):
    if not index.isValid():
      return None

    item = self._getItem(index)
    ret = ""
    if item.isEpisode():
      ret = file_helper.FileHelper.dirname(item.raw.filename)
    else:
      ret = item.raw.inputFolder
    return ret
  
  def getDeleteItem(self, index):
    if not index.isValid():
      return None

    item = self._getItem(index)
    ret = ""
    if item.isEpisode():
      ret = item.raw.filename
    else:
      ret = item.raw.inputFolder
    return ret
  
  def canEdit(self, index):
    if not index.isValid():
      return False
    return self._getItem(index).canEdit()
  
  def getRenameItem(self, index):
    if not index.isValid():
      return None
    item = self._getItem(index)
    return item.raw if item.isEpisode() and item.canCheck() else None
  
  def getAvailableActions(self, index):
    canEditEp = self.canEdit(index)
    canLaunch = bool(self.getFile(index))
    canOpen = bool(self.getFolder(index))
    canDelete = bool(self.getDeleteItem(index))
    
    ret = {}
    ret[base_model.BaseWorkBenchModel.ACTION_EPISODE] = canEditEp
    ret[base_model.BaseWorkBenchModel.ACTION_SEASON] = canOpen
    ret[base_model.BaseWorkBenchModel.ACTION_OPEN] = canOpen
    ret[base_model.BaseWorkBenchModel.ACTION_LAUNCH] = canLaunch
    ret[base_model.BaseWorkBenchModel.ACTION_DELETE] = canDelete
    return ret

  def data(self, index, role):
    if not index.isValid():
      return None

    item = self._getItem(index)
    if role == RAW_DATA_ROLE:
      return (copy.copy(item.raw), item.isEpisode()) #wow. this is confusing as hell..

    if role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      return item.checkState()
    else:
      return item.data(index, role)
 
  def setData(self, index, value, role):
    if not index.isValid():
      return False
    
    item = self._getItem(index)
    ret = item.setData(self, index, value, role)
    
    if ret and not self._bulkProcessing:   
      self._emitWorkBenchChanged()
    return ret

  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags

    item = self._getItem(index)

    f = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
    if item.canCheck() and index.column() == Columns.COL_OLD_NAME:
      f |= QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsTristate
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
      elif section == Columns.COL_FILE_SIZE:
        return "File Size"    
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

    childItem = self._getItem(index)
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
    #utils.verifyType(s, tv_types.Season)
    #check if already in list
    rowCount = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), rowCount, rowCount)
    ti = ContainerItem(s, self.rootItem)
    self.rootItem.appendChild(ti)
    for mi in s.episodeMoveItems:
      ti.appendChild(LeafItem(mi, ti))
    self.endInsertRows()     
    if not self._bulkProcessing:
      self._emitWorkBenchChanged()    

  def clear(self):
    self.beginResetModel()
    self.rootItem = ContainerItem(("",))  
    self.endResetModel()
    if not self._bulkProcessing:
      self._emitWorkBenchChanged()    

  def items(self):
    ret = []
    for seasonItem in [self.rootItem.child(i) for i in range(self.rootItem.childCount())]:
      for epItem in [seasonItem.child(i) for i in range(seasonItem.childCount())]:
        if epItem.checkState() == QtCore.Qt.Checked:
          ret.append(epItem.raw)
    return ret

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
    #utils.verifyType(isChecked, bool)
    self.beginUpdate()
    cs = QtCore.Qt.Checked if isChecked else QtCore.Qt.Unchecked
    for i in range(self.rootItem.childCount()):
      idx = self.index(i, Columns.COL_OLD_NAME, QtCore.QModelIndex())
      self.setData(idx, cs, QtCore.Qt.CheckStateRole)
    self.endUpdate()
    self._emitWorkBenchChanged()

  def _hasMoveableItems(self):
    return any(self.rootItem.child(i).checkState() != QtCore.Qt.Unchecked for i in range(self.rootItem.childCount()))

  def _emitWorkBenchChanged(self):
    hasItems = self._hasMoveableItems()
    self.workBenchChangedSignal.emit(hasItems)

  def beginUpdate(self):
    self._bulkProcessing = True
    self.beginUpdateSignal.emit()
    
  def endUpdate(self):
    self._bulkProcessing = False
    self.endUpdateSignal.emit()
    
  def _getItem(self, index):
    return index.internalPointer()
        
  def delete(self, index):
    if not index.isValid():
      return
    
    oldCheckedState = self.overallCheckedState()
    row = index.row()
    item = self._getItem(index)
    if item.isSeason():
      self.beginRemoveRows(index.parent(), row, row)
      self.rootItem.childItems.pop(row)
      self.endRemoveRows()
    else:
      parentItem = item.parent
      self.beginRemoveRows(index.parent(), 0, parentItem.childCount() - 1)
      parentItem.childItems = []
      parentItem.raw.removeSourceFile(item.raw.filename) 
      self.endRemoveRows()

      self.beginInsertRows(index.parent(), 0, len(parentItem.raw.episodeMoveItems) - 1)
      for mi in parentItem.raw.episodeMoveItems:
        parentItem.appendChild(LeafItem(mi, parentItem))
      self.endInsertRows()
      
    newCheckedState = self.overallCheckedState()
    if oldCheckedState != newCheckedState:
      self._emitWorkBenchChanged()
      
base_model.BaseWorkBenchModel.register(TvModel)