#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Allow the user to select an season for a given folder
# --------------------------------------------------------------------------------------------------------------------
import copy

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from common import fileHelper
from common import thread
from common import utils
from tv import episode
from tv import season
from tv import seasonHelper

_TITLE_COLUMN = 0

# --------------------------------------------------------------------------------------------------------------------
class GetSeasonThread(thread.WorkerThread):
  def __init__(self, seasonName, seasonNum, useCacheValue):
    super(GetSeasonThread, self).__init__()
    self._seasonName = seasonName
    self._seaonsonNum = seasonNum
    self._useCacheValue = useCacheValue

  def run(self):
    ret = seasonHelper.SeasonHelper.getSeasonInfo(self._seasonName, self._seaonsonNum, self._useCacheValue)
    self._onData(ret)

# --------------------------------------------------------------------------------------------------------------------
class ChangeSeasonWidget(QtGui.QDialog):
  """
  The widget allows the user to select an show name and season number for a given folder containing files.
  Unfortunately these is currently no way for the user to preview whether the show name and seaon number 
  are resovled by the web service.
  """
  def __init__(self, parent=None):
    super(QtGui.QDialog, self).__init__(parent)
    uic.loadUi("ui/ui_ChangeSeason.ui", self)
    self.setWindowModality(True)
    self._workerThread = None
    
    self.searchButton.clicked.connect(self._search)
    self.stopButton.clicked.connect(self._stopThread)
    self.addButton.clicked.connect(self._add)
    self.removeButton.clicked.connect(self._remove)
    self.upButton.clicked.connect(self._moveUp)
    self.downButton.clicked.connect(self._moveDown)
    self.episodeTable.cellClicked.connect(self._onSelectionChanged)
    self._onThreadFinished()
    
  def __del__(self):
    self._isShuttingDown = True
    self._stopThread()
    
  def _search(self):
    if self._workerThread and self._workerThread.isRunning():
      return
    self.searchButton.setVisible(False)
    self.stopButton.setEnabled(True)
    self.stopButton.setVisible(True)
    self.episodesGroupBox.setEnabled(False)
    self.buttonBox.setEnabled(False)
    self.useCacheCheckBox.setEnabled(False)
    
    self._workerThread = GetSeasonThread(utils.toString(self.seasonEdit.text()), 
                                         self.seasonSpin.value(),
                                         self.useCacheCheckBox.isChecked())
    self._workerThread.newDataSignal.connect(self._onDataFound)
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
    self.episodesGroupBox.setEnabled(True)
    self.buttonBox.setEnabled(True)
    self.useCacheCheckBox.setEnabled(True)
    self._onSelectionChanged()
    
  def _onDataFound(self, ret):
    seasonName, epMap = ret
    if epMap.matches:
      self.seasonEdit.setText(seasonName)
      self._setEpisodeMap(epMap)
    else:
      self._setEpisodeMap(episode.EpisodeMap())
      QtGui.QMessageBox.information(self, "Nothing found", "No results found for search")

  def _onSelectionChanged(self):
    currentIndex = self.episodeTable.currentItem().row() if self.episodeTable.currentItem() else -1
    self.removeButton.setEnabled(currentIndex != -1)
    self.upButton.setEnabled(currentIndex >= 1)
    self.downButton.setEnabled((currentIndex + 1) < self.episodeTable.rowCount())
    
  def _moveDown(self):
    currentItem = self.episodeTable.currentItem()
    utils.verify(currentItem, "Must have current item to get here")
    nextItem = self.episodeTable.item(currentItem.row() + 1, _TITLE_COLUMN)
    temp = nextItem.text()
    nextItem.setText(currentItem.text())
    currentItem.setText(temp)
    self.episodeTable.setCurrentItem(nextItem)
    
  def _moveUp(self):
    currentItem = self.episodeTable.currentItem()
    utils.verify(currentItem, "Must have current item to get here")
    nextItem = self.episodeTable.item(currentItem.row() - 1, _TITLE_COLUMN)
    temp = nextItem.text()
    nextItem.setText(currentItem.text())
    currentItem.setText(temp)
    self.episodeTable.setCurrentItem(nextItem)
  
  def _add(self):
    lastKey = str("0")
    rowCount = self.episodeTable.rowCount()
    if rowCount:
      lastKey = self.episodeTable.verticalHeaderItem(rowCount - 1).text()
    item = QtGui.QTableWidgetItem("")
    item.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
    
    self.episodeTable.setRowCount(rowCount + 1)
    self.episodeTable.setVerticalHeaderItem(rowCount, QtGui.QTableWidgetItem(str(int(lastKey) + 1)))
    self.episodeTable.setItem(rowCount, _TITLE_COLUMN, item)
  
  def _remove(self):
    currentItem = self.episodeTable.currentItem()
    utils.verify(currentItem, "Must have current item to get here")
    startIndex = int(self.episodeTable.verticalHeaderItem(0).text())
    self.episodeTable.removeRow(currentItem.row())
    rowCount = self.episodeTable.rowCount()
    if rowCount:
      self.episodeTable.setVerticalHeaderLabels(map(str, range(startIndex, rowCount + startIndex)))
  
  def setData(self, s):
    """ Fill the dialog with the data prior to being shown """
    utils.verifyType(s, season.Season)
    self._data = s
    self.folderEdit.setText(fileHelper.FileHelper.basename(s.inputFolder))    
    self.folderEdit.setToolTip(s.inputFolder)
    self.seasonEdit.setText(s.seasonName)
    self.seasonSpin.setValue(s.seasonNum)
    self._setEpisodeMap(s.destination)
      
  def _setEpisodeMap(self, episodeMap):
    utils.verifyType(episodeMap, episode.EpisodeMap)
    self.episodeTable.clearContents()
    
    minValue = min(map(int, episodeMap.matches) or [0])
    maxValue = max(map(int, episodeMap.matches) or [-1])
    
    epNums = map(str, range(minValue, maxValue + 1))
    self.episodeTable.setRowCount(len(epNums))
    self.episodeTable.setVerticalHeaderLabels(epNums)
    for i, epNum in enumerate(epNums):
      ep = episodeMap.matches.get(epNum, "")
      item = QtGui.QTableWidgetItem(ep.epName)
      item.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
      self.episodeTable.setItem(i, _TITLE_COLUMN, item)
    self._onSelectionChanged()
    
  def data(self):    
    destMap = episode.EpisodeMap() 
    for i in range(self.episodeTable.rowCount()):
      epName = self.episodeTable.item(i, _TITLE_COLUMN)
      destMap.addItem(episode.DestinationEpisode(int(self.episodeTable.verticalHeaderItem(i).text()), 
                                                 utils.toString(epName.text())))
    self._data.updateDestination(utils.toString(self.seasonEdit.text()), self.seasonSpin.value(), destMap)
    return copy.copy(self._data)

  