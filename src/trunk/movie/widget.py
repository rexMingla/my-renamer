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

from movie import model as movie_model
from movie import client as movie_client
from movie import types as movie_types

from base import client as base_client
from base import widget as base_widget

from common import config
from common import interfaces
from common import file_helper
from common import thread 
from common import utils

# --------------------------------------------------------------------------------------------------------------------
class MovieWorkBenchWidget(base_widget.BaseWorkBenchWidget):
  def __init__(self, manager, parent=None):
    super(MovieWorkBenchWidget, self).__init__(interfaces.Mode.MOVIE_MODE, manager, parent)
    self._setModel(movie_model.MovieModel(self.movieView))
    
    self._changeMovieWidget = EditMovieWidget(self)
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
     
  def get_config(self):
    ret = config.MovieWorkBenchConfig()
    ret.noYearAsError = self.yearCheckBox.isChecked()
    ret.noGenreAsError = self.genreCheckBox.isChecked()
    ret.duplicateAsError = self.duplicateCheckBox.isChecked()
    ret.state = utils.toString(self.movieView.horizontalHeader().saveState().toBase64())
    ret.seriesList = self._changeMovieWidget.getSeriesList()
    return ret
  
  def set_config(self, data):
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

# --------------------------------------------------------------------------------------------------------------------
class _GetMovieThread(thread.WorkerThread):
  """ search for movie from sources """
  
  def __init__(self, searchParams, isLucky):
    super(_GetMovieThread, self).__init__("movie search")
    self._searchParams = searchParams
    self._store = movie_client.getStoreHolder()
    self._isLucky = isLucky

  def run(self):
    for info in self._store.getInfos(self._searchParams):
      self._onData(info)
      if self._userStopped or (info and self._isLucky):
        break

# --------------------------------------------------------------------------------------------------------------------
class EditMovieWidget(QtGui.QDialog):
  """ The widget allows the user to search and modify movie info. """
  showEditSourcesSignal = QtCore.pyqtSignal()
  def __init__(self, parent=None):
    super(EditMovieWidget, self).__init__(parent)
    uic.loadUi("ui/ui_ChangeMovie.ui", self)
    self._workerThread = None
    self.setWindowModality(True)
    self.searchEdit.setPlaceholderText("Enter movie and year to search")
    self.searchEdit.installEventFilter(self)
    self.searchButton.clicked.connect(self._search)
    self.searchButton.setIcon(QtGui.QIcon("img/search.png"))
    
    self._searchResults = base_widget.SearchResultsWidget(self)
    self._searchResults.itemSelectedSignal.connect(self._setMovieInfo)
    lo = QtGui.QVBoxLayout()
    lo.setContentsMargins(0, 0, 0, 0)
    self.placeholderWidget.setLayout(lo)
    lo.addWidget(self._searchResults)

    self.hideLabel.linkActivated.connect(self._hideResults)    
    self.showLabel.linkActivated.connect(self._showResults)    
    self.stopButton.clicked.connect(self._stopThread)    
    self.stopButton.setIcon(QtGui.QIcon("img/stop.png"))
    self.partCheckBox.toggled.connect(self.partSpinBox.setEnabled)
    self.sourceButton.clicked.connect(self.showEditSourcesSignal.emit)    
    
    self._item = None
    self._isShuttingDown = False
    self._isLucky = False
    self._foundData = True
    self._onThreadFinished()
    self._hideResults()    
    self.showLabel.setVisible(False)
    self._seriesList = []
    
  def __del__(self):
    self._isShuttingDown = True
    self._stopThread()
        
  def accept(self):
    series = utils.toString(self.seriesEdit.text())
    if series and not series in self._seriesList:
      self._seriesList.append(series)
      self.setSeriesList(self._seriesList)    
    return super(EditMovieWidget, self).accept()
        
  def eventFilter(self, o, e):
    if o == self.searchEdit and e.type() == QtCore.QEvent.KeyPress and e.key() == QtCore.Qt.Key_Return:
      e.ignore()
      self._search()
      return False
    return super(EditMovieWidget, self).eventFilter(o, e)
    
  def showEvent(self, e):
    self._foundData = True    
    self._onThreadFinished()
    self._hideResults()    
    self.showLabel.setVisible(False)    
    super(EditMovieWidget, self).showEvent(e)  

  def _search(self):
    if self._workerThread and self._workerThread.isRunning():
      return
    self._isLucky = self.luckyCheckBox.isChecked()
    self._foundData = False

    self.searchButton.setVisible(False)
    self.stopButton.setEnabled(True)
    self.stopButton.setVisible(True)
    self.dataGroupBox.setEnabled(False)
    self.buttonBox.setEnabled(False)
    self.placeholderWidget.setEnabled(False)    
    self.progressBar.setVisible(True)
    
    search_text = utils.toString(self.searchEdit.text())
    self._workerThread = _GetMovieThread(movie_types.MovieSearchParams(search_text, self._isLucky))
    self._workerThread.newDataSignal.connect(self._onMovieInfo)
    self._workerThread.finished.connect(self._onThreadFinished)
    self._workerThread.terminated.connect(self._onThreadFinished)    
    self._workerThread.start()  
    
  def _stopThread(self):
    self.stopButton.setEnabled(False)
    if self._workerThread:
      self._workerThread.join()
    
  def _onThreadFinished(self):    
    self.stopButton.setVisible(False)
    self.searchButton.setVisible(True)
    self.searchButton.setEnabled(True)
    self.dataGroupBox.setEnabled(True)
    self.buttonBox.setEnabled(True)
    self.placeholderWidget.setEnabled(True)    
    self.progressBar.setVisible(False)   
    
    if not self._foundData:
      QtGui.QMessageBox.information(self, "Nothing found", "No results found for search")
    
  def _onMovieInfo(self, data):
    if not data:
      return
    
    if self._isLucky:
      self._setMovieInfo(data.info)
    else:
      if not self._foundData:
        self._searchResults.clear()
        self._searchResults.addItem(base_client.ResultHolder(self._getMovieInfo(), "current"))
      self._searchResults.addItem(data)
      self._showResults()
    self._foundData = True
    
  def _getMovieInfo(self):
    genreStr = utils.toString(self.genreEdit.text())
    return movie_types.MovieInfo(utils.toString(self.titleEdit.text()),
                                     utils.toString(self.yearEdit.text()),
                                     [genreStr] if genreStr else [])
      
  def _setMovieInfo(self, info):
    #utils.verifyType(info, movie_types.MovieInfo)
    self.titleEdit.setText(info.title)
    self.yearEdit.setText(info.year or "")
    self.genreEdit.setText(info.getGenre())  
    
  def setSeriesList(self, l):
    #utils.verifyType(l, list)
    self._seriesList = l
    completer = QtGui.QCompleter(self._seriesList, self)
    completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
    completer.setCompletionMode(QtGui.QCompleter.InlineCompletion)    
    self.seriesEdit.setCompleter(completer)        
    
  def getSeriesList(self):
    return self._seriesList
  
  def setData(self, item):
    """ Fill the dialog with the data prior to being shown """
    #utils.verifyType(item, movie_manager.MovieRenameItem)
    self._item = item  
    self.filenameEdit.setText(file_helper.FileHelper.basename(item.filename))
    self.filenameEdit.setToolTip(item.filename)
    info = item.info
    self.titleEdit.setText(info.title)
    self.searchEdit.setText(info.title)
    self.searchEdit.selectAll()
    self.yearEdit.setText(info.year or "")
    self.genreEdit.setText(info.getGenre(""))
    self.seriesEdit.setText(info.series)
    if info.part:
      self.partSpinBox.setValue(int(info.part))
    self.partCheckBox.setChecked(bool(info.part))
    
  def data(self):
    self._item.info.title = utils.toString(self.titleEdit.text())
    self._item.info.year = utils.toString(self.yearEdit.text())
    genre = utils.toString(self.genreEdit.text()).strip()
    if genre:
      genre = [genre]
    else:
      genre = []
    self._item.info.genres = genre
    self._item.info.part = None
    if self.partCheckBox.isChecked():
      self._item.info.part = self.partSpinBox.value()
    self._item.info.series = utils.toString(self.seriesEdit.text()).strip()
    return self._item
  
  def _showResults(self):
    self.placeholderWidget.setVisible(True)
    self.hideLabel.setVisible(True)
    self.showLabel.setVisible(False)
  
  def _hideResults(self):
    self.placeholderWidget.setVisible(False)
    self.hideLabel.setVisible(False)
    self.showLabel.setVisible(True)
  