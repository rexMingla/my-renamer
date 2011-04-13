#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore, QtGui, uic

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
    
    self._model_ = model.TreeModel()
    self._ui_.view_.setModel(self._model_)
    
  def _refresh(self):
    pass
  
  def updateModel(self, seasons):
    self._model_.setSeasons(seasons + seasons)