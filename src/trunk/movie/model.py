#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Model and other classes pertaining to the set of tv seasons to be modified in the workbench
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui

from common import fileHelper
from common import utils
"""import episode
import moveItemCandidate
import season
import seasonHelper"""
import movieHelper

# --------------------------------------------------------------------------------------------------------------------
class Columns:
  """ Columns used in workbench model. """
  COL_OLD_NAME = 0
  COL_NEW_NAME = 1
  COL_YEAR     = 2
  COL_GENRE    = 3
  COL_STATUS   = 4
  COL_DISC     = 5
  NUM_COLS     = 6

RAW_DATA_ROLE = QtCore.Qt.UserRole + 1


# --------------------------------------------------------------------------------------------------------------------
class MovieItem(object):
  def __init__(self, movie):
    super(MovieItem, self).__init__()
    utils.verifyType(movie, movieHelper.Movie)
    self.movie = movie
    self.performMove = True
    self.canEdit = True
    self.update()
    
  def hasData(self):
    return self.movie.title and self.movie.genres and self.movie.year
    
  def update(self):
    self.canEdit = self.movie.title and self.movie.year
      
# --------------------------------------------------------------------------------------------------------------------
class MovieModel(QtCore.QAbstractTableModel):
  """ 
  Represents 0 or more movies
  """
  workBenchChangedSignal = QtCore.pyqtSignal(bool)
  
  def __init__(self, parent=None):
    super(MovieModel, self).__init__(parent)
    self._movies = []
    self._bulkProcessing = False
    
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
      (role == QtCore.Qt.CheckStateRole and index.column() != Columns.COL_OLD_NAME):
      return None

    item = self._movies[index.row()]
    movie = item.movie
    col = index.column()
    if role == QtCore.Qt.ForegroundRole and not item.hasData():
      return QtGui.QBrush(QtCore.Qt.red)      
    if col == Columns.COL_OLD_NAME:
      if role == QtCore.Qt.CheckStateRole:
        if item.performMove and item.canEdit: 
          return QtCore.Qt.Checked
        else:
          return QtCore.Qt.Unchecked
      elif role == QtCore.Qt.DisplayRole:
        return fileHelper.FileHelper.basename(movie.filename)
      else:
        return movie.filename
    elif col == Columns.COL_NEW_NAME:
      return movie.title
    elif col == Columns.COL_DISC:
      return movie.part
    elif col == Columns.COL_STATUS:
      ret = "Missing Info"
      if item.hasData():
        ret = "OK"
      return ret
    elif col == Columns.COL_YEAR:
      return movie.year
    elif col == Columns.COL_GENRE:
      return movie.genres[0] # take first for now
       
  def setData(self, index, value, role):
    if not index.isValid():
      return False
    
    ret = False
    item = self._movies[index.row()]
    if role == QtCore.Qt.CheckStateRole and index.column() == Columns.COL_OLD_NAME:
      item.performMove = value == QtCore.Qt.Checked
      self.dataChanged.emit(index, index)
      ret = True
    if ret and not self._bulkProcessing:   
      self._emitWorkBenchChanged()    
    return ret
    
  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags
    
    item = self._movies[index.row()]
    movie = item.movie
    
    f = QtCore.Qt.ItemIsSelectable
    if item.canEdit:
      f |= QtCore.Qt.ItemIsEnabled 
    if index.column() == Columns.COL_OLD_NAME:
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
    self._movies.append(MovieItem(m))
    self.endInsertRows()     
    self._emitWorkBenchChanged()
  
  def items(self):
    return self._movies
  
  def overallCheckedState(self):
    filtered = [m for m in self._movies if m.canEdit]
    if not filtered:
      return None
    
    ret = QtCore.Qt.PartiallyChecked
    if all(m.performMove for m in self._movies):
      ret = QtCore.Qt.Checked
    elif all(not(m.performMove and m.canEdit) for m in self._movies):
      ret = QtCore.Qt.Unchecked
    return ret
  
  def setOverallCheckedState(self, isChecked):
    utils.verifyType(isChecked, bool)
    self._bulkProcessing = True
    cs = QtCore.Qt.Checked
    if not isChecked:
      cs = QtCore.Qt.Unchecked
    for i, _ in enumerate(self._movies):
      idx = self.index(i, Columns.COL_OLD_NAME)
      self.setData(idx, cs, QtCore.Qt.CheckStateRole) 
    self._bulkProcessing = False
    self._emitWorkBenchChanged()
  
  def _hasMoveableItems(self):
    return any(m.performMove and m.canEdit for m in self._movies)

  def _emitWorkBenchChanged(self):
    hasItems = self._hasMoveableItems()
    self.workBenchChangedSignal.emit(hasItems)
    
    
    