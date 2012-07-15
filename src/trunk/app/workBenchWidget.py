#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore, QtGui, uic

from common import utils
from tv import model, seasonHelper

import changeEpisodeWidget
import changeSeasonWidget

# --------------------------------------------------------------------------------------------------------------------
class WorkBenchWidget(QtGui.QWidget):
  workBenchChangedSignal_ = QtCore.pyqtSignal(bool)
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui = uic.loadUi("ui/ui_WorkBench.ui", self)
    
    self._changeEpisodeWidget = changeEpisodeWidget.ChangeEpisodeWidget(self)
    self._changeEpisodeWidget.accepted.connect(self._onChangeEpisodeFinished)
    
    self._changeSeasonWidget_ = changeSeasonWidget.ChangeSeasonWidget(self)
    self._changeSeasonWidget_.accepted.connect(self._onChangeSeasonFinished)
    
    self._model = model.TreeModel(self)
    self._ui.view_.setModel(self._model)
    self._ui.view_.header().setResizeMode(model.Columns.COL_NEW_NAME, QtGui.QHeaderView.Stretch)
    self._ui.view_.header().setResizeMode(model.Columns.COL_OLD_NAME, QtGui.QHeaderView.Stretch)
    self._ui.view_.header().setResizeMode(model.Columns.COL_STATUS, QtGui.QHeaderView.Stretch)
    self._ui.view_.header().setStretchLastSection(True)
    self._model.workBenchChangedSignal_.connect(self._onWorkBenchChanged)
    
    self._ui.view_.clicked.connect(self._onClicked)
    self._ui.view_.doubleClicked.connect(self._onDoubleClicked)
    self._ui.editEpisodeButton_.clicked.connect(self._editEpisode)
    self._ui.editSeasonButton_.clicked.connect(self._editSeason)
    
    self._ui.editEpisodeButton_.setEnabled(False)
    self._ui.editSeasonButton_.setEnabled(False)
    self._ui.selectAllCheckBox_.setEnabled(False)
    self._ui.selectAllCheckBox_.clicked.connect(self._model.setOverallCheckedState)
        
  def addSeason(self, season):
    self._model.addSeason(season)
    self._ui.view_.expandAll()
    
  def setSeasons(self, seasons):
    self._model.setSeasons(seasons)
    self._ui.view_.expandAll()
    self._ui.editEpisodeButton_.setEnabled(False)
    self._ui.editSeasonButton_.setEnabled(False)
    
  def seasons(self):
    seasons = self._model.seasons()
    return seasons
  
  def getConfig(self):
    return {"cache": seasonHelper.SeasonHelper.cache()}
  
  def setConfig(self, data):
    utils.verifyType(data, dict)
    seasonHelper.SeasonHelper.setCache(data.get("cache", {}))
    
  def _onClicked(self, modelIndex):
    self._currentIndex_ = modelIndex
    moveItemCandidateData, isMoveItemCandidate = self._model.data(modelIndex, model.RAW_DATA_ROLE)
    self._ui.editEpisodeButton_.setEnabled(isMoveItemCandidate and moveItemCandidateData.canEdit_)
    self._ui.editSeasonButton_.setEnabled(not isMoveItemCandidate)

  def _onDoubleClicked(self, modelIndex):
    utils.verifyType(modelIndex, QtCore.QModelIndex)
    moveItemCandidateData, isMoveItemCandidate = self._model.data(modelIndex, model.RAW_DATA_ROLE)
    if isMoveItemCandidate and moveItemCandidateData.canEdit_:
      self._editEpisode()
    else:
      self._editSeason()
        
  def _editSeason(self):
    seasonData, isMoveItemCandidate = self._model.data(self._currentIndex_, model.RAW_DATA_ROLE)
    if not isMoveItemCandidate: #maybe get the parent
      self._changeSeasonWidget_.setData(seasonData.inputFolder_, seasonData.seasonName_, seasonData.seasonNum_)
      self._changeSeasonWidget_.show()
  
  def _editEpisode(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._currentIndex_, model.RAW_DATA_ROLE)
    if isMoveItemCandidate and moveItemCandidateData.canEdit_:
      seasonData, isMoveItemCandidate = self._model.data(self._currentIndex_.parent(), model.RAW_DATA_ROLE)
      utils.verify(not isMoveItemCandidate, "Must be move item")
      self._changeEpisodeWidget.setData(seasonData, moveItemCandidateData)
      self._changeEpisodeWidget.show()
      
  def _onChangeEpisodeFinished(self):
    newKey = self._changeEpisodeWidget.episodeNumber()
    self._model.setData(self._currentIndex_, QtCore.QVariant(newKey), model.RAW_DATA_ROLE)
    
  def _onChangeSeasonFinished(self):
    showName = self._changeSeasonWidget_.showName()
    seasonNum = self._changeSeasonWidget_.seasonNumber()
    var = QtCore.QVariant.fromList([QtCore.QVariant(showName), QtCore.QVariant(seasonNum)])
    self._model.setData(self._currentIndex_, var, model.RAW_DATA_ROLE)
    
  def _onWorkBenchChanged(self, hasChecked):
    utils.verifyType(hasChecked, bool)
    cs = self._model.overallCheckedState()
    self._ui.selectAllCheckBox_.setEnabled(cs <> None)
    if cs == None:
      cs = QtCore.Qt.Unchecked
    self._ui.selectAllCheckBox_.setCheckState(cs)
    self.workBenchChangedSignal_.emit(hasChecked)
    