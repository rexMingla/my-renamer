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

import movieHelper

# --------------------------------------------------------------------------------------------------------------------
class SortFilterModel(QtGui.QSortFilterProxyModel):
  def lessThan(self, left, right):
    leftData = self.sourceModel().data(left, QtCore.Qt.ToolTipRole) #use tooltip so that filename is col is full path
    rightData = self.sourceModel().data(right, QtCore.Qt.ToolTipRole) 
    return leftData < rightData   
    
# --------------------------------------------------------------------------------------------------------------------
class Columns:
  """ Columns used in workbench model. """
  COL_CHECK     = 0
  COL_OLD_NAME  = 1
  COL_NEW_NAME  = 2
  COL_YEAR      = 3
  COL_GENRE     = 4
  COL_STATUS    = 5
  COL_DISC      = 6
  COL_FILE_SIZE = 7
  NUM_COLS      = 8

RAW_DATA_ROLE = QtCore.Qt.UserRole + 1

_YEAR_REQUIRED = "Year required"
_GENRE_REQUIRED = "Genre required"

# --------------------------------------------------------------------------------------------------------------------
class MovieItem(object):
  def __init__(self, movie, index):
    super(MovieItem, self).__init__()
    utils.verifyType(movie, movieHelper.Movie)
    self.movie = movie
    self.index = index
    self.wantToMove = True
    self.cachedStatusText = "Unknown"
    self.isDuplicate = False
    
  def isMatch(self, other):
    utils.verifyType(other, MovieItem)
    return (self.movie.result == movieHelper.Result.FOUND and self.movie.result == other.movie.result and
            self.movie.title == other.movie.title and self.movie.year == other.movie.year and 
            self.movie.part == other.movie.part and self.movie.ext == other.movie.ext and 
            self.movie.genre() == other.movie.genre())
  
  def isValid(self):
    return self.cachedStatusText == movieHelper.Result.as_string(movieHelper.Result.FOUND)
    
  def _updateStatusText(self, requireYear, requireGenre):
    ret = ""
    if self.movie.result != movieHelper.Result.FOUND:
      ret = movieHelper.Result.as_string(self.movie.result)
    elif self.isDuplicate:
      ret = "Duplicate"
    elif requireYear and not self.movie.year:
      ret = _YEAR_REQUIRED
    elif requireGenre and not self.movie.genres:
      ret = _GENRE_REQUIRED
    else:
      ret = movieHelper.Result.as_string(self.movie.result)
    self.cachedStatusText = ret
    return ret
    
  def performMove(self):
    return self.wantToMove and self.isValid()
      
# --------------------------------------------------------------------------------------------------------------------
class MovieModel(QtCore.QAbstractTableModel):
  """ 
  Represents 0 or more movies
  """
  workBenchChangedSignal = QtCore.pyqtSignal(bool)
  beginUpdateSignal = QtCore.pyqtSignal()
  endUpdateSignal = QtCore.pyqtSignal()  
  
  def __init__(self, parent=None):
    super(MovieModel, self).__init__(parent)
    self._movies = []
    self._bulkProcessing = False
    self._requireYear = True
    self._requireGenre = True
    
  def columnCount(self, parent):
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
    if role == RAW_DATA_ROLE:
      return copy.copy(movie)
    
    col = index.column()
    if role == QtCore.Qt.ForegroundRole and not item.isValid():
      return QtGui.QBrush(QtCore.Qt.red)      
    elif col == Columns.COL_CHECK:
      if role == QtCore.Qt.CheckStateRole:
        if item.performMove(): 
          return QtCore.Qt.Checked
        else:
          return QtCore.Qt.Unchecked
    elif col == Columns.COL_OLD_NAME:
      if role == QtCore.Qt.DisplayRole:
        return fileHelper.FileHelper.basename(movie.filename)
      else:
        return movie.filename
    elif col == Columns.COL_NEW_NAME:
      return movie.title
    elif col == Columns.COL_DISC:
      return movie.part
    elif col == Columns.COL_STATUS:
      return item.cachedStatusText
    elif col == Columns.COL_YEAR:
      return movie.year
    elif col == Columns.COL_GENRE:
      return movie.genre()
    elif col == Columns.COL_FILE_SIZE:
      return utils.bytesToString(movie.fileSize) if movie.result == movieHelper.Result.FOUND else ""
       
  def setData(self, index, value, role):
    if not index.isValid() or role not in (QtCore.Qt.CheckStateRole, RAW_DATA_ROLE):
      return False
    
    if role == RAW_DATA_ROLE:
      utils.verifyType(value, movieHelper.Movie)
      item = self._movies[index.row()]
      item.movie = copy.copy(value)
      if not self._bulkProcessing:
        self._updateStatusText()
    elif role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_CHECK:
      item = self._movies[index.row()]
      item.wantToMove = value == QtCore.Qt.Checked
      self.dataChanged.emit(index, index)
      if not self._bulkProcessing:
        self._emitWorkBenchChanged()    
    return True
    
  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags
    
    item = self._movies[index.row()]
    movie = item.movie
    
    f = QtCore.Qt.ItemIsSelectable
    if item.isValid() or index.column() != Columns.COL_CHECK:
      f |= QtCore.Qt.ItemIsEnabled 
    if index.column() == Columns.COL_CHECK:
      f |= QtCore.Qt.ItemIsUserCheckable
    return f

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

  def rowCount(self, parent):
    return len(self._movies)
  
  def clear(self):
    self.beginResetModel()
    self._movies = []
    self.endResetModel()
    self._emitWorkBenchChanged()
  
  def addItem(self, m):
    utils.verifyType(m, movieHelper.Movie)
    #check if already in list
    count = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), count, count)
    item = MovieItem(m, count)
    self._movies.append(item)
    self.endInsertRows()     
    self._emitWorkBenchChanged()
  
  def items(self):
    return [i.movie for i in self._movies if i.performMove()]
  
  def overallCheckedState(self):
    filtered = [m for m in self._movies if m.isValid()]
    if not filtered:
      return None
    
    ret = QtCore.Qt.PartiallyChecked
    if all(m.performMove() for m in filtered):
      ret = QtCore.Qt.Checked
    elif all(not(m.performMove()) for m in filtered):
      ret = QtCore.Qt.Unchecked
    return ret
  
  def setOverallCheckedState(self, isChecked):
    utils.verifyType(isChecked, bool)
    self._bulkProcessing = True
    cs = QtCore.Qt.Checked
    if not isChecked:
      cs = QtCore.Qt.Unchecked
    for i, _ in enumerate(self._movies):
      idx = self.index(i, Columns.COL_CHECK)
      self.setData(idx, cs, QtCore.Qt.CheckStateRole) 
    self._bulkProcessing = False
    self._emitWorkBenchChanged()
  
  def _hasMoveableItems(self):
    return any(m.performMove() for m in self._movies)

  def _emitWorkBenchChanged(self):
    if self._bulkProcessing:
      return
    hasItems = self._hasMoveableItems()
    self.workBenchChangedSignal.emit(hasItems)
    
  def _updateStatusText(self):
    self.beginUpdateSignal.emit()
    self._bulkProcessing = True
    for movie in self._movies:
      oldStatusText = movie.cachedStatusText
      #check for dup
      movie.isDuplicate = (movie.movie.result == movieHelper.Result.FOUND and 
                           any(m.isMatch(movie) for m in self._movies if m.index != movie.index))
      newStatusText = movie._updateStatusText(self._requireYear, self._requireGenre) #update the status
      if oldStatusText != newStatusText:
        self.dataChanged.emit(self.index(movie.index, 0), self.index(movie.index, Columns.NUM_COLS))
    self._bulkProcessing = False
    self._emitWorkBenchChanged()
    self.endUpdateSignal.emit()
    
  def beginUpdate(self):
    self._bulkProcessing = True
    
  def endUpdate(self):
    self._bulkProcessing = False    
    self._updateStatusText()
    
  def requireYearChanged(self, require):
    if self._requireYear != require:
      self._requireYear = require
      self._updateStatusText()
    
  def requireGenreChanged(self, require):
    if self._requireGenre != require:
      self._requireGenre = require
      self._updateStatusText()    
    
    