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
    if left.column() == Columns.COL_FILE_SIZE:
      leftData = self.sourceModel().data(left, RAW_DATA_ROLE).fileSize 
      rightData = self.sourceModel().data(right, RAW_DATA_ROLE).fileSize
      return leftData < rightData   
    else:
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

_MISSING_YEAR = "Missing Year"
_MISSING_GENRE = "Missing Genre"
_DUPLICATE = "Duplicate"
_OK = "Ok"

# --------------------------------------------------------------------------------------------------------------------
class MovieItem(object):
  def __init__(self, movie, index):
    super(MovieItem, self).__init__()
    utils.verifyType(movie, movieHelper.Movie)
    self.movie = movie
    self.index = index
    self.wantToMove = True
    self.cachedStatusText = "Unknown"
    self.duplicates = []
    
  def isMatch(self, other):
    utils.verifyType(other, MovieItem)
    return (self.movie.result == movieHelper.Result.FOUND and self.movie.result == other.movie.result and
            self.movie.title == other.movie.title and self.movie.year == other.movie.year and 
            self.movie.part == other.movie.part and self.movie.ext == other.movie.ext and 
            self.movie.genre() == other.movie.genre())
          
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
    self._flagDuplicates = True
    
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
      newMovie = copy.copy(value)
      if item.movie != newMovie:
        oldDups = item.duplicates
        item.movie = newMovie
        self._updateItemStatus(item)
        newDups = item.duplicates
        for nowDupIndex in (i for i in newDups if not i in oldDups):
          self._updateItemStatus(self._movies[nowDupIndex])
        for nowNotDupIndex in (i for i in oldDups if not i in newDups):
          self._updateItemStatus(self._movies[nowNotDupIndex])
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
    if self._isItemValid(item) or index.column() != Columns.COL_CHECK:
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

  def rowCount(self, parent=None):
    return len(self._movies)
  
  def clear(self):
    self.beginResetModel()
    self._movies = []
    self.endResetModel()
    if not self._bulkProcessing:
      self._emitWorkBenchChanged()    
  
  def addItem(self, m):
    utils.verifyType(m, movieHelper.Movie)
    #check if already in list
    count = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), count, count)
    item = MovieItem(m, count)
    self._movies.append(item)
    self.endInsertRows()     
    if not self._bulkProcessing:
      self._emitWorkBenchChanged()    
  
  def items(self):
    return [m.movie for m in self._movies if self._performMoveOnItem(m)]
  
  def _isItemValid(self, item):
    return item.cachedStatusText == _OK  or (item.cachedStatusText == _DUPLICATE and not self._flagDuplicates)
  
  def _updateItemStatus(self, item):
    oldStatusText = item.cachedStatusText
    self._updateDuplicatesForItem(item)
    self._updateItemStatusText(item)
    newStatusText = item.cachedStatusText
    if oldStatusText != newStatusText:
      self.dataChanged.emit(self.index(item.index, 0), self.index(item.index, Columns.NUM_COLS))
      
  def _updateItemStatusText(self, item):
    ret = ""
    if item.movie.result != movieHelper.Result.FOUND:
      ret = movieHelper.Result.resultStr(self.movie.result)
    elif item.duplicates:
      ret = _DUPLICATE
    elif self._requireYear and not item.movie.year:
      ret = _MISSING_YEAR
    elif self._requireGenre and not item.movie.genres:
      ret = _MISSING_GENRE
    else:
      ret = _OK
    item.cachedStatusText = ret
    return ret  
    
  def _performMoveOnItem(self, item):
    return item.wantToMove and self._isItemValid(item)
  
  def _updateDuplicatesForItem(self, item):
    item.duplicates = []
    if item.movie.result == movieHelper.Result.FOUND:
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
    utils.verifyType(isChecked, bool)
    self.beginUpdate()
    cs = QtCore.Qt.Checked
    if not isChecked:
      cs = QtCore.Qt.Unchecked
    for i, _ in enumerate(self._movies):
      idx = self.index(i, Columns.COL_CHECK)
      self.setData(idx, cs, QtCore.Qt.CheckStateRole) 
    self.endUpdate()
    self._emitWorkBenchChanged()
  
  def _hasMoveableItems(self):
    return any(self._performMoveOnItem(m) for m in self._movies)

  def _emitWorkBenchChanged(self):
    hasItems = self._hasMoveableItems()
    self.workBenchChangedSignal.emit(hasItems)
    
  def _updateAllStatusText(self):
    for movie in self._movies:
      self._updateItemStatus(movie)
    
  def beginUpdate(self):
    self._bulkProcessing = True
    self.beginUpdateSignal.emit()
    
  def endUpdate(self):
    self._updateAllStatusText()
    self._bulkProcessing = False 
    self._emitWorkBenchChanged()
    self.endUpdateSignal.emit()
    
  def requireYearChanged(self, require):
    if self._requireYear != require:
      self._requireYear = require
      self._updateAllStatusText()
    
  def requireGenreChanged(self, require):
    if self._requireGenre != require:
      self._requireGenre = require
      self._updateAllStatusText()
      
  def flagDuplicateChanged(self, flag):
    if self._flagDuplicates != flag:
      self._flagDuplicates = flag
      self._updateAllStatusText()
      
  def delete(self, index):
    if not index.isValid():
      return
    
    row = index.row()
    self.beginRemoveRows(QtCore.QModelIndex(), row, row)
    item = self._movies[row]
    dups = [i - 1 if i > row else i for i in item.duplicates]
    self._movies.pop(row)
    for item in self._movies[row:]:
      item.index -= 1
    self.endRemoveRows()
    
    for i in dups:
      self._updateItemStatus(self._movies[i])