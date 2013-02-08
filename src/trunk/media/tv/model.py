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

  def append_child(self, item):
    self.child_items.append(item)

  def child(self, row):
    return self.child_items[row]

  def child_count(self):
    return len(self.child_items)

  def parent(self):
    return self.parent

  def row(self):
    if self.parent:
      return self.parent.child_items.index(self)
    return 0

  def is_season(self):
    return isinstance(self.raw, tv_types.Season)

  def is_episode(self):
    return isinstance(self.raw, tv_types.EpisodeRenameItem)
  
  def set_data(self, model, index, value, role):
    raise NotImplementedError("BaseItem.set_data not implemented")

  def data(self, index, role=QtCore.Qt.DisplayRole):
    raise NotImplementedError("BaseItem.data not implemented")

  def can_check(self):
    raise NotImplementedError("BaseItem.can_check not implemented")

  def check_state(self):
    raise NotImplementedError("BaseItem.check_state not implemented")

  def set_check_state(self, checked_state):
    raise NotImplementedError("BaseItem.set_check_state not implemented")

  def can_edit(self):
    return False

# --------------------------------------------------------------------------------------------------------------------
class ContainerItem(BaseItem):
  """ Individual item in the workbench model. The item may represent a season or a moveItemCandidate. """ 
  def __init__(self, raw=None, parent=None):
    super(ContainerItem, self).__init__(raw, parent)
    
  def set_data(self, model, index, value, role):
    if not index.isValid():
      ret = False
    
    if role == RAW_DATA_ROLE:
      model.beginRemoveRows(index, 0, self.child_count() - 1)
      self.raw = value
      self.child_items = []
      for move_item in self.raw.episode_move_items:
        self.append_child(LeafItem(move_item, self))
      model.endRemoveRows()
      model.beginInsertRows(index, 0, self.child_count() - 1)
      #fix the check boxes
      for j in range(len(self.child_items)):
        idx = model.index(j, Columns.COL_NEW_NAME, index)
      model.endInsertRows()
      model.dataChanged.emit(index.sibling(index.row(), 0), index.sibling(index.row(), Columns.NUM_COLS-1))
      ret = True
    elif role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      self.set_check_state(value)
      model.dataChanged.emit(index, index)
      #HACK: shouldn't need this right?
      for child in self.child_items:
        child.set_check_state(value)
        changedIndex = index.child(Columns.COL_OLD_NAME, child.row())
        model.dataChanged.emit(changedIndex, changedIndex)
      ret = True
    return ret  

  def data(self, index, role=QtCore.Qt.DisplayRole):
    if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole, QtCore.Qt.ForegroundRole):
      return None

    is_unresolved = self.raw.info.season_num == tv_types.UNRESOLVED_KEY
    if role == QtCore.Qt.ForegroundRole and is_unresolved:
      return QtGui.QBrush(QtCore.Qt.red)      
    elif index.column() == Columns.COL_OLD_NAME:
      if role == QtCore.Qt.ToolTipRole:
        return "Folder: {}".format(self.raw.input_folder)
      else:
        return str(self.raw) if not is_unresolved else "Unknown"

  def can_check(self):
    return any(c.can_check() for c in self.child_items)

  def check_state(self):
    checked_state = None
    checked_items = [i.check_state() == QtCore.Qt.Checked for i in self.child_items if i.can_check()]
    if not checked_items or all(not is_checked for is_checked in checked_items):
      checked_state = QtCore.Qt.Unchecked
    elif all(checked_items):
      checked_state = QtCore.Qt.Checked
    else:
      checked_state = QtCore.Qt.PartiallyChecked
    return checked_state

  def set_check_state(self, checked_state):
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
    if role == QtCore.Qt.ForegroundRole:
      if self.raw.match_type() == tv_types.EpisodeRenameItem.MISSING_NEW:
        return QtGui.QBrush(QtCore.Qt.red)       
      elif self.raw.match_type() == tv_types.EpisodeRenameItem.MISSING_OLD:
        return QtGui.QBrush(QtCore.Qt.gray)       
    if column == Columns.COL_OLD_NAME:
      if role == QtCore.Qt.ToolTipRole:
        return self.raw.filename
      else:
        return file_helper.FileHelper.basename(self.raw.filename)
    elif column == Columns.COL_NEW_NUM:
      if self.raw.info.ep_num == tv_types.UNRESOLVED_KEY:
        return None
      else:
        return self.raw.info.ep_num
    elif column == Columns.COL_NEW_NAME:
      return self.raw.info.ep_name
    elif column == Columns.COL_STATUS:
      return tv_types.EpisodeRenameItem.type_str(self.raw.match_type())
    elif column == Columns.COL_FILE_SIZE:
      if self.raw.match_type() != tv_types.EpisodeRenameItem.MISSING_OLD:
        return utils.bytes_to_string(self.raw.file_size) 
    return None
  
  def set_data(self, model, index, value, role):
    if not index.isValid():
      return False
    ret = False

    if role == RAW_DATA_ROLE:
      parent_item = self.parent
      parentIndex = index.parent()
      utils.verify(parent_item.is_season(), "Not a Season")

      model.beginRemoveRows(parentIndex, 0, parent_item.child_count() - 1)
      parent_item.raw.set_episode_for_filename(value, self.raw.filename)
      parent_item.child_items = []
      for move_item in parent_item.raw.episode_move_items:
        parent_item.append_child(LeafItem(move_item, parent_item))
      model.endRemoveRows()
      ret = True
    elif role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      self.set_check_state(value)
      model.dataChanged.emit(index, index)
      #model.dataChanged.emit(index.parent(), index.parent())
      ret = True
    return ret

  def can_check(self):
    return self.raw.can_move

  def check_state(self):
    checked_state = None
    if self.can_check():
      checked_state = QtCore.Qt.Checked if self.raw.perform_move else QtCore.Qt.Unchecked
    return checked_state

  def set_check_state(self, checked_state):    
    self.raw.perform_move = checked_state == QtCore.Qt.Checked

  def can_edit(self):
    return bool(self.raw.filename)

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
  
  def get_file(self, index):
    if not index.isValid():
      return None

    item = self._get_item(index)
    ret = ""
    if item.is_episode():
      ret = item.raw.filename 
    return ret
  
  def get_folder(self, index):
    if not index.isValid():
      return None

    item = self._get_item(index)
    ret = ""
    if item.is_episode():
      ret = file_helper.FileHelper.dirname(item.raw.filename)
    else:
      ret = item.raw.input_folder
    return ret
  
  def get_delete_item(self, index):
    if not index.isValid():
      return None

    item = self._get_item(index)
    ret = ""
    if item.is_episode():
      ret = item.raw.filename
    else:
      ret = item.raw.input_folder
    return ret
  
  def can_edit(self, index):
    if not index.isValid():
      return False
    return self._get_item(index).can_edit()
  
  def get_rename_item(self, index):
    if not index.isValid():
      return None
    item = self._get_item(index)
    return item.raw if item.is_episode() and item.can_check() else None
  
  def get_available_actions(self, index):
    canEditEp = self.can_edit(index)
    canLaunch = bool(self.get_file(index))
    canOpen = bool(self.get_folder(index))
    canDelete = bool(self.get_delete_item(index))
    
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

    item = self._get_item(index)
    if role == RAW_DATA_ROLE:
      return (copy.copy(item.raw), item.is_episode()) #wow. this is confusing as hell..

    if role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      return item.check_state()
    else:
      return item.data(index, role)
 
  def setData(self, index, value, role):
    if not index.isValid():
      return False
    
    item = self._get_item(index)
    ret = item.set_data(self, index, value, role)
    
    if ret and not self._bulkProcessing:   
      self._emit_workbench_changed()
    return ret

  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags

    item = self._get_item(index)

    f = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
    if item.can_check() and index.column() == Columns.COL_OLD_NAME:
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

    child_item = self._get_item(index)
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

    return parent.child_count()

  def add_item(self, season):
    #utils.verify_type(s, tv_types.Season)
    #check if already in list
    rowCount = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), rowCount, rowCount)
    season_item = ContainerItem(season, self.rootItem)
    self.rootItem.append_child(season_item)
    for move_item in season.episode_move_items:
      season_item.append_child(LeafItem(move_item, season_item))
    self.endInsertRows()     
    if not self._bulkProcessing:
      self._emit_workbench_changed()    

  def clear(self):
    self.beginResetModel()
    self.rootItem = ContainerItem(("",))  
    self.endResetModel()
    if not self._bulkProcessing:
      self._emit_workbench_changed()    

  def items(self):
    ret = []
    for seasonItem in [self.rootItem.child(i) for i in range(self.rootItem.child_count())]:
      for epItem in [seasonItem.child(i) for i in range(seasonItem.child_count())]:
        if epItem.check_state() == QtCore.Qt.Checked:
          ret.append(epItem.raw)
    return ret

  def overall_checked_state(self):
    filteredItems = [i for i in self.rootItem.child_items if i.can_check()]
    if not filteredItems:
      return None

    ret = QtCore.Qt.PartiallyChecked
    if all(i.check_state() == QtCore.Qt.Checked for i in filteredItems):
      ret = QtCore.Qt.Checked 
    elif all(i.check_state() == QtCore.Qt.Unchecked for i in filteredItems):
      ret = QtCore.Qt.Unchecked 
    return ret

  def set_overall_checked_state(self, is_checked):
    #utils.verify_type(is_checked, bool)
    self.begin_update()
    checked_state = QtCore.Qt.Checked if is_checked else QtCore.Qt.Unchecked
    for i in range(self.rootItem.child_count()):
      idx = self.index(i, Columns.COL_OLD_NAME, QtCore.QModelIndex())
      self.setData(idx, checked_state, QtCore.Qt.CheckStateRole)
    self.end_update()
    self._emit_workbench_changed()

  def _has_moveable_items(self):
    return any(self.rootItem.child(i).check_state() != QtCore.Qt.Unchecked for i in range(self.rootItem.child_count()))

  def _emit_workbench_changed(self):
    has_items = self._has_moveable_items()
    self.workbench_changed_signal.emit(has_items)

  def begin_update(self):
    self._bulkProcessing = True
    self.begin_update_signal.emit()
    
  def end_update(self):
    self._bulkProcessing = False
    self.end_update_signal.emit()
    
  def _get_item(self, index):
    return index.internalPointer()
        
  def delete(self, index):
    if not index.isValid():
      return
    
    old_checked_state = self.overall_checked_state()
    row = index.row()
    item = self._get_item(index)
    if item.is_season():
      self.beginRemoveRows(index.parent(), row, row)
      self.rootItem.child_items.pop(row)
      self.endRemoveRows()
    else:
      parent_item = item.parent
      self.beginRemoveRows(index.parent(), 0, parent_item.child_count() - 1)
      parent_item.child_items = []
      parent_item.raw.remove_source_file(item.raw.filename) 
      self.endRemoveRows()

      self.beginInsertRows(index.parent(), 0, len(parent_item.raw.episode_move_items) - 1)
      for move_item in parent_item.raw.episode_move_items:
        parent_item.append_child(LeafItem(move_item, parent_item))
      self.endInsertRows()
      
    new_checked_state = self.overall_checked_state()
    if old_checked_state != new_checked_state:
      self._emit_workbench_changed()
      