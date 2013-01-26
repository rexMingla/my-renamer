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

import episode
import moveItemCandidate
import season
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
    if ep.matchType() == moveItemCandidate.MoveItemCandidate.MISSING_OLD:
      return None

    if index.column() == Columns.COL_NEW_NAME:
      comboBox = QtGui.QComboBox(parent)
      
      comboBox.addItem("Not set", episode.UNRESOLVED_KEY)
      comboBox.insertSeparator(1)
      # fill it

      moveItemCandidates = copy.copy(season.moveItemCandidates)
      moveItemCandidates = sorted(moveItemCandidates, key=lambda item: item.destination.epNum)
      for mi in moveItemCandidates:
        if mi.destination.epName != episode.UNRESOLVED_NAME:
          displayName = "{}: {}".format(mi.destination.epNum, mi.destination.epName)
          comboBox.addItem(displayName, mi.destination.epNum)
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
    if ep.matchType() == moveItemCandidate.MoveItemCandidate.MISSING_OLD:
      return None

    if index.column() == Columns.COL_NEW_NAME:
      editor.setCurrentIndex(editor.findData(ep.source.epNum))
 
  def setModelData(self, editor, model, index):
    model = index.model()
    item, isMoveCandidate = model.data(index, RAW_DATA_ROLE)
    if not isMoveCandidate:
      return None

    season, ep = model.data(index.parent(), RAW_DATA_ROLE)[0], item
    if ep.matchType() == moveItemCandidate.MoveItemCandidate.MISSING_OLD:
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
      elif column == Columns.COL_FILE_SIZE:
        if self.raw.matchType() != moveItemCandidate.MoveItemCandidate.MISSING_OLD:
          return utils.bytesToString(self.raw.source.fileSize) 
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
      return any(c.canCheck() for c in self.childItems)

  def checkState(self):
    cs = QtCore.Qt.Checked
    if self.isMoveItemCandidate():
      if not self.raw.performMove:
        cs = QtCore.Qt.Unchecked
    elif self.isSeason():
      checkedItems = [c.checkState() == QtCore.Qt.Checked for c in self.childItems if c.canCheck()]
      if not checkedItems or all(not c for c in checkedItems):
        cs = QtCore.Qt.Unchecked
      elif all(checkedItems):
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
    self.rootItem = TreeItem(("",))
    self._bulkProcessing = False
    #self._view = parent # hack

  def columnCount(self, parent):
    return Columns.NUM_COLS
  
  def getFile(self, index):
    if not index.isValid():
      return None

    item = index.internalPointer()
    ret = ""
    if item.isMoveItemCandidate():
      ret = item.raw.source.filename 
    return ret
  
  def getFolder(self, index):
    if not index.isValid():
      return None

    item = index.internalPointer()
    ret = ""
    if item.isMoveItemCandidate():
      ret = fileHelper.FileHelper.dirname(item.raw.source.filename)
    else:
      ret = item.raw.inputFolder
    return ret
  
  def getDeleteItem(self, index):
    if not index.isValid():
      return None

    item = index.internalPointer()
    ret = ""
    if item.isMoveItemCandidate():
      ret = item.raw.source.filename
    else:
      ret = item.raw.inputFolder
    return ret
  
  def getAvailableActions(self, index):
    canEditEp = False
    if index.isValid():      
      moveItemCandidateData, isMoveItemCandidate = self.data(index, RAW_DATA_ROLE)
      #filthy. check if parent has season info
      canEditEp = (isMoveItemCandidate and moveItemCandidateData.canEdit and 
                  bool(self.data(index.parent(), RAW_DATA_ROLE)[0].destination.matches))
    canLaunch = bool(self.getFile(index))
    canOpen = bool(self.getFolder(index))
    canDelete = bool(self.getDeleteItem(index))
    
    ret = {}
    ret[workBench.BaseWorkBenchModel.ACTION_EPISODE] = canEditEp
    ret[workBench.BaseWorkBenchModel.ACTION_SEASON] = canLaunch
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
        #self.beginInsertRows(parentIndex, 0, parentItem.childCount() - 1)
        #fix the check boxes
        #for j in range(len(parentItem.childItems)):
        #  idx = self.index(j, Columns.COL_NEW_NAME, parentIndex)
        #  #self._view.closePersistentEditor(idx)
        #  #if parentItem.canCheck() and parentItem.childItems[j].raw.source.filename: #more filth...
        #  #  self._view.openPersistentEditor(idx)
        #self.endInsertRows()            
        ret = True
      else:
        self.beginRemoveRows(index, 0, item.childCount() - 1)
        item.raw = value
        item.childItems = []
        for mi in item.raw.moveItemCandidates:
          item.appendChild(TreeItem(mi, item))
        self.endRemoveRows()
        self.beginInsertRows(index, 0, item.childCount() - 1)
        #fix the check boxes
        for j in range(len(item.childItems)):
          idx = self.index(j, Columns.COL_NEW_NAME, index)
          #self._view.closePersistentEditor(idx)
          #if item.canCheck() and item.childItems[j].raw.source.filename: #more filth...
          #  self._view.openPersistentEditor(idx)
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
    if not self._bulkProcessing:   
      self._emitWorkBenchChanged()
    return ret

  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags

    item = index.internalPointer()

    f = QtCore.Qt.ItemIsSelectable# | QtCore.Qt.ItemIsEditable
    if item.canCheck():
      f |= QtCore.Qt.ItemIsEnabled 
      if index.column() == Columns.COL_OLD_NAME:
        f |= QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsTristate
      #elif index.column() == Columns.COL_NEW_NAME and item.isMoveItemCandidate() and item.raw.canEdit and \
      #  bool(self.data(index.parent(), RAW_DATA_ROLE)[0].destination.matches): #filth....
      #  f |= QtCore.Qt.ItemIsEditable
    elif not item.isMoveItemCandidate() or item.raw.canEdit:
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
    utils.verifyType(s, season.Season)
    #check if already in list
    self.beginInsertRows(QtCore.QModelIndex(), len(self._seasons), len(self._seasons))
    ti = TreeItem(s, self.rootItem)
    self.rootItem.appendChild(ti)
    for mi in s.moveItemCandidates:
      ti.appendChild(TreeItem(mi, ti))
    self._seasons.append(s)
    self.endInsertRows()     
    if not self._bulkProcessing:
      self._emitWorkBenchChanged()    

  def clear(self):
    self.beginResetModel()
    self._seasons = []
    self.rootItem = TreeItem(("",))  
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
    
  def _oldUpdateStuff(self):
    for i in range(self.rootItem.childCount()):
      parent = self.index(i, Columns.COL_OLD_NAME, QtCore.QModelIndex())
      parentItem = self.rootItem.childItems[i]
      for j in range(len(parentItem.childItems)):
        index = self.index(j, Columns.COL_NEW_NAME, parent)
        #self._view.closePersistentEditor(index)
        #if parentItem.canCheck() and parentItem.childItems[j].raw.source.filename: #more filth...
        #  self._view.openPersistentEditor(index) 
        
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
      parentItem.raw.removeSourceFile(item.raw.source.filename) 
      self.endRemoveRows()

      self.beginInsertRows(index.parent(), 0, len(parentItem.raw.moveItemCandidates) - 1)
      for mi in parentItem.raw.moveItemCandidates:
        parentItem.appendChild(TreeItem(mi, parentItem))
      self.endInsertRows()
      
    newCheckedState = self.overallCheckedState()
    if oldCheckedState != newCheckedState:
      self._emitWorkBenchChanged()