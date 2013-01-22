#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui

from common import config
from common import renamer
from common import utils

from movie import model as movie_model
#from movie import manager as movie_manager

import editMovieWidget
import interfaces
import workBenchWidget
  
# --------------------------------------------------------------------------------------------------------------------
class MovieWorkBenchWidget(workBenchWidget.BaseWorkBenchWidget):
  def __init__(self, manager, parent=None):
    super(MovieWorkBenchWidget, self).__init__(interfaces.Mode.MOVIE_MODE, manager, parent)
    self._setModel(movie_model.MovieModel(self.movieView))
    
    self._changeMovieWidget = editMovieWidget.EditMovieWidget(self)
    self._changeMovieWidget.accepted.connect(self._onChangeMovieFinished)
    self._changeMovieWidget.showEditSourcesSignal.connect(self.showEditSourcesSignal.emit)    
    
    self._sortModel = movie_model.SortFilterModel(self)
    self._sortModel.setSourceModel(self._model)  
    self.movieView.setModel(self._sortModel)
    self.movieView.horizontalHeader().setResizeMode(movie_model.Columns.COL_CHECK, QtGui.QHeaderView.Fixed)
    self.movieView.horizontalHeader().resizeSection(movie_model.Columns.COL_CHECK, 25)
    self.movieView.horizontalHeader().setResizeMode(movie_model.Columns.COL_NEW_NAME, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movie_model.Columns.COL_OLD_NAME, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movie_model.Columns.COL_YEAR, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movie_model.Columns.COL_DISC, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movie_model.Columns.COL_STATUS, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movie_model.Columns.COL_GENRE, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setStretchLastSection(True)
    self.movieView.verticalHeader().setDefaultSectionSize(20)
    self.movieView.setSortingEnabled(True)
        
    self.yearCheckBox.toggled.connect(self._requireYearChanged)
    self.genreCheckBox.toggled.connect(self._requireGenreChanged)
    self.duplicateCheckBox.toggled.connect(self._flagDuplicateChanged)
    self.movieView.selectionModel().selectionChanged.connect(self._onSelectionChanged)    
    self.movieView.doubleClicked.connect(self._editMovie)
    self.editMovieButton.clicked.connect(self._editMovie)
    
    self._requireYearChanged(self.yearCheckBox.isChecked())
    self._requireGenreChanged(self.genreCheckBox.isChecked())
    self._flagDuplicateChanged(self.duplicateCheckBox.isChecked())
    
    self.tvView.setVisible(False)
    self._onSelectionChanged()
     
  def getConfig(self):
    ret = config.MovieWorkBenchConfig()
    ret.noYearAsError = self.yearCheckBox.isChecked()
    ret.noGenreAsError = self.genreCheckBox.isChecked()
    ret.duplicateAsError = self.duplicateCheckBox.isChecked()
    ret.state = utils.toString(self.movieView.horizontalHeader().saveState().toBase64())
    ret.seriesList = self._changeMovieWidget.getSeriesList()
    return ret
  
  def setConfig(self, data):
    data = data or config.MovieWorkBenchConfig()

    self.yearCheckBox.setChecked(data.noYearAsError)
    self.genreCheckBox.setChecked(data.noGenreAsError)
    self.duplicateCheckBox.setChecked(data.duplicateAsError)
    self.movieView.horizontalHeader().restoreState(QtCore.QByteArray.fromBase64(data.state))
    self._changeMovieWidget.setSeriesList(data.seriesList)
    
  def _showItem(self):    
    self._editMovie()

  def _onSelectionChanged(self, selection=None):
    selection = selection or self.movieView.selectionModel().selection()
    indexes = selection.indexes()
    self._currentIndex = self._sortModel.mapToSource(indexes[0]) if indexes else QtCore.QModelIndex()
    self._updateActions()
    self.renameItemChangedSignal.emit(self._model.getRenameItem(self._currentIndex))
    
  def _editMovie(self):
    movie = self._model.data(self._currentIndex, movie_model.RAW_DATA_ROLE)
    #utils.verifyType(movie, movie_manager.MovieRenameItem)
    self._changeMovieWidget.setData(movie)
    self._changeMovieWidget.show()    
      
  def _onChangeMovieFinished(self):
    data = self._changeMovieWidget.data()    
    #utils.verifyType(data, movie_manager.MovieRenameItem)
    self._manager.setItem(data.getInfo())
    self._model.setData(self._currentIndex, data, movie_model.RAW_DATA_ROLE)
    self._onSelectionChanged()
    
  def _requireYearChanged(self, requireYear):
    self._disable()
    self._model.requireYearChanged(requireYear)
    self._enable()

  def _requireGenreChanged(self, requireGenre):
    self._disable()
    self._model.requireGenreChanged(requireGenre)
    self._enable()

  def _flagDuplicateChanged(self, flagDuplicate):
    self._disable()
    self._model.flagDuplicateChanged(flagDuplicate)
    self._enable()

  