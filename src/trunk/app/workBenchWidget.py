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
from movie import model as movieModel
from movie import movieHelper
from tv import model
from tv import season
from tv import seasonHelper

import changeEpisodeWidget
import changeMovieWidget
import changeSeasonWidget
import config
import interfaces

# --------------------------------------------------------------------------------------------------------------------
class BaseWorkBenchWidget(interfaces.LoadWidgetInterface):
  workBenchChangedSignal = QtCore.pyqtSignal(bool)
  modeChangedSignal = QtCore.pyqtSignal(object)  
  
  def __init__(self, mode, parent=None):
    super(BaseWorkBenchWidget, self).__init__("workBench/{}".format(mode), parent)
    uic.loadUi("ui/ui_WorkBench.ui", self)
    
    self._model = None
    self.selectAllCheckBox.clicked.connect(self._setOverallCheckedState)
    self.launchButton.clicked.connect(self._launch)
    self.openButton.clicked.connect(self._open)    
    self.deleteButton.clicked.connect(self._delete)
    self.movieButton.clicked.connect(self._setMovieMode)
    self.tvButton.clicked.connect(self._setTvMode)
    
  def _setModel(self, m):
    self._model = m
    self._model.workBenchChangedSignal.connect(self._onWorkBenchChanged)
    self._onWorkBenchChanged(False)
    self._model.beginUpdateSignal.connect(self.startWorkBenching)
    self._model.endUpdateSignal.connect(self.stopWorkBenching)      
    
  def _setMovieMode(self):
    self.modeChangedSignal.emit(interfaces.Mode.MOVIE_MODE)

  def _setTvMode(self):
    self.modeChangedSignal.emit(interfaces.Mode.TV_MODE)
    
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
    self.editSeasonButton.setEnabled(False)
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
  
  def setConfig(self, data, mode=None):
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
  def __init__(self, parent=None):
    super(TvWorkBenchWidget, self).__init__(interfaces.Mode.TV_MODE, parent)
    self._setModel(model.TvModel(self.tvView))

    self._changeEpisodeWidget = changeEpisodeWidget.ChangeEpisodeWidget(self)
    self._changeEpisodeWidget.accepted.connect(self._onChangeEpisodeFinished)
    
    self._changeSeasonWidget = changeSeasonWidget.ChangeSeasonWidget(self)
    self._changeSeasonWidget.accepted.connect(self._onChangeSeasonFinished)
        
    self.tvView.setModel(self._model)
    self.tvView.header().setResizeMode(model.Columns.COL_NEW_NAME, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(model.Columns.COL_OLD_NAME, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(model.Columns.COL_NEW_NUM, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(model.Columns.COL_STATUS, QtGui.QHeaderView.Interactive)
    self.tvView.header().setStretchLastSection(True)
    #self.tvView.setItemDelegateForColumn(model.Columns.COL_NEW_NAME, model.SeriesDelegate(self))
    
    self.tvView.selectionModel().selectionChanged.connect(self._onSelectionChanged)
    self.tvView.doubleClicked.connect(self._onTvDoubleClicked)
    self.editEpisodeButton.clicked.connect(self._editEpisode)
    self.editSeasonButton.clicked.connect(self._editSeason)
    
    self.movieView.setVisible(False)
    self.tvButton.setVisible(False)  
    self.editMovieButton.setVisible(False)
    self.movieGroupBox.setVisible(False)
    
  def _launch(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, model.RAW_DATA_ROLE)
    assert(isMoveItemCandidate)
    self._launchLocation(moveItemCandidateData.source.filename)
  
  def _open(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      f = fileHelper.FileHelper.dirname(moveItemCandidateData.source.filename)
    else:
      f = moveItemCandidateData.inputFolder
    self._launchLocation(f)
    
  def getConfig(self):
    return {"cache" : seasonHelper.SeasonHelper.cache(),
            "state" : utils.toString(self.tvView.header().saveState().toBase64()),
            "use_cache" : self._changeSeasonWidget.useCacheCheckBox.isChecked() }
  
  def setConfig(self, data, mode=None):
    utils.verifyType(data, dict)
    seasonHelper.SeasonHelper.setCache(data.get("cache", {}))
    self._changeSeasonWidget.useCacheCheckBox.setChecked(data.get("use_cache", True))
    self.tvView.header().restoreState(QtCore.QByteArray.fromBase64(data.get("state", "")))
    
  def stopExploring(self):
    super(TvWorkBenchWidget, self).stopExploring()
    self.tvView.expandAll()
            
  def _onSelectionChanged(self, selection):
    indexes = selection.indexes()
    self._currentIndex = selection.indexes()[0] if selection.indexes() else None
    if bool(self._currentIndex):
      moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, model.RAW_DATA_ROLE)
      #filthy. check if parent has season info
      canEditEp = (isMoveItemCandidate and moveItemCandidateData.canEdit and 
                  bool(self._model.data(self._currentIndex.parent(), model.RAW_DATA_ROLE)[0].destination.matches))
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
    moveItemCandidateData, isMoveItemCandidate = self._model.data(modelIndex, model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      if (isMoveItemCandidate and moveItemCandidateData.canEdit and 
          bool(self._model.data(modelIndex.parent(), model.RAW_DATA_ROLE)[0].destination.matches)):
        self._editEpisode()
      else:
        QtGui.QMessageBox.information(self, "Can not edit Episode", 
                                      "Episodes can only be edited for existing files where Season data has been defined.")
    else:
      self._editSeason()
        
  def _editSeason(self):
    seasonData, isMoveItemCandidate = self._model.data(self._currentIndex, model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      self._currentIndex  = self._currentIndex.parent()
      seasonData, isMoveItemCandidate = self._model.data(self._currentIndex, model.RAW_DATA_ROLE)
    utils.verify(not isMoveItemCandidate, "Must be a movie to have gotten here!")
    self._changeSeasonWidget.setData(seasonData)
    self._changeSeasonWidget.show()
  
  def _editEpisode(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, model.RAW_DATA_ROLE)
    if isMoveItemCandidate and moveItemCandidateData.canEdit:
      seasonData, isMoveItemCandidate = self._model.data(self._currentIndex.parent(), model.RAW_DATA_ROLE)
      utils.verify(not isMoveItemCandidate, "Must be move item")
      self._changeEpisodeWidget.setData(seasonData, moveItemCandidateData)
      self._changeEpisodeWidget.show()
      
  def _onChangeEpisodeFinished(self):
    newKey = self._changeEpisodeWidget.episodeNumber()
    self._model.setData(self._currentIndex, QtCore.QVariant(newKey), model.RAW_DATA_ROLE)
    self.tvView.expand(self._currentIndex.parent())
    
  def _onChangeSeasonFinished(self):
    data = self._changeSeasonWidget.data()
    utils.verifyType(data, season.Season)
    seasonHelper.SeasonHelper.setSeasonInfo(data.seasonName, data.seasonNum, data.destination)    
    self._model.setData(self._currentIndex, data, model.RAW_DATA_ROLE)
    self.tvView.expand(self._currentIndex)
    
  def _delete(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      f = moveItemCandidateData.source.filename
    else:
      f = moveItemCandidateData.inputFolder
    if self._deleteLocation(f):
      self._model.delete(self._currentIndex)
  
    
# --------------------------------------------------------------------------------------------------------------------
class MovieWorkBenchWidget(BaseWorkBenchWidget):
  def __init__(self, parent=None):
    super(MovieWorkBenchWidget, self).__init__(interfaces.Mode.MOVIE_MODE, parent)
    self._setModel(movieModel.MovieModel(self.movieView))
    
    self._changeMovieWidget = changeMovieWidget.ChangeMovieWidget(self)
    self._changeMovieWidget.accepted.connect(self._onChangeMovieFinished)    
    
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
    self.movieView.clicked.connect(self._onMovieClicked)
    self.movieView.doubleClicked.connect(self._editMovie)
    self.editMovieButton.clicked.connect(self._editMovie)
    
    self._requireYearChanged(self.yearCheckBox.isChecked())
    self._requireGenreChanged(self.genreCheckBox.isChecked())
    self._flagDuplicateChanged(self.duplicateCheckBox.isChecked())
    
    self.tvView.setVisible(False)
    self.movieButton.setVisible(False)  
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
    return {"cache" : movieHelper.MovieHelper.cache(),
            "no_year_as_error" : self.yearCheckBox.isChecked(),
            "no_genre_as_error" : self.genreCheckBox.isChecked(),
            "duplicate_as_error" : self.duplicateCheckBox.isChecked(),
            "state" : utils.toString(self.movieView.horizontalHeader().saveState().toBase64()) }
  
  def setConfig(self, data, mode=None):
    utils.verifyType(data, dict)
    movieHelper.MovieHelper.setCache(data.get("cache", {}))
    self.yearCheckBox.setChecked(data.get("no_year_as_error", True))
    self.genreCheckBox.setChecked(data.get("no_genre_as_error", True))
    self.duplicateCheckBox.setChecked(data.get("duplicate_as_error", True)),
    self.movieView.horizontalHeader().restoreState(QtCore.QByteArray.fromBase64(data.get("state", "")))

  def _currentMovieModelIndex(self, index):
    return self._sortModel.mapToSource(index)
      
  def _onMovieClicked(self, index):
    self.launchButton.setEnabled(True)
    self.openButton.setEnabled(True)
    self.deleteButton.setEnabled(True)
    self._currentIndex = self._currentMovieModelIndex(index)
      
  def _editMovie(self):
    movie = self._model.data(self._currentIndex, movieModel.RAW_DATA_ROLE)
    utils.verifyType(movie, movieHelper.Movie)
    self._changeMovieWidget.setData(movie)
    self._changeMovieWidget.show()    
      
  def _onChangeMovieFinished(self):
    data = self._changeMovieWidget.data()    
    utils.verifyType(data, movieHelper.Movie)
    movieHelper.MovieHelper.setItem(data)
    self._model.setData(self._currentIndex, data, model.RAW_DATA_ROLE)
    
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
  