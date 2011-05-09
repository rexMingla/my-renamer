#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import os

from PyQt4 import QtCore, QtGui, uic

from common import serializer, utils

# --------------------------------------------------------------------------------------------------------------------
class InputSettings():
  """"""
  def __init__(self):
    self.showRecursive_ = True
    self.folder_ = os.getcwd()
    self.extensions_ = ".avi"        

  def toDictionary(self):
    return {"folder"        :utils.toString(self.folder_),
            "showRecursive" :utils.toString(self.showRecursive_), 
            "extensions"    :utils.toString(self.extensions_)}

  def fromDictionary(self, dic):
    utils.verifyType(dic, dict)
    if dic.has_key("folder") and isinstance(dic["folder"], str):         
      self.folder_ = dic["folder"]
    if dic.has_key("showRecursive") and isinstance(dic["showRecursive"], str):   
      self.showRecursive_ = utils.strToBool(dic["showRecursive"])
    if dic.has_key("extensions") and isinstance(dic["extensions"], str): 
      self.extensions_ = dic["extensions"]
      
# --------------------------------------------------------------------------------------------------------------------
class InputWidget(QtGui.QWidget):
  """"""
  exploreSignal_ = QtCore.pyqtSignal()
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_InputWidget.ui", self)
    self.inputSettings_ = InputSettings()
    self.dataItem_ = serializer.DataItem(self.inputSettings_.toDictionary())
    self.dataItem_.onChangedSignal_.connect(self._onStateChanged)
    self._ui_.folderButton_.clicked.connect(self._showFolderSelectionDialog)
    self._ui_.loadButton_.clicked.connect(self.exploreSignal_)
    self._onStateChanged()
    
    self._ui_.folderEdit_.editingFinished.connect(self._readbackGUI)
    self._ui_.isRecursiveCheckBox_.toggled.connect(self._readbackGUI)
    self._ui_.fileExtensionEdit_.editingFinished.connect(self._readbackGUI)
    
    completer = QtGui.QCompleter(self)
    fsModel = QtGui.QFileSystemModel(completer)
    fsModel.setRootPath("")
    completer.setModel(fsModel)
    self._ui_.folderEdit_.setCompleter(completer)
    self._isUpdating = False
    
  def enableControls(self, isEnabled):
    self._ui_.loadButton_.setEnabled(isEnabled)
  
  def _readbackGUI(self):
    if not self._isUpdating:
      self.inputSettings_.folder_ = utils.toString(self._ui_.folderEdit_.text())
      self.inputSettings_.showRecursive_ = self._ui_.isRecursiveCheckBox_.isChecked()
      self.inputSettings_.extensions_ = utils.toString(self._ui_.fileExtensionEdit_.text())
      self.dataItem_.setData(self.inputSettings_.toDictionary())
    
  def _onStateChanged(self):
    self._isUpdating  = True
    self.inputSettings_.fromDictionary(self.dataItem_.data_)
    self._ui_.folderEdit_.setText(self.inputSettings_.folder_)
    self._ui_.isRecursiveCheckBox_.setChecked(self.inputSettings_.showRecursive_)
    self._ui_.fileExtensionEdit_.setText(self.inputSettings_.extensions_)    
    self._isUpdating  = False
      
  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self.inputSettings_.folder_)
    if folder:
      self.inputSettings_.folder_ = utils.toString(folder)
      self.dataItem_.setData(self.inputSettings_.toDictionary())
  
  
