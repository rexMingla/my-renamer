#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Allow the user to select an season for a given folder
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui
from PyQt4 import uic

from common import fileHelper
from common import thread 
from common import utils
from movie import movieHelper

# --------------------------------------------------------------------------------------------------------------------
class GetMovieThread(thread.WorkerThread):
  def __init__(self, title, year, useCacheValue):
    super(GetMovieThread, self).__init__("movie search")
    self._title = title
    self._year = year
    self._useCacheValue = useCacheValue

  def run(self):
    destMap = movieHelper.MovieHelper.getItem(self._title, self._year, self._useCacheValue)
    self._onData(destMap)

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
    self.searchButton.clicked.connect(self._search)
    self.stopButton.clicked.connect(self._stopThread)    
    self.partCheckBox.toggled.connect(self.partSpinBox.setEnabled)
    self._onThreadFinished()
    
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
    self.searchButton.setVisible(False)
    self.stopButton.setEnabled(True)
    self.stopButton.setVisible(True)
    self.dataGroupBox.setEnabled(False)
    self.buttonBox.setEnabled(False)
    
    self._workerThread = GetMovieThread(utils.toString(self.titleEdit.text()), 
                                        self.yearEdit.text(), 
                                        self.useCacheCheckBox.isChecked())
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
    
  def _onMovieInfo(self, item):
    utils.verifyType(item, movieHelper.MovieInfo)
    if item.title and item.year:
      self.titleEdit.setText(item.title)
      self.yearEdit.setText(item.year or "")
      self.genreEdit.setText(item.genres[0] if item.genres else "")    
    else:
      QtGui.QMessageBox.information(self, "Nothing found", "No results found for search")
  
  def setData(self, item):
    """ Fill the dialog with the data prior to being shown """
    utils.verifyType(item, movieHelper.Movie)
    self.item = item  
    self.filenameEdit.setText(fileHelper.FileHelper.basename(item.filename))
    self.filenameEdit.setToolTip(item.filename)
    self.titleEdit.setText(item.title)
    self.yearEdit.setText(item.year or "")
    self.genreEdit.setText(item.genre())
    if item.part:
      self.partSpinBox.setValue(int(item.part))
    self.partCheckBox.setChecked(bool(item.part))
    
  def data(self):
    self.item.title = self.titleEdit.text()
    self.item.year = self.yearEdit.text()
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
    

  