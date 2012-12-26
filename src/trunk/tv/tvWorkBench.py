#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui

from common import utils
from common import workBench

import season
import tvModel
import tvManager

from app import editEpisodeWidget
from app import editSeasonWidget
from app import interfaces

# --------------------------------------------------------------------------------------------------------------------
class TvWorkBenchWidget(workBench.BaseWorkBenchWidget):
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
    self.tvView.doubleClicked.connect(self._showItem)
    
    self.movieView.setVisible(False)
    self.movieGroupBox.setVisible(False)
    self._onSelectionChanged()
    
  def getConfig(self):
    return {"state" : utils.toString(self.tvView.header().saveState().toBase64()) }
  
  def setConfig(self, data):
    utils.verifyType(data, dict)
    self.tvView.header().restoreState(QtCore.QByteArray.fromBase64(data.get("state", "AAAA/wAAAAAAAAABAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA14AAAAFAQAAAQAAAAAAAAAAAAAAAGT/////AAAAgQAAAAAAAAAFAAABJQAAAAEAAAAAAAAAVgAAAAEAAAAAAAAA7QAAAAEAAAAAAAAAVwAAAAEAAAAAAAAAnwAAAAEAAAAA")))
    
  def stopExploring(self):
    super(TvWorkBenchWidget, self).stopExploring()
    self.tvView.expandAll()
            
  def _onSelectionChanged(self, selection=None):
    indexes = selection and selection.indexes()
    self._currentIndex = indexes[0] if indexes else None
    self._updateActions()
    
  def _showItem(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex, tvModel.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      if (isMoveItemCandidate and moveItemCandidateData.canEdit and 
          bool(self._model.data(self._currentIndex.parent(), tvModel.RAW_DATA_ROLE)[0].destination.matches)):
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
    