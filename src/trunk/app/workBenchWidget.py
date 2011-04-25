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
import serializer
import utils
import model

# --------------------------------------------------------------------------------------------------------------------
class WorkBenchWidget(QtGui.QWidget):
  """"""
  refreshSignal_ = QtCore.pyqtSignal(str, int)
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_WorkBench.ui", self)
    self._ui_.refreshButton_.clicked.connect(self._refresh)
    
    self._changeEpisodeWidget_ = changeEpisodeWidget.ChangeEpisodeWidget()
    self._changeEpisodeWidget_.accepted.connect(self._onChangeEpisodeFinished)
    
    self._model_ = model.TreeModel()
    self._ui_.view_.setModel(self._model_)
    self._ui_.view_.header().setResizeMode(model.Columns.COL_NEW_NAME, QtGui.QHeaderView.Stretch)
    self._ui_.view_.header().setResizeMode(model.Columns.COL_OLD_NAME, QtGui.QHeaderView.Stretch)
    self._ui_.view_.header().setResizeMode(model.Columns.COL_STATUS, QtGui.QHeaderView.Stretch)
    self._ui_.view_.header().setStretchLastSection(True)
    #cbDelegate = delegate.ComboBoxItemDelegate(self._ui_.view_)
    #self._ui_.view_.setItemDelegate(cbDelegate)
    
    self._ui_.view_.doubleClicked.connect(self._onDoubleClicked)
    
  def _onDoubleClicked(self, modelIndex):
    utils.verifyType(modelIndex, QtCore.QModelIndex)
    #table view to model index
    #get move item
    moveItemData, isMoveItem = self._model_.data(modelIndex, model.RAW_DATA_ROLE)
    self._currentIndex_ = modelIndex
    if isMoveItem:
      seasonData, isMoveItem = self._model_.data(modelIndex.parent(), model.RAW_DATA_ROLE)
      utils.verify(not isMoveItem, "Must be move item")
      self._changeEpisodeWidget_.setData(seasonData, moveItemData)
      self._changeEpisodeWidget_.show()
        
  def _refresh(self):
    pass
  
  def updateModel(self, seasons):
    self._model_.setSeasons(seasons)
    self._ui_.view_.expandAll()
    
  def _onChangeEpisodeFinished(self):
    newKey = self._changeEpisodeWidget_.episodeNumber()
    index = self._currentIndex_.sibling(self._currentIndex_.row(), model.Columns.COL_NEW_NAME)
    self._model_.setData(index, QtCore.QVariant(newKey), QtCore.Qt.EditRole)