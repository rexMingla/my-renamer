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

from common import thread
from common import utils
from tv import episode
from tv import season
from tv import seasonHelper

# --------------------------------------------------------------------------------------------------------------------
class GetSeasonThread(thread.WorkerThread):
  #progressSignal = QtCore.pyqtSignal(int)
  #logSignal = QtCore.pyqtSignal(object)
  #newDataSignal = QtCore.pyqtSignal(object)

  def __init__(self, seasonName, seasonNum):
    super(GetSeasonThread, self).__init__()
    self._seasonName = seasonName
    self._seaonsonNum = seasonNum

  def run(self):
    destMap = seasonHelper.SeasonHelper.getDestinationEpisodeMapFromTVDB(self._seasonName, self._seaonsonNum)
    if destMap:
      self._onData(destMap)

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
    self._onThreadFinished()
    
  def __del__(self):
    self._stopThread()

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
    
    self._workerThread = GetSeasonThread(utils.toString(self.seasonEdit.text()), self.seasonSpin.value())
    #self._workerThread.progressSignal.connect(self._inputWidget.progressBar.setValue)
    self._workerThread.newDataSignal.connect(self._setEpisodeMap)
    #self._workerThread.logSignal.connect(self._logWidget.appendMessage)
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
    
  def _onDataFound(self, data):
    self.setData(data)

  def _onItemSelected(self):
    pass #update widgets
    
  def _moveUp(self):
    pass
  
  def setData(self, s):
    """ Fill the dialog with the data prior to being shown """
    utils.verifyType(s, season.Season)
    self._data = s
    self.folderLabel.setText(s.inputFolder)
    self.seasonEdit.setText(s.seasonName)
    self.seasonSpin.setValue(s.seasonNum)
    self._setEpisodeMap(s.destination)
      
  def _setEpisodeMap(self, episodeMap):
    utils.verifyType(episodeMap, episode.EpisodeMap)
    self.episodeTable.clearContents()
    self.episodeTable.setRowCount(len(episodeMap.matches))
    for i, key in enumerate(sorted(episodeMap.matches)):
      item = QtGui.QTableWidgetItem(episodeMap.matches[key].epName)
      item.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
      self.episodeTable.setItem(i, 0, item)
    
  def data(self):    
    self.folderLabel.setText(s.inputFolder)
    self._data.seasonName = utils.toString(self.seasonEdit.text())
    self._data.seasonNum = self.seasonSpin.value()
    destMap = episode.EpisodeMap()
    for i in range(len(self.episodeTable.count())):
      sourceMap.addItem(episode.DestinationEpisode(i+1, utils.toString(item.text())))
    self._data.updateDestination(destMap)
    return copy.copy(self._data)

  