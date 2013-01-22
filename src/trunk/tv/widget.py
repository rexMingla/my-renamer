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

import copy

from common import config
from common import file_helper
from common import interfaces
from common import thread
from common import utils

from base import client as base_client
from base import widget as base_widget

from tv import types as tv_types
from tv import client as tv_client
from tv import model as tv_model

_TITLE_COLUMN = 0

# --------------------------------------------------------------------------------------------------------------------
class TvWorkBenchWidget(base_widget.BaseWorkBenchWidget):
  def __init__(self, manager, parent=None):
    super(TvWorkBenchWidget, self).__init__(interfaces.Mode.TV_MODE, manager, parent)
    self._setModel(tv_model.TvModel(self.tvView))

    self._changeEpisodeWidget = EditEpisodeWidget(self)
    self._changeEpisodeWidget.accepted.connect(self._onChangeEpisodeFinished)
    
    self._changeSeasonWidget = EditSeasonWidget(self)
    self._changeSeasonWidget.accepted.connect(self._onChangeSeasonFinished)
    self._changeSeasonWidget.showEditSourcesSignal.connect(self.showEditSourcesSignal.emit)
        
    self.tvView.setModel(self._model)
    self.tvView.header().setResizeMode(tv_model.Columns.COL_NEW_NAME, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(tv_model.Columns.COL_OLD_NAME, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(tv_model.Columns.COL_NEW_NUM, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(tv_model.Columns.COL_STATUS, QtGui.QHeaderView.Interactive)
    self.tvView.header().setStretchLastSection(True)
    #self.tvView.setItemDelegateForColumn(tv_model.Columns.COL_NEW_NAME, tv_model.SeriesDelegate(self))
    
    self.tvView.selectionModel().selectionChanged.connect(self._onSelectionChanged)
    self.tvView.doubleClicked.connect(self._showItem)
    
    self.movieView.setVisible(False)
    self.movieGroupBox.setVisible(False)
    self._onSelectionChanged()
    
  def getConfig(self):
    ret = config.TvWorkBenchConfig()
    ret.state = utils.toString(self.tvView.header().saveState().toBase64())
    return ret
  
  def setConfig(self, data):
    data = data or config.TvWorkBenchConfig()
    self.tvView.header().restoreState(QtCore.QByteArray.fromBase64(data.state))
    
  def stopExploring(self):
    super(TvWorkBenchWidget, self).stopExploring()
    self.tvView.expandAll()
            
  def _onSelectionChanged(self, selection=None):
    selection = selection or self.tvView.selectionModel().selection()
    indexes = selection.indexes()
    self._currentIndex = indexes[0] if indexes else QtCore.QModelIndex()
    self._updateActions()
    self.renameItemChangedSignal.emit(self._model.getRenameItem(self._currentIndex))
    
  def _showItem(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, tv_model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      if self._model.canEdit(self._currentIndex):
        self._editEpisode()
      else:
        QtGui.QMessageBox.information(self, "Can not edit Episode", 
                                      "Episodes can only be edited for existing files where Season data has been defined.")
    else:
      self._editSeason()
        
  def _editSeason(self):
    seasonData, isMoveItemCandidate = self._model.data(self._currentIndex, tv_model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      self._currentIndex  = self._currentIndex.parent()
      seasonData, isMoveItemCandidate = self._model.data(self._currentIndex, tv_model.RAW_DATA_ROLE)
    utils.verify(not isMoveItemCandidate, "Must be a movie to have gotten here!")
    self._changeSeasonWidget.setData(seasonData)
    self._changeSeasonWidget.show()
  
  def _editEpisode(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, tv_model.RAW_DATA_ROLE)
    if isMoveItemCandidate and moveItemCandidateData.canEdit:
      seasonData, isMoveItemCandidate = self._model.data(self._currentIndex.parent(), tv_model.RAW_DATA_ROLE)
      utils.verify(not isMoveItemCandidate, "Must be move item")
      self._changeEpisodeWidget.setData(seasonData, moveItemCandidateData)
      self._changeEpisodeWidget.show()
      
  def _onChangeEpisodeFinished(self):
    self._model.setData(self._currentIndex, self._changeEpisodeWidget.episodeNumber(), tv_model.RAW_DATA_ROLE)
    self.tvView.expand(self._currentIndex.parent())
    self._onSelectionChanged()
    
  def _onChangeSeasonFinished(self):
    data = self._changeSeasonWidget.data()
    #utils.verifyType(data, tv_types.Season)
    self._manager.setItem(data.getInfo())
    self._model.setData(self._currentIndex, data, tv_model.RAW_DATA_ROLE)
    self.tvView.expand(self._currentIndex)

# --------------------------------------------------------------------------------------------------------------------
class GetSeasonThread(thread.WorkerThread):
  def __init__(self, searchParams, store, isLucky):
    super(GetSeasonThread, self).__init__("tv search")
    self._searchParams = searchParams
    self._store = store
    self._isLucky = isLucky

  def run(self):
    for info in self._store.getInfos(self._searchParams):
      self._onData(info)
      if self._userStopped or (info and self._isLucky):
        break
    
# --------------------------------------------------------------------------------------------------------------------
class EditSeasonWidget(QtGui.QDialog):
  showEditSourcesSignal = QtCore.pyqtSignal()
  """ The widget allows the user to search and modify tv info. """
  def __init__(self, parent=None):
    super(QtGui.QDialog, self).__init__(parent)
    uic.loadUi("ui/ui_ChangeSeason.ui", self)
    self.setWindowModality(True)
    self._workerThread = None
    self._data = tv_types.Season("", tv_types.SeasonInfo(), tv_types.SourceFiles())
    
    self.searchButton.clicked.connect(self._search)
    self.searchButton.setIcon(QtGui.QIcon("img/search.png"))
    self.stopButton.clicked.connect(self._stopThread)
    self.stopButton.setIcon(QtGui.QIcon("img/stop.png"))
    self.addButton.clicked.connect(self._add)
    self.removeButton.clicked.connect(self._remove)
    self.upButton.clicked.connect(self._moveUp)
    self.downButton.clicked.connect(self._moveDown)
    self.episodeTable.cellClicked.connect(self._onSelectionChanged)
    self.indexSpinBox.valueChanged.connect(self._updateColumnHeaders)
    self.hideLabel.linkActivated.connect(self._hideResults)    
    self.showLabel.linkActivated.connect(self._showResults)    
    self.sourceButton.clicked.connect(self.showEditSourcesSignal.emit)    

    self.seasonEdit.installEventFilter(self)
    self.seasonSpin.installEventFilter(self)

    self._searchResults = base_widget.SearchResultsWidget(self)
    self._searchResults.itemSelectedSignal.connect(self._setSeasonInfo)
    lo = QtGui.QVBoxLayout()
    lo.setContentsMargins(0, 0, 0, 0)
    self.placeholderWidget.setLayout(lo)
    lo.addWidget(self._searchResults)
    
    self._isLucky = False
    self._foundData = True    
    self._onThreadFinished()
    self._hideResults()    
    self.showLabel.setVisible(False)
    
  def __del__(self):
    self._isShuttingDown = True
    self._stopThread()
    
  def showEvent(self, e):
    self._foundData = True    
    self._onThreadFinished()
    self._hideResults()    
    self.showLabel.setVisible(False)    
    super(EditSeasonWidget, self).showEvent(e)
    
  def eventFilter(self, o, e):
    if o in (self.seasonSpin, self.seasonEdit) and \
      e.type() == QtCore.QEvent.KeyPress and e.key() == QtCore.Qt.Key_Return:
      e.ignore()
      self._search()
      return False
    return super(EditSeasonWidget, self).eventFilter(o, e)  
    
  def _search(self):
    if self._workerThread and self._workerThread.isRunning():
      return
    self._isLucky = self.luckyCheckBox.isChecked()
    self._foundData = False

    self.searchButton.setVisible(False)
    self.stopButton.setEnabled(True)
    self.stopButton.setVisible(True)
    self.episodesGroupBox.setEnabled(False)
    self.buttonBox.setEnabled(False)
    self.placeholderWidget.setEnabled(False)    
    self.progressBar.setVisible(True)
    
    self._workerThread = GetSeasonThread(tv_types.TvSearchParams(utils.toString(self.seasonEdit.text()), 
                                                                     self.seasonSpin.value()),
                                         tv_client.getStoreHolder(),
                                         self._isLucky)
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
    self.placeholderWidget.setEnabled(True)
    self.progressBar.setVisible(False)

    self._onSelectionChanged()
    if not self._foundData:
      QtGui.QMessageBox.information(self, "Nothing found", "No results found for search")    
    
  def _onDataFound(self, data):
    if not data:
      return
    
    if self._isLucky:
      self._setSeasonInfo(data.info)
    else:
      if not self._foundData:
        self._searchResults.clear()
        self._searchResults.addItem(base_client.ResultHolder(self.data().info, "current"))
      self._searchResults.addItem(data)
      self._showResults()
    self._foundData = True
    
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
    self._onSelectionChanged()
    
  def _moveUp(self):
    currentItem = self.episodeTable.currentItem()
    utils.verify(currentItem, "Must have current item to get here")
    nextItem = self.episodeTable.item(currentItem.row() - 1, _TITLE_COLUMN)
    temp = nextItem.text()
    nextItem.setText(currentItem.text())
    currentItem.setText(temp)
    self.episodeTable.setCurrentItem(nextItem)
    self._onSelectionChanged()
  
  def _add(self):
    currentItem = self.episodeTable.currentItem()
    row = currentItem.row() if currentItem else self.episodeTable.rowCount()
    item = QtGui.QTableWidgetItem("")
    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)    
    #self.episodeTable.setRowCount(self.episodeTable.rowCount() + 1)
    self.episodeTable.insertRow(row)
    self.episodeTable.setItem(row, _TITLE_COLUMN, item)
    self._onSelectionChanged()
    self._updateColumnHeaders()
  
  def _remove(self):
    currentItem = self.episodeTable.currentItem()
    utils.verify(currentItem, "Must have current item to get here")
    self.episodeTable.removeRow(currentItem.row())
    self._onSelectionChanged()
    self._updateColumnHeaders()
      
  def _updateColumnHeaders(self):
    startIndex = self.indexSpinBox.value()
    rowCount = self.episodeTable.rowCount()
    self.episodeTable.setVerticalHeaderLabels(map(str, range(startIndex, rowCount + startIndex)))
  
  def setData(self, s):
    """ Fill the dialog with the data prior to being shown """
    #utils.verifyType(s, tv_types.Season)
    self._data = s
    self.folderEdit.setText(file_helper.FileHelper.basename(s.inputFolder))    
    self.folderEdit.setToolTip(s.inputFolder)    
    self._setSeasonInfo(s.info)
    self.seasonEdit.selectAll()    
    
  def _setSeasonInfo(self, info):
    #utils.verifyType(info, tv_types.SeasonInfo)
    self.seasonEdit.setText(info.showName)
    self.seasonSpin.setValue(info.seasonNum)    
    self.episodeTable.clearContents()
    
    minValue = min([ep.epNum for ep in info.episodes] or [0])
    maxValue = max([ep.epNum for ep in info.episodes] or [-1])
    self.indexSpinBox.setValue(minValue)
    
    epNums = map(str, range(minValue, maxValue + 1))
    self.episodeTable.setRowCount(len(epNums))
    for i, epNum in enumerate(epNums):
      ep = info.episodes[i]
      item = QtGui.QTableWidgetItem(ep.epName)
      item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
      self.episodeTable.setItem(i, _TITLE_COLUMN, item)
    self._onSelectionChanged()
    
  def data(self):   
    info = tv_types.SeasonInfo(utils.toString(self.seasonEdit.text()), self.seasonSpin.value()) 
    startIndex = self.indexSpinBox.value()
    for i in range(self.episodeTable.rowCount()):
      epName = self.episodeTable.item(i, _TITLE_COLUMN)
      info.episodes.append(tv_types.EpisodeInfo(i + startIndex, utils.toString(epName.text())))
    self._data.updateSeasonInfo(info)
    return copy.copy(self._data)
  
  def _showResults(self):
    self.placeholderWidget.setVisible(True)
    self.hideLabel.setVisible(True)
    self.showLabel.setVisible(False)
  
  def _hideResults(self):
    self.placeholderWidget.setVisible(False)
    self.hideLabel.setVisible(False)
    self.showLabel.setVisible(True)

# --------------------------------------------------------------------------------------------------------------------
class EditEpisodeWidget(QtGui.QDialog):
  """ Allows the user to assign an episode to a given file """
  def __init__(self, parent=None):
    super(QtGui.QDialog, self).__init__(parent)
    self._ui = uic.loadUi("ui/ui_ChangeEpisode.ui", self)
    self.pickFromListRadio.toggled.connect(self.episodeComboBox.setEnabled)
    self.setWindowModality(True)
    
  def showEvent(self, event):
    """ protected Qt function """
    utils.verify(self.episodeComboBox.count() > 0, "No items in list")
    self.setMaximumHeight(self.sizeHint().height())
    self.setMinimumHeight(self.sizeHint().height())
  
  def setData(self, ssn, ep):
    """ Fill the dialog with the data prior to being shown """
    #utils.verifyType(ssn, tv_types.Season)
    #utils.verifyType(ep, tv_types.EpisodeRenameItem)
    self.episodeComboBox.clear()
    #episodeMoveItems = copy.copy(ssn.episodeMoveItems)
    #episodeMoveItems = sorted(episodeMoveItems, key=lambda item: item.info.epNum)
    for mi in ssn.episodeMoveItems:
      if mi.info.epNum != tv_types.UNRESOLVED_KEY:
        displayName = "{}: {}".format(mi.info.epNum, mi.info.epName)
        self.episodeComboBox.addItem(displayName, mi.info.epNum)
    index = self.episodeComboBox.findData(ep.info.epNum)
    if index != -1:
      self.pickFromListRadio.setChecked(True)
      self.episodeComboBox.setCurrentIndex(index)
    else:
      self.ignoreRadio.setChecked(True)
    self.filenameEdit.setText(file_helper.FileHelper.basename(ep.filename))
    self.filenameEdit.setToolTip(ep.filename)
    self.episodeComboBox.setEnabled(index != -1)
    
  def episodeNumber(self):
    """ 
    Returns the currently selected episode number from the dialog. 
    Returns tv_types.UNRESOLVED_KEY if non is selected. 
    """
    if self.ignoreRadio.isChecked():
      return tv_types.UNRESOLVED_KEY
    else:
      return self.episodeComboBox.itemData(self.episodeComboBox.currentIndex()).toInt()[0]