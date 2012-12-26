#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui

from common import utils
from common import workBench

from movie import movieModel
from movie import movieManager

from app import editMovieWidget
from app import interfaces
  
# --------------------------------------------------------------------------------------------------------------------
class MovieWorkBenchWidget(workBench.BaseWorkBenchWidget):
  def __init__(self, manager, parent=None):
    super(MovieWorkBenchWidget, self).__init__(interfaces.Mode.MOVIE_MODE, manager, parent)
    self._setModel(movieModel.MovieModel(self.movieView))
    
    self._changeMovieWidget = editMovieWidget.EditMovieWidget(self)
    self._changeMovieWidget.accepted.connect(self._onChangeMovieFinished)
    self._changeMovieWidget.showEditSourcesSignal.connect(self.showEditSourcesSignal.emit)    
    
    self._sortModel = movieModel.SortFilterModel(self)
    self._sortModel.setSourceModel(self._model)  
    self.movieView.setModel(self._sortModel)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_CHECK, QtGui.QHeaderView.Fixed)
    self.movieView.horizontalHeader().resizeSection(movieModel.Columns.COL_CHECK, 25)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_NEW_NAME, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_OLD_NAME, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_YEAR, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_DISC, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_STATUS, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_GENRE, QtGui.QHeaderView.Interactive)
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
    return {"no_year_as_error" : self.yearCheckBox.isChecked(),
            "no_genre_as_error" : self.genreCheckBox.isChecked(),
            "duplicate_as_error" : self.duplicateCheckBox.isChecked(),
            "state" : utils.toString(self.movieView.horizontalHeader().saveState().toBase64()),
            "series_list" : self._changeMovieWidget.getSeriesList()  }
  
  def setConfig(self, data):
    utils.verifyType(data, dict)
    self.yearCheckBox.setChecked(data.get("no_year_as_error", True))
    self.genreCheckBox.setChecked(data.get("no_genre_as_error", True))
    self.duplicateCheckBox.setChecked(data.get("duplicate_as_error", True)),
    self.movieView.horizontalHeader().restoreState(QtCore.QByteArray.fromBase64(data.get("state", "AAAA/wAAAAAAAAABAAAAAQAAAAABAAAAAAAAAAAAAAAAAAAAAAAAA14AAAAJAAEAAQAAAAAAAAAAAAAAAGT/////AAAAhAAAAAAAAAAJAAAAGQAAAAEAAAACAAAAmQAAAAEAAAAAAAAA4wAAAAEAAAAAAAAAQgAAAAEAAAAAAAAAPwAAAAEAAAAAAAAAZAAAAAEAAAAAAAAAUAAAAAEAAAAAAAAARQAAAAEAAAAAAAAATwAAAAEAAAAA")))
    self._changeMovieWidget.setSeriesList(data.get("series_list", []))
    
  def _showItem(self):    
    self._editMovie()

  def _onSelectionChanged(self, selection=None):
    indexes = selection and selection.indexes()
    self._currentIndex = self._sortModel.mapToSource(indexes[0]) if indexes else None
    self._updateActions()
      
  def _editMovie(self):
    movie = self._model.data(self._currentIndex, movieModel.RAW_DATA_ROLE)
    utils.verifyType(movie, movieManager.Movie)
    self._changeMovieWidget.setData(movie)
    self._changeMovieWidget.show()    
      
  def _onChangeMovieFinished(self):
    data = self._changeMovieWidget.data()    
    utils.verifyType(data, movieManager.Movie)
    self._manager.setItem(data.itemToInfo())
    self._model.setData(self._currentIndex, data, tvModel.RAW_DATA_ROLE)
    
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

  