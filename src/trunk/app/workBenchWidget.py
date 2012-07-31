#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from common import utils
from movie import model as movieModel
from movie import movieHelper
from tv import model
from tv import seasonHelper

import changeEpisodeWidget
import changeMovieWidget
import changeSeasonWidget
import interfaces

# --------------------------------------------------------------------------------------------------------------------
class WorkBenchWidget(interfaces.LoadWidgetInterface):
  workBenchChangedSignal = QtCore.pyqtSignal(bool)
  
  def __init__(self, parent=None):
    super(WorkBenchWidget, self).__init__("workBench", parent)
    uic.loadUi("ui/ui_WorkBench.ui", self)
    
    self._changeEpisodeWidget = changeEpisodeWidget.ChangeEpisodeWidget(self)
    self._changeEpisodeWidget.accepted.connect(self._onChangeEpisodeFinished)
    
    self._changeSeasonWidget = changeSeasonWidget.ChangeSeasonWidget(self)
    self._changeSeasonWidget.accepted.connect(self._onChangeSeasonFinished)
    
    self._changeMovieWidget = changeMovieWidget.ChangeMovieWidget(self)
    self._changeMovieWidget.accepted.connect(self._onChangeMovieFinished)    
    
    self.movieModel = movieModel.MovieModel(self)
    self._sortModel = movieModel.SortFilterModel(self)
    self._sortModel.setSourceModel(self.movieModel)    
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
    self.movieModel.workBenchChangedSignal.connect(self._onWorkBenchChanged)
        
    self.yearCheckBox.toggled.connect(self.movieModel.requireYearChanged)
    self.genreCheckBox.toggled.connect(self.movieModel.requireGenreChanged)
    self.movieView.clicked.connect(self._onMovieClicked)
    self.movieView.doubleClicked.connect(self._editMovie)
    self.editMovieButton.clicked.connect(self._editMovie)

    self.tvModel = model.TvModel(self)
    self.tvView.setModel(self.tvModel)
    self.tvView.header().setResizeMode(model.Columns.COL_NEW_NAME, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(model.Columns.COL_OLD_NAME, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(model.Columns.COL_NEW_NUM, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(model.Columns.COL_STATUS, QtGui.QHeaderView.Interactive)
    self.tvView.header().setStretchLastSection(True)
    self.tvModel.workBenchChangedSignal.connect(self._onWorkBenchChanged)    
    self.selectAllCheckBox.clicked.connect(self._setOverallCheckedState)
    
    self.tvView.clicked.connect(self._onTvClicked)
    self.tvView.doubleClicked.connect(self._onTvDoubleClicked)
    self.editEpisodeButton.clicked.connect(self._editEpisode)
    self.editSeasonButton.clicked.connect(self._editSeason)
    
    self.movieModel.beginUpdateSignal.connect(self._disable)
    self.movieModel.endUpdateSignal.connect(self._enable)

    self.editEpisodeButton.setEnabled(False)
    self.editSeasonButton.setEnabled(False)
    self.selectAllCheckBox.setEnabled(False)
    
    self._currentModel = None
    
    self.stopActioning()
    self.stopExploring()
    
  def _enable(self):
    self.setEnabled(True)
        
  def _disable(self):
    self.setEnabled(False)
        
  def startExploring(self):
    self._currentModel.clear()
    self._disable()
  
  def stopExploring(self):
    self._enable()
    self.editSeasonButton.setEnabled(False)
    if self.mode == interfaces.Mode.MOVIE_MODE:
      self.movieModel.buildUpdateFinished()

  def startActioning(self):
    self._disable()

  def stopActioning(self):
    self.tvView.expandAll()    
    self._enable()
    
  def _setMovieMode(self):
    self._currentModel = self.movieModel
    self._setOverallCheckedState(not self._currentModel.overallCheckedState())

    self.movieButton.setVisible(False)  
    self.editSeasonButton.setVisible(False)
    self.editEpisodeButton.setVisible(False)
    self.tvView.setVisible(False)
    
    self.tvButton.setVisible(True)
    self.editMovieButton.setVisible(True)
    self.movieView.setVisible(True)
    self.movieGroupBox.setVisible(True)
    
  def _setTvMode(self):
    self._currentModel = self.tvModel
    self._setOverallCheckedState(not self._currentModel.overallCheckedState())

    self.tvButton.setVisible(False)
    self.editMovieButton.setVisible(False)
    self.movieView.setVisible(False)
    self.movieGroupBox.setVisible(False)

    self.movieButton.setVisible(True)  
    self.editSeasonButton.setVisible(True)
    self.editEpisodeButton.setVisible(True)
    self.tvView.setVisible(True)
            
  def getConfig(self, mode=None):
    mode = mode or self.mode
    if mode == interfaces.Mode.MOVIE_MODE:
      return {"cache" : movieHelper.MovieHelper.cache(),
              "no_year_as_error" : self.yearCheckBox.isChecked(),
              "no_genre_as_error" : self.genreCheckBox.isChecked(),
              "state" : utils.toString(self.movieView.horizontalHeader().saveState().toBase64()) }
    else:
      return {"cache" : seasonHelper.SeasonHelper.cache(),
              "state" : utils.toString(self.tvView.header().saveState().toBase64()),
              "use_cache" : self._changeSeasonWidget.useCacheCheckBox.isChecked() }
  
  def setConfig(self, data, mode=None):
    utils.verifyType(data, dict)
    mode = mode or self.mode
    if mode == interfaces.Mode.MOVIE_MODE:
      movieHelper.MovieHelper.setCache(data.get("cache", {}))
      self.yearCheckBox.setChecked(data.get("no_year_as_error", True))
      self.genreCheckBox.setChecked(data.get("no_genre_as_error", True))
      self.movieView.horizontalHeader().restoreState(QtCore.QByteArray.fromBase64(data.get("state", "")))
    else:
      seasonHelper.SeasonHelper.setCache(data.get("cache", {}))
      self._changeSeasonWidget.useCacheCheckBox.setChecked(data.get("use_cache", True))
      self.tvView.header().restoreState(QtCore.QByteArray.fromBase64(data.get("state", "")))

  def _currentMovieModelIndex(self, index):
    return self._sortModel.mapToSource(index)
      
  def _onMovieClicked(self, index):
    self._currentIndex = self._currentMovieModelIndex(index)
      
  def _editMovie(self):
    movie = self.movieModel.data(self._currentIndex, movieModel.RAW_DATA_ROLE)
    utils.verifyType(movie, movieHelper.Movie)
    self._changeMovieWidget.setData(movie)
    self._changeMovieWidget.show()    
      
  def _onChangeMovieFinished(self):
    data = self._changeMovieWidget.data()
    utils.verifyType(data, movieHelper.Movie)
    self.movieModel.setData(self._currentIndex, data, model.RAW_DATA_ROLE)
            
  def _onTvClicked(self, modelIndex):
    self._currentIndex = modelIndex
    moveItemCandidateData, isMoveItemCandidate = self.tvModel.data(modelIndex, model.RAW_DATA_ROLE)
    #filthy. check if parent has season info
    canEditEp = (isMoveItemCandidate and moveItemCandidateData.canEdit and 
                bool(self.tvModel.data(modelIndex.parent(), model.RAW_DATA_ROLE)[0].destination.matches))
    self.editEpisodeButton.setEnabled(canEditEp)
    self.editSeasonButton.setEnabled(True)

  def _onTvDoubleClicked(self, modelIndex):
    utils.verifyType(modelIndex, QtCore.QModelIndex)
    moveItemCandidateData, isMoveItemCandidate = self.tvModel.data(modelIndex, model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      if (isMoveItemCandidate and moveItemCandidateData.canEdit and 
          bool(self.tvModel.data(modelIndex.parent(), model.RAW_DATA_ROLE)[0].destination.matches)):
        self._editEpisode()
      else:
        QtGui.QMessageBox.information(self, "Can not edit Episode", 
                                      "Episodes can only be edited for existing files where Season data has been defined.")
    else:
      self._editSeason()
        
  def _editSeason(self):
    seasonData, isMoveItemCandidate = self.tvModel.data(self._currentIndex, model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      self._currentIndex  = self._currentIndex.parent()
      seasonData, isMoveItemCandidate = self.tvModel.data(self._currentIndex, model.RAW_DATA_ROLE)
    utils.verify(not isMoveItemCandidate, "Must be a movie to have gotten here!")
    self._changeSeasonWidget.setData(seasonData)
    self._changeSeasonWidget.show()
  
  def _editEpisode(self):
    moveItemCandidateData, isMoveItemCandidate = self.tvModel.data(self._currentIndex, model.RAW_DATA_ROLE)
    if isMoveItemCandidate and moveItemCandidateData.canEdit:
      seasonData, isMoveItemCandidate = self.tvModel.data(self._currentIndex.parent(), model.RAW_DATA_ROLE)
      utils.verify(not isMoveItemCandidate, "Must be move item")
      self._changeEpisodeWidget.setData(seasonData, moveItemCandidateData)
      self._changeEpisodeWidget.show()
      
  def _onChangeEpisodeFinished(self):
    newKey = self._changeEpisodeWidget.episodeNumber()
    self.tvModel.setData(self._currentIndex, QtCore.QVariant(newKey), model.RAW_DATA_ROLE)
    self.tvView.expand(self._currentIndex.parent())
    
  def _onChangeSeasonFinished(self):
    data = self._changeSeasonWidget.data()
    self.tvModel.setData(self._currentIndex, data, model.RAW_DATA_ROLE)
    self.tvView.expand(self._currentIndex)
    
  def _setOverallCheckedState(self, state):
    if self._currentModel:
      self._currentModel.setOverallCheckedState(state)
    
  def _onWorkBenchChanged(self, hasChecked):
    utils.verifyType(hasChecked, bool)
    if not self._currentModel:
      return
    cs = self._currentModel.overallCheckedState()
    self.selectAllCheckBox.setEnabled(not cs is None)
    if cs == None:
      cs = QtCore.Qt.Unchecked
    self.selectAllCheckBox.setCheckState(cs)
    self.workBenchChangedSignal.emit(hasChecked)
    