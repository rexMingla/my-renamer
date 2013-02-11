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
    #utils.verifyType(movie, movie_types.MovieRenameItem)
    self.movie = movie
    self.index = index
    self.want_to_move = True
    self.cached_status_text = movie.status()
    self.duplicates = []

  def isMatch(self, other):
    #utils.verifyType(other, MovieItem)
    return self.movie.status() == self.movie.READY and self.movie.info == other.movie.info

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

  def getFile(self, index):
    item = self.getRenameItem(index)
    return item.filename if item else ""

  def getFolder(self, index):
    ret = self.getFile(index)
    if ret:
      ret = file_helper.FileHelper.dirname(ret)
    return ret

  def getDeleteItem(self, index):
    return self.getFile(index)

  def getRenameItem(self, index):
    return self._movies[index.row()].movie if index.isValid() else None

  def getAvailableActions(self, index):
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
    if role == QtCore.Qt.ForegroundRole and not self._isItemValid(item):
      return QtGui.QBrush(QtCore.Qt.red)
    elif col == Columns.COL_CHECK:
      if role == QtCore.Qt.CheckStateRole:
        if self._performMoveOnItem(item):
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
      return info.getGenre()
    elif col == Columns.COL_FILE_SIZE:
      return utils.bytesToString(movie.file_size) if movie.isReady() else ""
    elif col == Columns.COL_SERIES:
      return info.series

  def setData(self, index, value, role):
    if not index.isValid() or role not in (QtCore.Qt.CheckStateRole, RAW_DATA_ROLE):
      return False

    if role == RAW_DATA_ROLE:
      #utils.verifyType(value, movie_types.MovieRenameItem)
      item = self._movies[index.row()]
      new_movie = copy.copy(value)
      if item.movie != new_movie:
        old_dups = item.duplicates
        item.movie = new_movie
        self._updateItemStatus(item)
        new_dups = item.duplicates
        for now_dup_index in (i for i in new_dups if not i in old_dups):
          self._updateItemStatus(self._movies[now_dup_index])
        for now_not_dup_index in (i for i in old_dups if not i in new_dups):
          self._updateItemStatus(self._movies[now_not_dup_index])
    elif role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_CHECK:
      item = self._movies[index.row()]
      item.want_to_move = value == QtCore.Qt.Checked
      self.dataChanged.emit(index, index)
    if not self._bulk_updating:
      self._emitWorkbenchChanged()
    return True

  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags

    item = self._movies[index.row()]
    flags = QtCore.Qt.ItemIsSelectable
    if self._isItemValid(item) or index.column() != Columns.COL_CHECK:
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
      self._emitWorkbenchChanged()

  def addItem(self, movie):
    #utils.verifyType(m, movie_types.MovieRenameItem)
    #check if already in list
    count = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), count, count)
    item = MovieItem(movie, count)
    self._movies.append(item)
    self.endInsertRows()
    if not self._bulk_updating:
      self._emitWorkbenchChanged()

  def items(self):
    return [i.movie for i in self._movies if self._performMoveOnItem(i)]

  def _isItemValid(self, item):
    return item.cached_status_text == _OK  or (item.cached_status_text == _DUPLICATE and not self._flag_duplicates)

  def _updateItemStatus(self, item):
    old_status_text = item.cached_status_text
    self._updateDuplicatesForItem(item)
    self._updateItemStatusText(item)
    new_status_text = item.cached_status_text
    if old_status_text != new_status_text:
      self.dataChanged.emit(self.index(item.index, 0), self.index(item.index, Columns.NUM_COLS))

  def _updateItemStatusText(self, item):
    ret = ""
    if not file_helper.FileHelper.fileExists(item.movie.filename):
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

  def _performMoveOnItem(self, item):
    return item.want_to_move and self._isItemValid(item)

  def _updateDuplicatesForItem(self, item):
    item.duplicates = []
    if item.movie.isReady():
      item.duplicates = [m.index for m in self._movies if m.index != item.index and m.isMatch(item)]

  def overallCheckedState(self):
    filtered = [m for m in self._movies if self._isItemValid(m)]
    if not filtered:
      return None

    ret = QtCore.Qt.PartiallyChecked
    if all(self._performMoveOnItem(m) for m in filtered):
      ret = QtCore.Qt.Checked
    elif all(not self._performMoveOnItem(m) for m in filtered):
      ret = QtCore.Qt.Unchecked
    return ret

  def setOverallCheckedState(self, isChecked):
    #utils.verifyType(isChecked, bool)
    self.beginUpdate()
    checkState = QtCore.Qt.Checked
    if not isChecked:
      checkState = QtCore.Qt.Unchecked
    for i, _ in enumerate(self._movies):
      idx = self.index(i, Columns.COL_CHECK)
      self.setData(idx, checkState, QtCore.Qt.CheckStateRole)
    self.endUpdate()
    self._emitWorkbenchChanged()

  def _hasMoveableItems(self):
    return any(self._performMoveOnItem(m) for m in self._movies)

  def _emitWorkbenchChanged(self):
    has_items = self._hasMoveableItems()
    self.workbench_changed_signal.emit(has_items)

  def _updateAllStatusText(self):
    for movie in self._movies:
      self._updateItemStatus(movie)

  def beginUpdate(self):
    self._bulk_updating = True
    self.begin_update_signal.emit()

  def endUpdate(self):
    self._updateAllStatusText()
    self._bulk_updating = False
    self._emitWorkbenchChanged()
    self.end_update_signal.emit()

  def requireYearChanged(self, require):
    if self._require_year != require:
      self._require_year = require
      self._updateAllStatusText()

  def requireGenreChanged(self, require):
    if self._require_genre != require:
      self._require_genre = require
      self._updateAllStatusText()

  def flagDuplicateChanged(self, flag):
    if self._flag_duplicates != flag:
      self._flag_duplicates = flag
      self._updateAllStatusText()

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
        self._updateItemStatus(item)
    self.endRemoveRows()
