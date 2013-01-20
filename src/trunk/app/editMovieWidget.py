#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Allow the user to select an season for a given folder
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from common import fileHelper
from common import commonInfoClient
from common import interfaces
from common import thread 
from common import utils

from movie import movieInfoClient
from movie import movieTypes

import searchResultsWidget

# --------------------------------------------------------------------------------------------------------------------
class GetMovieThread(thread.WorkerThread):
  """ search for movie from sources """
  
  def __init__(self, searchParams, isLucky):
    super(GetMovieThread, self).__init__("movie search")
    self._searchParams = searchParams
    self._store = movieInfoClient.getStoreHolder()
    self._isLucky = isLucky

  def run(self):
    for info in self._store.getInfos(self._searchParams):
      self._onData(info)
      if self._userStopped or (info and self._isLucky):
        break

# --------------------------------------------------------------------------------------------------------------------
class EditMovieWidget(QtGui.QDialog):
  showEditSourcesSignal = QtCore.pyqtSignal()
  """ The widget allows the user to search and modify movie info. """
  def __init__(self, parent=None):
    super(EditMovieWidget, self).__init__(parent)
    uic.loadUi("ui/ui_ChangeMovie.ui", self)
    self._workerThread = None
    self.setWindowModality(True)
    self.searchEdit.setPlaceholderText("Enter movie and year to search")
    self.searchEdit.installEventFilter(self)
    self.searchButton.clicked.connect(self._search)
    self.searchButton.setIcon(QtGui.QIcon("img/search.png"))
    
    self._searchResults = searchResultsWidget.SearchResultsWidget(self)
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
    
    self._workerThread = GetMovieThread(movieTypes.MovieSearchParams(utils.toString(self.searchEdit.text())), self._isLucky)
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
        self._searchResults.addItem(commonInfoClient.ResultHolder(self._getMovieInfo(), "current"))
      self._searchResults.addItem(data)
      self._showResults()
    self._foundData = True
    
  def _getMovieInfo(self):
    genreStr = utils.toString(self.genreEdit.text())
    return movieTypes.MovieInfo(utils.toString(self.titleEdit.text()),
                                     utils.toString(self.yearEdit.text()),
                                     [genreStr] if genreStr else [])
      
  def _setMovieInfo(self, info):
    #utils.verifyType(info, movieTypes.MovieInfo)
    self.titleEdit.setText(info.title)
    self.yearEdit.setText(info.year or "")
    self.genreEdit.setText(info.genres[0] if info.genres else "")  
    
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
    #utils.verifyType(item, movieManager.MovieRenameItem)
    self._item = item  
    self.filenameEdit.setText(fileHelper.FileHelper.basename(item.filename))
    self.filenameEdit.setToolTip(item.filename)
    info = item.info
    self.titleEdit.setText(info.title)
    self.searchEdit.setText(info.title)
    self.searchEdit.selectAll()
    self.yearEdit.setText(info.year or "")
    self.genreEdit.setText(info.getGenre(""))
    self.seriesEdit.setText(info.series)
    if info.disc:
      self.partSpinBox.setValue(int(info.disc))
    self.partCheckBox.setChecked(bool(info.disc))
    
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
  