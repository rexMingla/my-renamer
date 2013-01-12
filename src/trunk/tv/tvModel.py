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
from common import workBench

import tvImpl
import tvManager

# --------------------------------------------------------------------------------------------------------------------
class SeriesDelegate(QtGui.QStyledItemDelegate):
  def __init__ (self, parent = None):
    QtGui.QStyledItemDelegate.__init__(self, parent)  
    
  def createEditor(self, parent, option, index):
    model = index.model()
    item, isMoveCandidate = model.data(index, RAW_DATA_ROLE)
    if not isMoveCandidate:
      return None

    season, ep = model.data(index.parent(), RAW_DATA_ROLE)[0], item
    if ep.matchType() == tvImpl.EpisodeRenameItem.MISSING_OLD:
      return None

    if index.column() == Columns.COL_NEW_NAME:
      comboBox = QtGui.QComboBox(parent)
      
      comboBox.addItem("Not set", tvImpl.UNRESOLVED_KEY)
      comboBox.insertSeparator(1)
      # fill it

      episodeMoveItems = copy.copy(season.episodeMoveItems)
      episodeMoveItems = sorted(episodeMoveItems, key=lambda item: item.info.epNum)
      for mi in episodeMoveItems:
        if mi.info.epName != tvImpl.UNRESOLVED_NAME:
          displayName = "{}: {}".format(mi.info.epNum, mi.info.epName)
          comboBox.addItem(displayName, mi.info.epNum)
      comboBox.setCurrentIndex(comboBox.findData(ep.source.epNum))
      # Commit data to the model once the selection has changed
      comboBox.currentIndexChanged.connect(self.commitEditorData)
      return comboBox;

  def setEditorData(self, editor, index):
    model = index.model()
    item, isMoveCandidate = model.data(index, RAW_DATA_ROLE)
    if not isMoveCandidate:
      return None

    season, ep = model.data(index.parent(), RAW_DATA_ROLE)[0], item
    if ep.matchType() == tvImpl.EpisodeRenameItem.MISSING_OLD:
      return None

    if index.column() == Columns.COL_NEW_NAME:
      editor.setCurrentIndex(editor.findData(ep.source.epNum))
 
  def setModelData(self, editor, model, index):
    model = index.model()
    item, isMoveCandidate = model.data(index, RAW_DATA_ROLE)
    if not isMoveCandidate:
      return None

    season, ep = model.data(index.parent(), RAW_DATA_ROLE)[0], item
    if ep.matchType() == tvImpl.EpisodeRenameItem.MISSING_OLD:
      return None

    if index.column() == Columns.COL_NEW_NAME:
      model.setData(index, editor.itemData(editor.currentIndex()), RAW_DATA_ROLE)

  def commitEditorData(self):
    editor = self.sender()
    self.commitData.emit(editor)

  def closeAndCommitEditorData(self):
    self.commitEditorData()
    self.closeEditor.emit(editor)
    
  def sizeHint(self, option, index):
    return super(SeriesDelegate, self).sizeHint(option, index)  

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

  def columnCount(self):
    return len(self.rowData_)

  def parent(self):
    return self.parent

  def row(self):
    if self.parent:
      return self.parent.childItems.index(self)
    return 0

  def isSeason(self):
    return isinstance(self.raw, tvImpl.Season)

  def isMoveItemCandidate(self):
    return isinstance(self.raw, tvImpl.EpisodeRenameItem)
  
  def setData(self, model, index, value, role):
    raise NotImplementedError("BaseItem.setData not implemented")    

  def data(self, index, role=QtCore.Qt.DisplayRole):
    raise NotImplementedError("BaseItem.data not implemented")
  
  def canCheck(self):
    raise NotImplementedError("BaseItem.canCheck not implemented")

  def checkState(self):
    raise NotImplementedError("BaseItem.checkState not implemented")

  def setCheckState(self, cs):
    raise NotImplementedError("BaseItem.setCheckState not implemented")

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

    isUnresolved = self.raw.info.seasonNum == tvImpl.UNRESOLVED_KEY
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
    cs = QtCore.Qt.Checked
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
    if role == QtCore.Qt.ForegroundRole and self.raw.matchType() == tvImpl.EpisodeRenameItem.MISSING_NEW:
      return QtGui.QBrush(QtCore.Qt.red)       
    if column == Columns.COL_OLD_NAME:
      if role == QtCore.Qt.ToolTipRole:
        return self.raw.filename
      else:
        return fileHelper.FileHelper.basename(self.raw.filename)
    elif column == Columns.COL_NEW_NUM:
      if self.raw.info.epNum == tvImpl.UNRESOLVED_KEY:
        return None
      else:
        return self.raw.info.epNum
    elif column == Columns.COL_NEW_NAME:
      return self.raw.info.epName
    elif column == Columns.COL_STATUS:
      return tvImpl.EpisodeRenameItem.typeStr(self.raw.matchType())
    elif column == Columns.COL_FILE_SIZE:
      if self.raw.matchType() != tvImpl.EpisodeRenameItem.MISSING_OLD:
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
      model.dataChanged.emit(index.parent(), index.parent())
      ret = True
    return ret

  def canCheck(self):
    return self.raw.canMove

  def checkState(self):
    return QtCore.Qt.Checked if self.canCheck() and self.raw.performMove else QtCore.Qt.Unchecked

  def setCheckState(self, cs):    
    self.raw.performMove = cs == QtCore.Qt.Checked

# --------------------------------------------------------------------------------------------------------------------
class TvModel(QtCore.QAbstractItemModel, workBench.BaseWorkBenchModel):
  """ 
  Represents 0 or more tv seasons. Each folder (season) contains a collection of moveItemCandiates. 
  At the moment folder can not be nested, but it is foreseeable that this this would be handy in the future.
  """
  workBenchChangedSignal = QtCore.pyqtSignal(bool)
  beginUpdateSignal = QtCore.pyqtSignal()
  endUpdateSignal = QtCore.pyqtSignal()  
  
  ALL_ACTIONS = (workBench.BaseWorkBenchModel.ACTION_DELETE,
                 workBench.BaseWorkBenchModel.ACTION_LAUNCH,
                 workBench.BaseWorkBenchModel.ACTION_OPEN,
                 workBench.BaseWorkBenchModel.ACTION_EPISODE,
                 workBench.BaseWorkBenchModel.ACTION_SEASON)

  def __init__(self, parent=None):
    super(QtCore.QAbstractItemModel, self).__init__(parent)
    super(workBench.BaseWorkBenchModel, self).__init__()
    self._seasons = []
    self.rootItem = None
    self._bulkProcessing = False
    self.clear()
    #self._view = parent # hack

  def columnCount(self, parent):
    return Columns.NUM_COLS
  
  def getFile(self, index):
    if not index.isValid():
      return None

    item = index.internalPointer()
    ret = ""
    if item.isMoveItemCandidate():
      ret = item.raw.filename 
    return ret
  
  def getFolder(self, index):
    if not index.isValid():
      return None

    item = index.internalPointer()
    ret = ""
    if item.isMoveItemCandidate():
      ret = fileHelper.FileHelper.dirname(item.raw.filename)
    else:
      ret = item.raw.inputFolder
    return ret
  
  def getDeleteItem(self, index):
    if not index.isValid():
      return None

    item = index.internalPointer()
    ret = ""
    if item.isMoveItemCandidate():
      ret = item.raw.filename
    else:
      ret = item.raw.inputFolder
    return ret
  
  def getAvailableActions(self, index):
    canEditEp = False
    if index.isValid():
      item = index.internalPointer()
      moveItemCandidateData, isMoveItemCandidate = self.data(index, RAW_DATA_ROLE)
      #filthy. check if parent has season info
      canEditEp = (isMoveItemCandidate and moveItemCandidateData.canEdit and 
                   True) #bool(self.data(index.parent(), RAW_DATA_ROLE)[0].info.matches))
    canLaunch = bool(self.getFile(index))
    canOpen = bool(self.getFolder(index))
    canDelete = bool(self.getDeleteItem(index))
    
    ret = {}
    ret[workBench.BaseWorkBenchModel.ACTION_EPISODE] = canEditEp
    ret[workBench.BaseWorkBenchModel.ACTION_SEASON] = canOpen
    ret[workBench.BaseWorkBenchModel.ACTION_OPEN] = canOpen
    ret[workBench.BaseWorkBenchModel.ACTION_LAUNCH] = canLaunch
    ret[workBench.BaseWorkBenchModel.ACTION_DELETE] = canDelete
    return ret

  def data(self, index, role):
    if not index.isValid():
      return None

    item = index.internalPointer()
    if role == RAW_DATA_ROLE:
      return (copy.copy(item.raw), item.isMoveItemCandidate()) #wow. this is confusing as hell..

    if role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      return item.checkState()
    else:
      return item.data(index, role)
 
  def setData(self, index, value, role):
    if not index.isValid():
      return False
    
    item = index.internalPointer()
    ret = item.setData(self, index, value, role)
    
    if ret and not self._bulkProcessing:   
      self._emitWorkBenchChanged()
    return ret

  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags

    item = index.internalPointer()

    f = QtCore.Qt.ItemIsSelectable
    if item.canCheck() or index.column() == Columns.COL_OLD_NAME:
      f |= QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsTristate
    if item.canCheck() or not item.isMoveItemCandidate() or item.raw.canEdit:
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
    utils.verifyType(s, tvImpl.Season)
    #check if already in list
    self.beginInsertRows(QtCore.QModelIndex(), len(self._seasons), len(self._seasons))
    ti = ContainerItem(s, self.rootItem)
    self.rootItem.appendChild(ti)
    for mi in s.episodeMoveItems:
      ti.appendChild(LeafItem(mi, ti))
    self._seasons.append(s)
    self.endInsertRows()     
    if not self._bulkProcessing:
      self._emitWorkBenchChanged()    

  def clear(self):
    self.beginResetModel()
    self._seasons = []
    self.rootItem = ContainerItem(("",))  
    self.endResetModel()
    if not self._bulkProcessing:
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
        
  def delete(self, index):
    if not index.isValid():
      return
    
    oldCheckedState = self.overallCheckedState()
    row = index.row()
    item = index.internalPointer()
    if item.isSeason():
      self.beginRemoveRows(index.parent(), row, row)
      self.rootItem.childItems.pop(row)
      self._seasons.pop(row)
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