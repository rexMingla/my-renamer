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

from common import utils
from movie import model as movieModel
from tv import model
from tv import seasonHelper

import changeEpisodeWidget
import changeSeasonWidget

# --------------------------------------------------------------------------------------------------------------------
class WorkBenchWidget(QtGui.QWidget):
  workBenchChangedSignal = QtCore.pyqtSignal(bool)
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    uic.loadUi("ui/ui_WorkBench.ui", self)
    
    self._changeEpisodeWidget = changeEpisodeWidget.ChangeEpisodeWidget(self)
    self._changeEpisodeWidget.accepted.connect(self._onChangeEpisodeFinished)
    
    self._changeSeasonWidget_ = changeSeasonWidget.ChangeSeasonWidget(self)
    self._changeSeasonWidget_.accepted.connect(self._onChangeSeasonFinished)
    
    self.movieModel = movieModel.MovieModel(self)
    self.movieView.setModel(self.movieModel)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_NEW_NAME, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_OLD_NAME, QtGui.QHeaderView.Interactive)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_YEAR, QtGui.QHeaderView.Fixed)
    self.movieView.horizontalHeader().resizeSection(movieModel.Columns.COL_YEAR, 75)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_DISC, QtGui.QHeaderView.Fixed)
    self.movieView.horizontalHeader().resizeSection(movieModel.Columns.COL_DISC, 75)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_STATUS, QtGui.QHeaderView.Fixed)
    self.movieView.horizontalHeader().resizeSection(movieModel.Columns.COL_STATUS, 75)
    self.movieView.horizontalHeader().setResizeMode(movieModel.Columns.COL_GENRE, QtGui.QHeaderView.Fixed)
    self.movieView.horizontalHeader().resizeSection(movieModel.Columns.COL_GENRE, 75)
    self.movieView.horizontalHeader().setStretchLastSection(True)
    self.movieView.verticalHeader().setDefaultSectionSize(20)
    self.movieModel.workBenchChangedSignal.connect(self._onWorkBenchChanged)
    
    self.tvModel = model.TvModel(self)
    self.tvView.setModel(self.tvModel)
    self.tvView.header().setResizeMode(model.Columns.COL_NEW_NAME, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(model.Columns.COL_OLD_NAME, QtGui.QHeaderView.Interactive)
    self.tvView.header().setResizeMode(model.Columns.COL_NEW_NUM, QtGui.QHeaderView.Fixed)
    self.tvView.header().resizeSection(model.Columns.COL_NEW_NUM, 75)
    self.tvView.header().setResizeMode(model.Columns.COL_STATUS, QtGui.QHeaderView.Fixed)
    self.tvView.header().resizeSection(model.Columns.COL_STATUS, 75)
    self.tvView.header().setStretchLastSection(True)
    self.tvModel.workBenchChangedSignal.connect(self._onWorkBenchChanged)    
    self.selectAllCheckBox.clicked.connect(self._setOverallCheckedState)
    
    self.tvView.clicked.connect(self._onTvClicked)
    self.tvView.doubleClicked.connect(self._onTvDoubleClicked)
    self.editEpisodeButton.clicked.connect(self._editEpisode)
    self.editSeasonButton.clicked.connect(self._editSeason)

    self.editEpisodeButton.setEnabled(False)
    self.editSeasonButton.setEnabled(False)
    self.selectAllCheckBox.setEnabled(False)
    
    self._currentModel = None
    
  def setCurrentModel(self, model):
    self._currentModel = model
    if self._currentModel:
      self._setOverallCheckedState(self._currentModel.overallCheckedState() != None)
    else:
      self._setOverallCheckedState(False)
        
  def getConfig(self):
    return {"cache": seasonHelper.SeasonHelper.cache()}
  
  def setConfig(self, data):
    utils.verifyType(data, dict)
    seasonHelper.SeasonHelper.setCache(data.get("cache", {}))
    
  def _onTvClicked(self, modelIndex):
    self._currentIndex_ = modelIndex
    moveItemCandidateData, isMoveItemCandidate = self.tvModel.data(modelIndex, model.RAW_DATA_ROLE)
    self.editEpisodeButton.setEnabled(isMoveItemCandidate and moveItemCandidateData.canEdit)
    self.editSeasonButton.setEnabled(not isMoveItemCandidate)

  def _onTvDoubleClicked(self, modelIndex):
    utils.verifyType(modelIndex, QtCore.QModelIndex)
    moveItemCandidateData, isMoveItemCandidate = self.tvModel.data(modelIndex, model.RAW_DATA_ROLE)
    if isMoveItemCandidate and moveItemCandidateData.canEdit:
      self._editEpisode()
    else:
      self._editSeason()
        
  def _editSeason(self):
    seasonData, isMoveItemCandidate = self.tvModel.data(self._currentIndex_, model.RAW_DATA_ROLE)
    if not isMoveItemCandidate: #maybe get the parent
      self._changeSeasonWidget_.setData(seasonData.inputFolder_, seasonData.seasonName, seasonData.seasonNum)
      self._changeSeasonWidget_.show()
  
  def _editEpisode(self):
    moveItemCandidateData, isMoveItemCandidate = self.tvModel.data(self._currentIndex_, model.RAW_DATA_ROLE)
    if isMoveItemCandidate and moveItemCandidateData.canEdit:
      seasonData, isMoveItemCandidate = self.tvModel.data(self._currentIndex_.parent(), model.RAW_DATA_ROLE)
      utils.verify(not isMoveItemCandidate, "Must be move item")
      self._changeEpisodeWidget.setData(seasonData, moveItemCandidateData)
      self._changeEpisodeWidget.show()
      
  def _onChangeEpisodeFinished(self):
    newKey = self._changeEpisodeWidget.episodeNumber()
    self.tvModel.setData(self._currentIndex_, QtCore.QVariant(newKey), model.RAW_DATA_ROLE)
    
  def _onChangeSeasonFinished(self):
    showName = self._changeSeasonWidget_.showName()
    seasonNum = self._changeSeasonWidget_.seasonNumber()
    var = QtCore.QVariant.fromList([QtCore.QVariant(showName), QtCore.QVariant(seasonNum)])
    self.tvModel.setData(self._currentIndex_, var, model.RAW_DATA_ROLE)
    
  def _setOverallCheckedState(self, state):
    if self._currentModel:
      self._currentModel.setOverallCheckedState(state)
    
  def _onWorkBenchChanged(self, hasChecked):
    utils.verifyType(hasChecked, bool)
    if not self._currentModel:
      return
    cs = self._currentModel.overallCheckedState()
    self.selectAllCheckBox.setEnabled(cs != None)
    if cs == None:
      cs = QtCore.Qt.Unchecked
    self.selectAllCheckBox.setCheckState(cs)
    self.workBenchChangedSignal.emit(hasChecked)
    