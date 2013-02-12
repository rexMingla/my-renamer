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

from media.base import model as base_model
from common import file_helper
from common import utils

from media.tv import types as tv_types

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
  def __init__(self, raw=None, parent=None):
    super(BaseItem, self).__init__()
    self.parent = parent
    self.raw = raw
    self.child_items = []

  def appendChild(self, item):
    self.child_items.append(item)

  def child(self, row):
    return self.child_items[row]

  def childCount(self):
    return len(self.child_items)

  def parent(self):
    return self.parent

  def row(self):
    if self.parent:
      return self.parent.child_items.index(self)
    return 0

  def isSeason(self):
    return isinstance(self.raw, tv_types.Season)

  def isEpisode(self):
    return isinstance(self.raw, tv_types.EpisodeRenameItem)

  def setData(self, model, index, value, role):
    raise NotImplementedError("BaseItem.setData not implemented")

  def data(self, index, role=QtCore.Qt.DisplayRole):
    raise NotImplementedError("BaseItem.data not implemented")

  def canCheck(self):
    raise NotImplementedError("BaseItem.canCheck not implemented")

  def checkState(self):
    raise NotImplementedError("BaseItem.checkState not implemented")

  def setCheckState(self, checked_state):
    raise NotImplementedError("BaseItem.setCheckState not implemented")

  def canEdit(self):
    return False

# --------------------------------------------------------------------------------------------------------------------
class ContainerItem(BaseItem):
  """ Individual item in the workbench model. The item may represent a season or a moveItemCandidate. """
  def __init__(self, raw=None, parent=None):
    super(ContainerItem, self).__init__(raw, parent)

  def setData(self, model, index, value, role):
    if not index.isValid():
      ret = False

    if role == RAW_DATA_ROLE:
      model.beginRemoveRows(index, 0, self.childCount() - 1)
      self.raw = value
      self.child_items = []
      for move_item in self.raw.episode_move_items:
        self.appendChild(LeafItem(move_item, self))
      model.endRemoveRows()
      model.beginInsertRows(index, 0, self.childCount() - 1)
      #fix the check boxes
      for j in range(len(self.child_items)):
        idx = model.index(j, Columns.COL_NEW_NAME, index)
      model.endInsertRows()
      model.dataChanged.emit(index.sibling(index.row(), 0), index.sibling(index.row(), Columns.NUM_COLS-1))
      ret = True
    elif role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      self.setCheckState(value)
      model.dataChanged.emit(index, index)
      #HACK: shouldn't need this right?
      for child in self.child_items:
        child.setCheckState(value)
        changedIndex = index.child(Columns.COL_OLD_NAME, child.row())
        model.dataChanged.emit(changedIndex, changedIndex)
      ret = True
    return ret

  def data(self, index, role=QtCore.Qt.DisplayRole):
    if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole, QtCore.Qt.ForegroundRole):
      return None

    is_unresolved = self.raw.getStatus() == tv_types.Season.SEASON_NOT_FOUND
    if role == QtCore.Qt.ForegroundRole and is_unresolved:
      return QtGui.QBrush(QtCore.Qt.red)
    elif index.column() == Columns.COL_OLD_NAME:
      if role == QtCore.Qt.ToolTipRole:
        return "Folder: {}".format(self.raw.input_folder)
      else:
        return str(self.raw)

  def canCheck(self):
    return self.raw.getStatus() != tv_types.Season.SEASON_NOT_FOUND and any(c.canCheck() for c in self.child_items)

  def checkState(self):
    if not self.canCheck():
      return None
    checked_state = QtCore.Qt.PartiallyChecked
    checked_items = [i.checkState() == QtCore.Qt.Checked for i in self.child_items if i.canCheck()]
    if not checked_items or all(not isChecked for isChecked in checked_items):
      checked_state = QtCore.Qt.Unchecked
    elif all(checked_items):
      checked_state = QtCore.Qt.Checked
    return checked_state

  def setCheckState(self, checked_state):
    pass

# --------------------------------------------------------------------------------------------------------------------
class LeafItem(BaseItem):
  """ Individual item in the workbench model. The item may represent a season or a moveItemCandidate. """
  def __init__(self, raw=None, parent=None):
    super(LeafItem, self).__init__(raw, parent)

  def data(self, index, role=QtCore.Qt.DisplayRole):
    if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole, QtCore.Qt.ForegroundRole):
      return None

    column = index.column()
    info = self.raw.getInfo()
    if role == QtCore.Qt.ForegroundRole:
      if self.raw.getStatus() == tv_types.EpisodeRenameItem.MISSING_NEW:
        return QtGui.QBrush(QtCore.Qt.red)
      elif self.raw.getStatus() == tv_types.EpisodeRenameItem.MISSING_OLD:
        return QtGui.QBrush(QtCore.Qt.gray)
    if column == Columns.COL_OLD_NAME:
      if role == QtCore.Qt.ToolTipRole:
        return self.raw.filename
      else:
        return file_helper.FileHelper.basename(self.raw.filename)
    elif column == Columns.COL_NEW_NUM:
      if info.ep_num == tv_types.UNRESOLVED_KEY:
        return None
      else:
        return info.ep_num
    elif column == Columns.COL_NEW_NAME:
      return info.ep_name
    elif column == Columns.COL_STATUS:
      return self.raw.getStatus()
    elif column == Columns.COL_FILE_SIZE:
      if self.raw.canEdit():
        return utils.bytesToString(self.raw.getFileSize())
    return None

  def setData(self, model, index, value, role):
    if not index.isValid():
      return False
    ret = False

    if role == RAW_DATA_ROLE:
      parent_item = self.parent
      parentIndex = index.parent()
      utils.verify(parent_item.isSeason(), "Not a Season")

      model.beginRemoveRows(parentIndex, 0, parent_item.childCount() - 1)
      parent_item.raw.setEpisodeForFilename(value, self.raw.filename)
      parent_item.child_items = []
      for move_item in parent_item.raw.episode_move_items:
        parent_item.appendChild(LeafItem(move_item, parent_item))
      model.endRemoveRows()
      ret = True
    elif role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      self.setCheckState(value)
      model.dataChanged.emit(index, index)
      #model.dataChanged.emit(index.parent(), index.parent())
      ret = True
    return ret

  def canCheck(self):
    return self.raw.isValid()

  def checkState(self):
    checked_state = None
    if self.canCheck():
      checked_state = QtCore.Qt.Checked if self.raw.is_enabled else QtCore.Qt.Unchecked
    return checked_state

  def setCheckState(self, checked_state):
    self.raw.is_enabled = checked_state == QtCore.Qt.Checked

  def canEdit(self):
    return self.raw.canEdit() and self.parent.canCheck()

# --------------------------------------------------------------------------------------------------------------------
class TvModel(QtCore.QAbstractItemModel, base_model.BaseWorkBenchModel):
  """
  Represents 0 or more tv seasons. Each folder (season) contains a collection of moveItemCandiates.
  At the moment folder can not be nested, but it is foreseeable that this this would be handy in the future.
  """
  workbench_changed_signal = QtCore.pyqtSignal(bool)
  begin_update_signal = QtCore.pyqtSignal()
  end_update_signal = QtCore.pyqtSignal()

  ALL_ACTIONS = (base_model.BaseWorkBenchModel.ACTION_DELETE,
                 base_model.BaseWorkBenchModel.ACTION_LAUNCH,
                 base_model.BaseWorkBenchModel.ACTION_OPEN,
                 base_model.BaseWorkBenchModel.ACTION_EPISODE,
                 base_model.BaseWorkBenchModel.ACTION_SEASON)

  def __init__(self, parent=None):
    super(QtCore.QAbstractItemModel, self).__init__(parent)
    super(base_model.BaseWorkBenchModel, self).__init__()
    self.rootItem = None
    self._bulkProcessing = False
    self.clear()
    #self._view = parent # hack

  def columnCount(self, parent):
    return Columns.NUM_COLS

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
      self._emitWorkbenchChanged()
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

    child_item = parent.child(row)
    if child_item:
      return self.createIndex(row, column, child_item)
    else:
      return QtCore.QModelIndex()

  def parent(self, index):
    if not index.isValid():
      return QtCore.QModelIndex()

    child_item = self._getItem(index)
    parent = child_item.parent

    if parent == self.rootItem:
      return QtCore.QModelIndex()

    return self.createIndex(parent.row(), 0, parent)

  def rowCount(self, parent):
    if parent.column() > 0:
      return 0

    if not parent.isValid():
      parent = self.rootItem
    else:
      parent = parent.internalPointer()

    return parent.childCount()

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
      ret = item.raw.input_folder
    return ret

  def getDeleteItem(self, index):
    if not index.isValid():
      return None

    item = self._getItem(index)
    ret = ""
    if item.isEpisode():
      ret = item.raw.filename
    else:
      ret = item.raw.input_folder
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
    can_open = bool(self.getFolder(index))
    
    ret = {}
    ret[base_model.BaseWorkBenchModel.ACTION_EPISODE] = self.canEdit(index)
    ret[base_model.BaseWorkBenchModel.ACTION_SEASON] = can_open
    ret[base_model.BaseWorkBenchModel.ACTION_OPEN] = can_open
    ret[base_model.BaseWorkBenchModel.ACTION_LAUNCH] = bool(self.getFile(index))
    ret[base_model.BaseWorkBenchModel.ACTION_DELETE] = bool(self.getDeleteItem(index))
    return ret

  def addItem(self, season):
    #utils.verifyType(s, tv_types.Season)
    #check if already in list
    rowCount = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), rowCount, rowCount)
    season_item = ContainerItem(season, self.rootItem)
    self.rootItem.appendChild(season_item)
    for move_item in season.episode_move_items:
      season_item.appendChild(LeafItem(move_item, season_item))
    self.endInsertRows()
    if not self._bulkProcessing:
      self._emitWorkbenchChanged()

  def clear(self):
    self.beginResetModel()
    self.rootItem = ContainerItem(("",))
    self.endResetModel()
    if not self._bulkProcessing:
      self._emitWorkbenchChanged()

  def items(self):
    ret = []
    for seasonItem in [self.rootItem.child(i) for i in range(self.rootItem.childCount())]:
      for epItem in [seasonItem.child(i) for i in range(seasonItem.childCount())]:
        if epItem.checkState() == QtCore.Qt.Checked:
          ret.append(epItem.raw)
    return ret

  def overallCheckedState(self):
    filteredItems = [i for i in self.rootItem.child_items if i.canCheck()]
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
    checked_state = QtCore.Qt.Checked if isChecked else QtCore.Qt.Unchecked
    for i in range(self.rootItem.childCount()):
      idx = self.index(i, Columns.COL_OLD_NAME, QtCore.QModelIndex())
      self.setData(idx, checked_state, QtCore.Qt.CheckStateRole)
    self.endUpdate()
    self._emitWorkbenchChanged()

  def _hasMoveableItems(self):
    return any(self.rootItem.child(i).checkState() != QtCore.Qt.Unchecked for i in range(self.rootItem.childCount()))

  def _emitWorkbenchChanged(self):
    has_items = self._hasMoveableItems()
    self.workbench_changed_signal.emit(has_items)

  def beginUpdate(self):
    self._bulkProcessing = True
    self.begin_update_signal.emit()

  def endUpdate(self):
    self._bulkProcessing = False
    self.end_update_signal.emit()

  def _getItem(self, index):
    return index.internalPointer()

  def delete(self, index):
    if not index.isValid():
      return

    old_checked_state = self.overallCheckedState()
    row = index.row()
    item = self._getItem(index)
    if item.isSeason():
      self.beginRemoveRows(index.parent(), row, row)
      self.rootItem.child_items.pop(row)
      self.endRemoveRows()
    else:
      parent_item = item.parent
      self.beginRemoveRows(index.parent(), 0, parent_item.childCount() - 1)
      parent_item.child_items = []
      parent_item.raw.removeSourceFile(item.raw.filename)
      self.endRemoveRows()

      self.beginInsertRows(index.parent(), 0, len(parent_item.raw.episode_move_items) - 1)
      for move_item in parent_item.raw.episode_move_items:
        parent_item.appendChild(LeafItem(move_item, parent_item))
      self.endInsertRows()

    new_checked_state = self.overallCheckedState()
    if old_checked_state != new_checked_state:
      self._emitWorkbenchChanged()

