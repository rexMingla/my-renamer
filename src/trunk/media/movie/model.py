#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Model and other classes pertaining to the set of tv seasons to be modified in the workbench
# --------------------------------------------------------------------------------------------------------------------
import copy

from PyQt4 import QtGui #needed before QtCore for pylint
from PyQt4 import QtCore

from common import file_helper
from common import utils
from media.base import model as base_model

# --------------------------------------------------------------------------------------------------------------------
class SortFilterModel(QtGui.QSortFilterProxyModel):
  def lessThan(self, left, right):
    if left.column() == Columns.COL_FILE_SIZE:
      left_data = self.sourceModel().data(left, RAW_DATA_ROLE).file_size 
      right_data = self.sourceModel().data(right, RAW_DATA_ROLE).file_size
      return left_data < right_data   
    else:
      left_data = self.sourceModel().data(left, QtCore.Qt.ToolTipRole) #use tooltip so that filename is col is full path
      right_data = self.sourceModel().data(right, QtCore.Qt.ToolTipRole) 
      return left_data < right_data   
    
# --------------------------------------------------------------------------------------------------------------------
class Columns:
  """ Columns used in workbench model. """
  COL_CHECK     = 0
  COL_OLD_NAME  = 1
  COL_NEW_NAME  = 2
  COL_YEAR      = 3
  COL_GENRE     = 4
  COL_STATUS    = 5
  COL_FILE_SIZE = 6
  COL_DISC      = 7
  COL_SERIES    = 8
  NUM_COLS      = 9

RAW_DATA_ROLE = QtCore.Qt.UserRole + 1

_MISSING_YEAR = "Missing Year"
_MISSING_GENRE = "Missing Genre"
_DUPLICATE = "Duplicate"
_OK = "Ok"

# --------------------------------------------------------------------------------------------------------------------
class MovieItem(object):
  def __init__(self, movie, index):
    super(MovieItem, self).__init__()
    #utils.verify_type(movie, movie_types.MovieRenameItem)
    self.movie = movie
    self.index = index
    self.want_to_move = True
    self.cached_status_text = "Unknown"
    self.duplicates = []
    
  def is_match(self, other):
    #utils.verify_type(other, MovieItem)
    return self.movie.file_exists() and self.movie.info == other.movie.info
      
# --------------------------------------------------------------------------------------------------------------------
class MovieModel(QtCore.QAbstractTableModel, base_model.BaseWorkBenchModel):
  """ 
  Represents 0 or more movies
  """
  workbench_changed_signal = QtCore.pyqtSignal(bool)
  begin_update_signal = QtCore.pyqtSignal()
  end_update_signal = QtCore.pyqtSignal() 
  
  ALL_ACTIONS = (base_model.BaseWorkBenchModel.ACTION_DELETE,
                 base_model.BaseWorkBenchModel.ACTION_LAUNCH,
                 base_model.BaseWorkBenchModel.ACTION_OPEN,
                 base_model.BaseWorkBenchModel.ACTION_MOVIE)  
  
  def __init__(self, parent=None):
    super(QtCore.QAbstractTableModel, self).__init__(parent)
    super(base_model.BaseWorkBenchModel, self).__init__()
    self._movies = []
    self._bulk_updating = False
    self._require_year = True
    self._require_genre = True
    self._flag_duplicates = True
    
  def get_file(self, index):
    item = self.get_rename_item(index)
    return item.filename if item else ""
  
  def get_folder(self, index):
    ret = self.get_file(index)
    if ret:
      ret = file_helper.FileHelper.dirname(ret)
    return ret
  
  def get_delete_item(self, index):
    return self.get_file(index)
  
  def get_rename_item(self, index):
    return self._movies[index.row()].movie if index.isValid() else None    
    
  def get_available_actions(self, index):
    has_index = index.isValid()
    
    ret = {}
    ret[base_model.BaseWorkBenchModel.ACTION_DELETE] = has_index
    ret[base_model.BaseWorkBenchModel.ACTION_LAUNCH] = has_index
    ret[base_model.BaseWorkBenchModel.ACTION_OPEN] = has_index
    ret[base_model.BaseWorkBenchModel.ACTION_MOVIE] = has_index
    return ret
    
  def columnCount(self, _parent):
    return Columns.NUM_COLS

  def data(self, index, role):
    if not index.isValid():
      return None
    
    if role not in (QtCore.Qt.ForegroundRole, 
                    QtCore.Qt.DisplayRole, 
                    QtCore.Qt.ToolTipRole, 
                    QtCore.Qt.CheckStateRole, 
                    RAW_DATA_ROLE) or \
      (role == QtCore.Qt.CheckStateRole and index.column() != Columns.COL_CHECK):
      return None
    
    item = self._movies[index.row()]    
    movie = item.movie
    info = movie.info
    if role == RAW_DATA_ROLE:
      return copy.copy(movie)
    
    col = index.column()
    if role == QtCore.Qt.ForegroundRole and not self._is_item_valid(item):
      return QtGui.QBrush(QtCore.Qt.red)      
    elif col == Columns.COL_CHECK:
      if role == QtCore.Qt.CheckStateRole:
        if self._perform_move_on_item(item): 
          return QtCore.Qt.Checked
        else:
          return QtCore.Qt.Unchecked
    elif col == Columns.COL_OLD_NAME:
      if role == QtCore.Qt.DisplayRole:
        return file_helper.FileHelper.basename(movie.filename)
      else:
        return movie.filename
    elif col == Columns.COL_NEW_NAME:
      return info.title
    elif col == Columns.COL_DISC:
      return info.part
    elif col == Columns.COL_STATUS:
      return item.cached_status_text
    elif col == Columns.COL_YEAR:
      return info.year
    elif col == Columns.COL_GENRE:
      return info.get_genre()
    elif col == Columns.COL_FILE_SIZE:
      return utils.bytes_to_string(movie.file_size) if movie.file_exists() else ""
    elif col == Columns.COL_SERIES:
      return info.series
       
  def setData(self, index, value, role):
    if not index.isValid() or role not in (QtCore.Qt.CheckStateRole, RAW_DATA_ROLE):
      return False
    
    if role == RAW_DATA_ROLE:
      #utils.verify_type(value, movie_types.MovieRenameItem)
      item = self._movies[index.row()]
      new_movie = copy.copy(value)
      if item.movie != new_movie:
        old_dups = item.duplicates
        item.movie = new_movie
        self._update_item_status(item)
        new_dups = item.duplicates
        for now_dup_index in (i for i in new_dups if not i in old_dups):
          self._update_item_status(self._movies[now_dup_index])
        for now_not_dup_index in (i for i in old_dups if not i in new_dups):
          self._update_item_status(self._movies[now_not_dup_index])
    elif role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_CHECK:
      item = self._movies[index.row()]
      item.want_to_move = value == QtCore.Qt.Checked
      self.dataChanged.emit(index, index)
    if not self._bulk_updating:
      self._emit_workbench_changed()
    return True
  
  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags
    
    item = self._movies[index.row()]
    flags = QtCore.Qt.ItemIsSelectable
    if self._is_item_valid(item) or index.column() != Columns.COL_CHECK:
      flags |= QtCore.Qt.ItemIsEnabled 
    if index.column() == Columns.COL_CHECK:
      flags |= QtCore.Qt.ItemIsUserCheckable
    return flags

  def headerData(self, section, orientation, role):
    if role != QtCore.Qt.DisplayRole or orientation == QtCore.Qt.Vertical:
      return
    
    if section == Columns.COL_DISC:
      return "Disc"
    elif section == Columns.COL_NEW_NAME:
      return "Title"
    elif section == Columns.COL_OLD_NAME:
      return "Filename"
    elif section == Columns.COL_STATUS:
      return "Status"
    elif section == Columns.COL_YEAR:
      return "Year"
    elif section == Columns.COL_GENRE:
      return "Genre"
    elif section == Columns.COL_FILE_SIZE:
      return "File Size"
    elif section == Columns.COL_SERIES:
      return "Series"

  def rowCount(self, _parent=None):
    return len(self._movies)
  
  def clear(self):
    self.beginResetModel()
    self._movies = []
    self.endResetModel()
    if not self._bulk_updating:
      self._emit_workbench_changed()    
  
  def add_item(self, movie):
    #utils.verify_type(m, movie_types.MovieRenameItem)
    #check if already in list
    count = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), count, count)
    item = MovieItem(movie, count)
    self._movies.append(item)
    self.endInsertRows()     
    if not self._bulk_updating:
      self._emit_workbench_changed()    
  
  def items(self):
    return [i.movie for i in self._movies if self._perform_move_on_item(i)]
  
  def _is_item_valid(self, item):
    return item.cached_status_text == _OK  or (item.cached_status_text == _DUPLICATE and not self._flag_duplicates)
  
  def _update_item_status(self, item):
    old_status_text = item.cached_status_text
    self._update_duplicates_for_item(item)
    self._update_item_status_text(item)
    new_status_text = item.cached_status_text
    if old_status_text != new_status_text:
      self.dataChanged.emit(self.index(item.index, 0), self.index(item.index, Columns.NUM_COLS))
      
  def _update_item_status_text(self, item):
    ret = ""
    if not file_helper.FileHelper.file_exists(item.movie.filename):
      ret = "File not found"
    elif item.duplicates:
      ret = _DUPLICATE
    elif self._require_year and not item.movie.info.year:
      ret = _MISSING_YEAR
    elif self._require_genre and not item.movie.info.genres:
      ret = _MISSING_GENRE
    else:
      ret = _OK
    item.cached_status_text = ret
    return ret  
    
  def _perform_move_on_item(self, item):
    return item.want_to_move and self._is_item_valid(item)
  
  def _update_duplicates_for_item(self, item):
    item.duplicates = []
    if item.movie.file_exists():
      item.duplicates = [m.index for m in self._movies if m.index != item.index and m.is_match(item)]
  
  def overall_checked_state(self):
    filtered = [m for m in self._movies if self._is_item_valid(m)]
    if not filtered:
      return None
    
    ret = QtCore.Qt.PartiallyChecked
    if all(self._perform_move_on_item(m) for m in filtered):
      ret = QtCore.Qt.Checked
    elif all(not self._perform_move_on_item(m) for m in filtered):
      ret = QtCore.Qt.Unchecked
    return ret
  
  def set_overall_checked_state(self, is_checked):
    #utils.verify_type(is_checked, bool)
    self.begin_update()
    check_state = QtCore.Qt.Checked
    if not is_checked:
      check_state = QtCore.Qt.Unchecked
    for i, _ in enumerate(self._movies):
      idx = self.index(i, Columns.COL_CHECK)
      self.setData(idx, check_state, QtCore.Qt.CheckStateRole) 
    self.end_update()
    self._emit_workbench_changed()
  
  def _has_moveable_items(self):
    return any(self._perform_move_on_item(m) for m in self._movies)

  def _emit_workbench_changed(self):
    has_items = self._has_moveable_items()
    self.workbench_changed_signal.emit(has_items)
    
  def _update_all_status_text(self):
    for movie in self._movies:
      self._update_item_status(movie)
    
  def begin_update(self):
    self._bulk_updating = True
    self.begin_update_signal.emit()
    
  def end_update(self):
    self._update_all_status_text()
    self._bulk_updating = False 
    self._emit_workbench_changed()
    self.end_update_signal.emit()
    
  def require_year_changed(self, require):
    if self._require_year != require:
      self._require_year = require
      self._update_all_status_text()
    
  def require_genre_changed(self, require):
    if self._require_genre != require:
      self._require_genre = require
      self._update_all_status_text()
      
  def flag_duplicate_changed(self, flag):
    if self._flag_duplicates != flag:
      self._flag_duplicates = flag
      self._update_all_status_text()
      
  def delete(self, index):
    if not index.isValid():
      return
    
    row = index.row()
    self.beginRemoveRows(QtCore.QModelIndex(), row, row)
    item = self._movies[row]
    self._movies.pop(row)
    for item in self._movies[row:]:
      item.index -= 1
    
    #update all duplicates as they may be pointing at the wrong rows
    for item in self._movies:
      if item.duplicates:
        self._update_item_status(item)
    self.endRemoveRows()
