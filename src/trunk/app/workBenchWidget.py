#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore, QtGui, uic

#import delegate
import changeEpisodeWidget
import changeSeasonWidget
import serializer
import utils
import model

# --------------------------------------------------------------------------------------------------------------------
class WorkBenchWidget(QtGui.QWidget):
  workBenchChangedSignal_ = QtCore.pyqtSignal(bool)
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_WorkBench.ui", self)
    #self._ui_.refreshButton_.clicked.connect(self._refresh)
    
    self._changeEpisodeWidget_ = changeEpisodeWidget.ChangeEpisodeWidget()
    self._changeEpisodeWidget_.accepted.connect(self._onChangeEpisodeFinished)
    
    self._changeSeasonWidget_ = changeSeasonWidget.ChangeSeasonWidget()
    self._changeSeasonWidget_.accepted.connect(self._onChangeSeasonFinished)
    
    self._model_ = model.TreeModel()
    self._ui_.view_.setModel(self._model_)
    self._ui_.view_.header().setResizeMode(model.Columns.COL_NEW_NAME, QtGui.QHeaderView.Stretch)
    self._ui_.view_.header().setResizeMode(model.Columns.COL_OLD_NAME, QtGui.QHeaderView.Stretch)
    self._ui_.view_.header().setResizeMode(model.Columns.COL_STATUS, QtGui.QHeaderView.Stretch)
    self._ui_.view_.header().setStretchLastSection(True)
    
    self._ui_.view_.clicked.connect(self._onClicked)
    self._ui_.view_.doubleClicked.connect(self._onDoubleClicked)
    self._ui_.editEpisodeButton_.clicked.connect(self._editEpisode)
    self._ui_.editSeasonButton_.clicked.connect(self._editSeason)
    
    self._ui_.editEpisodeButton_.setEnabled(False)
    self._ui_.editSeasonButton_.setEnabled(False)
    
    self._model_.workBenchChangedSignal_.connect(self.workBenchChangedSignal_)
    
  def _onClicked(self, modelIndex):
    self._currentIndex_ = modelIndex
    moveItemData, isMoveItem = self._model_.data(modelIndex, model.RAW_DATA_ROLE)
    self._ui_.editEpisodeButton_.setEnabled(isMoveItem and moveItemData.canEdit_)
    self._ui_.editSeasonButton_.setEnabled(not isMoveItem)

  def _onDoubleClicked(self, modelIndex):
    utils.verifyType(modelIndex, QtCore.QModelIndex)
    moveItemData, isMoveItem = self._model_.data(modelIndex, model.RAW_DATA_ROLE)
    if isMoveItem and moveItemData.canEdit_:
      self._editEpisode()
    else:
      self._editSeason()
        
  def _editSeason(self):
    seasonData, isMoveItem = self._model_.data(self._currentIndex_, model.RAW_DATA_ROLE)
    if not isMoveItem: #maybe get the parent
      self._changeSeasonWidget_.setData(seasonData.inputFolder_, seasonData.seasonName_, seasonData.seasonNum_)
      self._changeSeasonWidget_.show()
  
  def _editEpisode(self):
    moveItemData, isMoveItem = self._model_.data(self._currentIndex_, model.RAW_DATA_ROLE)
    if isMoveItem and moveItemData.canEdit_:
      seasonData, isMoveItem = self._model_.data(self._currentIndex_.parent(), model.RAW_DATA_ROLE)
      utils.verify(not isMoveItem, "Must be move item")
      self._changeEpisodeWidget_.setData(seasonData, moveItemData)
      self._changeEpisodeWidget_.show()
  
  def updateModel(self, seasons):
    self._model_.setSeasons(seasons)
    self._ui_.view_.expandAll()
    self._ui_.editEpisodeButton_.setEnabled(False)
    self._ui_.editSeasonButton_.setEnabled(False)
    
  def seasons(self):
    seasons = self._model_.seasons()
    return seasons
    
  def _onChangeEpisodeFinished(self):
    newKey = self._changeEpisodeWidget_.episodeNumber()
    self._model_.setData(self._currentIndex_, QtCore.QVariant(newKey), model.RAW_DATA_ROLE)
    
  def _onChangeSeasonFinished(self):
    seasonName = self._changeSeasonWidget_.seasonName()
    seasonNum = self._changeSeasonWidget_.seasonNumber()
    var = QtCore.QVariant.fromList([QtCore.QVariant(seasonName), QtCore.QVariant(seasonNum)])
    self._model_.setData(self._currentIndex_, var, model.RAW_DATA_ROLE)
    #newKey = self._changeEpisodeWidget_.episodeNumber()
    #index = self._currentIndex_.sibling(self._currentIndex_.row(), model.Columns.COL_NEW_NAME)
    #self._model_.setData(index, QtCore.QVariant(newKey), QtCore.Qt.EditRole)
    