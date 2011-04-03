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

# --------------------------------------------------------------------------------------------------------------------
class OutputSettings():
  """"""
  def __init__(self):
    self.shouldOverwrite_ = False

  def toDictionary(self):
    return {"shouldOverwrite":self.shouldOverwrite_}

  def fromDictionary(self, dic):
    utils.verifyType(dic, dict)
    if dic.has_key("shouldOverwrite"): self.shouldOverwrite_ = dic["shouldOverwrite"]
      
# --------------------------------------------------------------------------------------------------------------------
class OutputWidget(QtGui.QWidget):
  """"""
  saveSignal_ = QtCore.pyqtSignal()
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_OutputWidget.ui", self)
    self.outputSettings_ = OutputSettings()
    self.dataItem_ = serializer.DataItem(self.outputSettings_.toDictionary())
    self.dataItem_.onChangedSignal_.connect(self._onStateChanged)
    self._ui_.saveButton_.clicked.connect(self.saveSignal_)
    self._onStateChanged()
    
  def _onStateChanged(self):
    self.outputSettings_.fromDictionary(self.dataItem_.data_)
    self._ui_.shouldOverwriteCheckBox_.setChecked(self.outputSettings_.shouldOverwrite_)
  
  
