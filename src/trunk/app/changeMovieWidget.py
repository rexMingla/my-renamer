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
from common import thread 
from common import utils
from movie import movieHelper
from movie import movieInfoClient

import searchResultsWidget

# --------------------------------------------------------------------------------------------------------------------
class GetMovieThread(thread.WorkerThread):
  def __init__(self, title, store, isLucky):
    super(GetMovieThread, self).__init__("movie search")
    self._title = title
    self._store = store
    self._isLucky = isLucky

  def run(self):
    for info in self._store.getInfos(self._title):
      self._onData(info)
      if info and self._isLucky:
        break

# --------------------------------------------------------------------------------------------------------------------
class ChangeMovieWidget(QtGui.QDialog):
  """
  The widget allows the user to select a movie info. Needs interactive search...
  """
  def __init__(self, parent=None):
    super(ChangeMovieWidget, self).__init__(parent)
    uic.loadUi("ui/ui_ChangeMovie.ui", self)
    self._workerThread = None
    self.setWindowModality(True)
    self.searchEdit.setPlaceholderText("Enter movie and year to search")
    self.searchEdit.installEventFilter(self)
    self.searchButton.clicked.connect(self._search)
    
    self._searchResults = searchResultsWidget.SearchResultsWidget(self)
    self._searchResults.itemSelectedSignal.connect(self._setMovieInfo)
    lo = QtGui.QVBoxLayout()
    lo.setContentsMargins(0, 0, 0, 0)
    self.placeholderWidget.setLayout(lo)
    lo.addWidget(self._searchResults)

    self.hideLabel.linkActivated.connect(self._hideResults)    
    self.showLabel.linkActivated.connect(self._showResults)    
    self.stopButton.clicked.connect(self._stopThread)    
    self.partCheckBox.toggled.connect(self.partSpinBox.setEnabled)
    
    self._isLucky = False
    self._foundData = True
    self._onThreadFinished()
    self._hideResults()    
    self.showLabel.setVisible(False)
    
  def eventFilter(self, o, e):
    if o == self.searchEdit and e.type() == QtCore.QEvent.KeyPress and e.key() == QtCore.Qt.Key_Return:
      e.ignore()
      self._search()
      return False
    return super(ChangeMovieWidget, self).eventFilter(o, e)
  
  def __del__(self):
    self._isShuttingDown = True
    self._stopThread()
    
  def showEvent(self, event):
    """ protected Qt function """
    self.setMaximumHeight(self.sizeHint().height())
    self.setMinimumHeight(self.sizeHint().height()) 
    
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
    
    self._workerThread = GetMovieThread(utils.toString(self.searchEdit.text()), movieInfoClient.getStore(), self._isLucky)
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
    if not self._foundData:
      QtGui.QMessageBox.information(self, "Nothing found", "No results found for search")
    
  def _onMovieInfo(self, data):
    if not data:
      return
    
    info, sourceName = data
    if self._isLucky:
      self._setMovieInfo(info)
    else:
      if not self._foundData:
        self._searchResults.clear()
        self._searchResults.addItem(self._getMovieInfo(), "current")
      self._searchResults.addItem(info, sourceName)
      self._showResults()
    self._foundData = True
    
  def _getMovieInfo(self):
    genreStr = utils.toString(self.genreEdit.text())
    return movieInfoClient.MovieInfo(utils.toString(self.titleEdit.text()),
                                     utils.toString(self.yearEdit.text()),
                                     [genreStr] if genreStr else [])
      
  def _setMovieInfo(self, info):
    utils.verifyType(info, movieInfoClient.MovieInfo)
    self.titleEdit.setText(info.title)
    self.yearEdit.setText(info.year or "")
    self.genreEdit.setText(info.genres[0] if info.genres else "")    
  
  def setData(self, item):
    """ Fill the dialog with the data prior to being shown """
    utils.verifyType(item, movieHelper.Movie)
    self.item = item  
    self.filenameEdit.setText(fileHelper.FileHelper.basename(item.filename))
    self.filenameEdit.setToolTip(item.filename)
    self.titleEdit.setText(item.title)
    self.yearEdit.setText(item.year or "")
    self.genreEdit.setText(item.genre())
    self.searchEdit.clear()
    self.searchEdit.setFocus()
    if item.part:
      self.partSpinBox.setValue(int(item.part))
    self.partCheckBox.setChecked(bool(item.part))
    
  def data(self):
    self.item.title = utils.toString(self.titleEdit.text())
    self.item.year = utils.toString(self.yearEdit.text())
    genre = utils.toString(self.genreEdit.text()).strip()
    if genre:
      genre = [genre]
    else:
      genre = []
    self.item.genres = genre
    self.item.part = None
    if self.partCheckBox.isChecked():
      self.item.part = self.partSpinBox.value()
    return self.item
  
  def _showResults(self):
    self.placeholderWidget.setVisible(True)
    self.hideLabel.setVisible(True)
    self.showLabel.setVisible(False)
  
  def _hideResults(self):
    self.placeholderWidget.setVisible(False)
    self.hideLabel.setVisible(False)
    self.showLabel.setVisible(True)


  