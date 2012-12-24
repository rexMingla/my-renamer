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
from send2trash import send2trash

from common import fileHelper
from common import utils

from movie import movieModel
from movie import movieManager

from tv import season
from tv import tvModel
from tv import tvManager

import editEpisodeWidget
import editMovieWidget
import editSeasonWidget
import config
import interfaces

# --------------------------------------------------------------------------------------------------------------------
class BaseWorkBenchWidget(interfaces.LoadWidgetInterface):
  workBenchChangedSignal = QtCore.pyqtSignal(bool)
  showEditSourcesSignal = QtCore.pyqtSignal()
  
  def __init__(self, mode, manager, parent=None):
    super(BaseWorkBenchWidget, self).__init__("workBench/{}".format(mode), parent)
    uic.loadUi("ui/ui_WorkBench.ui", self)
    self._model = None
    self._manager = manager
    self.selectAllCheckBox.clicked.connect(self._setOverallCheckedState)
    self.launchButton.clicked.connect(self._launch)
    self.openButton.clicked.connect(self._open)    
    self.deleteButton.clicked.connect(self._delete)
    
  def _setModel(self, m):
    self._model = m
    self._model.workBenchChangedSignal.connect(self._onWorkBenchChanged)
    self._onWorkBenchChanged(False)
    self._model.beginUpdateSignal.connect(self.startWorkBenching)
    self._model.endUpdateSignal.connect(self.stopWorkBenching)      
    
  def _launchLocation(self, location):
    path = QtCore.QDir.toNativeSeparators(location)
    if not QtGui.QDesktopServices.openUrl(QtCore.QUrl("file:///{}".format(path))):
      QtGui.QMessageBox.information(self, "An error occured", 
                                    "Could not find path:\n{}".format(path))
    
  def _launch(self):
    raise NotImplementedError("BaseWorkBenchWidget._launch")
  
  def _open(self):
    raise NotImplementedError("BaseWorkBenchWidget._open")
      
  def _enable(self):
    self.setEnabled(True)
        
  def _disable(self):
    self.setEnabled(False)
    
  def startWorkBenching(self):
    self._disable()
        
  def stopWorkBenching(self):
    self._enable()
        
  def startExploring(self):
    self._model.clear()
    self._disable()
    self._model.beginUpdate()
  
  def stopExploring(self):
    self._enable()
    self.editEpisodeButton.setEnabled(False)    
    self.editSeasonButton.setEnabled(False)
    self.editMovieButton.setEnabled(False)    
    self.launchButton.setEnabled(False)
    self.openButton.setEnabled(False)
    self.deleteButton.setEnabled(False)    
    self._model.endUpdate()
    self._onWorkBenchChanged(bool(self._model.items())) #HACK: TODO: 
    
  def startActioning(self):
    self._disable()

  def stopActioning(self):
    self.tvView.expandAll()    
    self._enable()
    
  def getConfig(self):
    raise NotImplementedError("BaseWorkBenchWidget.getConfig not implemented")
  
  def setConfig(self, data):
    raise NotImplementedError("BaseWorkBenchWidget.getConfig not implemented")

  def _setOverallCheckedState(self, state):
    self._disable()
    self._model.setOverallCheckedState(state)
    self._enable()
    
  def _onWorkBenchChanged(self, hasChecked):
    utils.verifyType(hasChecked, bool)
    cs = self._model.overallCheckedState()
    self.selectAllCheckBox.setEnabled(not cs is None)
    if cs == None:
      cs = QtCore.Qt.Unchecked
    self.selectAllCheckBox.setCheckState(cs)
    self.workBenchChangedSignal.emit(hasChecked)
    
  def _delete(self):
    raise NotImplementedError("BaseWorkBenchWidget._delete not implemented")
    
  def _deleteLocation(self, location):
    isDel = False
    try:
      send2trash(location)
      isDel = True
    except OSError as e:
      mb = QtGui.QMessageBox(QtGui.QMessageBox.Information, 
                                   "An error occured", "Unable to move to trash. Path:\n{}".format(location))
      mb.setDetailedText("Error:\n{}".format(str(e)))
      mb.exec_()  
    return isDel
    
  def addItem(self, item):
    self._model.addItem(item)
    
  def actionableItems(self):
    return self._model.items()
  
# --------------------------------------------------------------------------------------------------------------------
class TvWorkBenchWidget(BaseWorkBenchWidget):
  def __init__(self, manager, parent=None):
    super(TvWorkBenchWidget, self).__init__(interfaces.Mode.TV_MODE, manager, parent)
    self._setModel(tvModel.TvModel(self.tvView))

    self._changeEpisodeWidget = editEpisodeWidget.EditEpisodeWidget(self)
    self._changeEpisodeWidget.accepted.connect(self._onChangeEpisodeFinished)
    
    self._changeSeasonWidget = editSeasonWidget.EditSeasonWidget(self)
    self._changeSeasonWidget.accepted.connect(self._onChangeSeasonFinished)
    self._changeSeasonWidget.showEditSourcesSignal.connect(self.showEditSourcesSignal.emit)
        
    self.tvView.setModel(self._model)
    self.tvView.header().setResizeMode(tvModel.Columns.COL_NEW_NAME, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(tvModel.Columns.COL_OLD_NAME, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(tvModel.Columns.COL_NEW_NUM, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(tvModel.Columns.COL_STATUS, QtGui.QHeaderView.Interactive)
    self.tvView.header().setStretchLastSection(True)
    #self.tvView.setItemDelegateForColumn(tvModel.Columns.COL_NEW_NAME, tvModel.SeriesDelegate(self))
    
    self.tvView.selectionModel().selectionChanged.connect(self._onSelectionChanged)
    self.tvView.doubleClicked.connect(self._onTvDoubleClicked)
    self.editEpisodeButton.clicked.connect(self._editEpisode)
    self.editSeasonButton.clicked.connect(self._editSeason)
    
    self.movieView.setVisible(False)
    self.editMovieButton.setVisible(False)
    self.movieGroupBox.setVisible(False)
    
  def _launch(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, tvModel.RAW_DATA_ROLE)
    assert(isMoveItemCandidate)
    self._launchLocation(moveItemCandidateData.source.filename)
  
  def _open(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, tvModel.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      f = fileHelper.FileHelper.dirname(moveItemCandidateData.source.filename)
    else:
      f = moveItemCandidateData.inputFolder
    self._launchLocation(f)
    
  def getConfig(self):
    return {"cache" : self._manager.cache(),
            "state" : utils.toString(self.tvView.header().saveState().toBase64()) }
  
  def setConfig(self, data):
    utils.verifyType(data, dict)
    self._manager.setCache(data.get("cache", {}))
    self.tvView.header().restoreState(QtCore.QByteArray.fromBase64(data.get("state", "")))
    
  def stopExploring(self):
    super(TvWorkBenchWidget, self).stopExploring()
    self.tvView.expandAll()
            
  def _onSelectionChanged(self, selection):
    indexes = selection.indexes()
    self._currentIndex = indexes[0] if indexes else None
    if bool(self._currentIndex):
      moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, tvModel.RAW_DATA_ROLE)
      #filthy. check if parent has season info
      canEditEp = (isMoveItemCandidate and moveItemCandidateData.canEdit and 
                  bool(self._model.data(self._currentIndex.parent(), tvModel.RAW_DATA_ROLE)[0].destination.matches))
      self.editEpisodeButton.setEnabled(canEditEp)
      self.editSeasonButton.setEnabled(True)
      self.launchButton.setEnabled(isMoveItemCandidate)
      self.openButton.setEnabled(True)
      self.deleteButton.setEnabled(not isMoveItemCandidate or 
                                   fileHelper.FileHelper.fileExists(moveItemCandidateData.source.filename))
    else:
      self.editEpisodeButton.setEnabled(False)
      self.editSeasonButton.setEnabled(False)
      self.launchButton.setEnabled(False)
      self.openButton.setEnabled(False)
      self.deleteButton.setEnabled(False)      

  def _onTvDoubleClicked(self, modelIndex):
    utils.verifyType(modelIndex, QtCore.QModelIndex)
    moveItemCandidateData, isMoveItemCandidate = self._model.data(modelIndex, tvModel.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      if (isMoveItemCandidate and moveItemCandidateData.canEdit and 
          bool(self._model.data(modelIndex.parent(), tvModel.RAW_DATA_ROLE)[0].destination.matches)):
        self._editEpisode()
      else:
        QtGui.QMessageBox.information(self, "Can not edit Episode", 
                                      "Episodes can only be edited for existing files where Season data has been defined.")
    else:
      self._editSeason()
        
  def _editSeason(self):
    seasonData, isMoveItemCandidate = self._model.data(self._currentIndex, tvModel.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      self._currentIndex  = self._currentIndex.parent()
      seasonData, isMoveItemCandidate = self._model.data(self._currentIndex, tvModel.RAW_DATA_ROLE)
    utils.verify(not isMoveItemCandidate, "Must be a movie to have gotten here!")
    self._changeSeasonWidget.setData(seasonData)
    self._changeSeasonWidget.show()
  
  def _editEpisode(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, tvModel.RAW_DATA_ROLE)
    if isMoveItemCandidate and moveItemCandidateData.canEdit:
      seasonData, isMoveItemCandidate = self._model.data(self._currentIndex.parent(), tvModel.RAW_DATA_ROLE)
      utils.verify(not isMoveItemCandidate, "Must be move item")
      self._changeEpisodeWidget.setData(seasonData, moveItemCandidateData)
      self._changeEpisodeWidget.show()
      
  def _onChangeEpisodeFinished(self):
    newKey = self._changeEpisodeWidget.episodeNumber()
    self._model.setData(self._currentIndex, QtCore.QVariant(newKey), tvModel.RAW_DATA_ROLE)
    self.tvView.expand(self._currentIndex.parent())
    
  def _onChangeSeasonFinished(self):
    data = self._changeSeasonWidget.data()
    utils.verifyType(data, season.Season)
    self._manager.setItem(data.itemToInfo())
    self._model.setData(self._currentIndex, data, tvModel.RAW_DATA_ROLE)
    self.tvView.expand(self._currentIndex)
    
  def _delete(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, tvModel.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      f = moveItemCandidateData.source.filename
    else:
      f = moveItemCandidateData.inputFolder
    if self._deleteLocation(f):
      self._model.delete(self._currentIndex)
  
    
# --------------------------------------------------------------------------------------------------------------------
class MovieWorkBenchWidget(BaseWorkBenchWidget):
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
    self.editSeasonButton.setVisible(False)
    self.editEpisodeButton.setVisible(False)    
     
  def _launch(self):
    movie = self._model.data(self._currentIndex, movieModel.RAW_DATA_ROLE)
    self._launchLocation(movie.filename)
  
  def _open(self):
    movie = self._model.data(self._currentIndex, movieModel.RAW_DATA_ROLE)
    f = fileHelper.FileHelper.dirname(movie.filename)
    self._launchLocation(fileHelper.FileHelper.dirname(movie.filename))
            
  def getConfig(self):
    return {"cache" : self._manager.cache(),
            "no_year_as_error" : self.yearCheckBox.isChecked(),
            "no_genre_as_error" : self.genreCheckBox.isChecked(),
            "duplicate_as_error" : self.duplicateCheckBox.isChecked(),
            "state" : utils.toString(self.movieView.horizontalHeader().saveState().toBase64()),
            "series_list" : self._changeMovieWidget.getSeriesList()  }
  
  def setConfig(self, data):
    utils.verifyType(data, dict)
    self._manager.setCache(data.get("cache", {}))
    self.yearCheckBox.setChecked(data.get("no_year_as_error", True))
    self.genreCheckBox.setChecked(data.get("no_genre_as_error", True))
    self.duplicateCheckBox.setChecked(data.get("duplicate_as_error", True)),
    self.movieView.horizontalHeader().restoreState(QtCore.QByteArray.fromBase64(data.get("state", "")))
    self._changeMovieWidget.setSeriesList(data.get("series_list", []))

  def _onSelectionChanged(self, selection):
    indexes = selection.indexes()
    self._currentIndex = self._sortModel.mapToSource(indexes[0]) if indexes else None
    hasIndex = bool(self._currentIndex)
    
    self.launchButton.setEnabled(hasIndex)
    self.openButton.setEnabled(hasIndex)
    self.deleteButton.setEnabled(hasIndex)
    self.editMovieButton.setEnabled(hasIndex)
      
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
  
  def _delete(self):
    movie = self._model.data(self._currentIndex, movieModel.RAW_DATA_ROLE)
    if self._deleteLocation(movie.filename):
      self._model.delete(self._currentIndex)
      self.tvView.expandAll()
  