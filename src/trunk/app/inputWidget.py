#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: The input widget and settings
# --------------------------------------------------------------------------------------------------------------------
import os

from PyQt4 import QtCore, QtGui, uic

from common import utils
      
# --------------------------------------------------------------------------------------------------------------------
class InputWidget(QtGui.QWidget):
  """ Widget allowing for the configuration of source folders """
  exploreSignal_ = QtCore.pyqtSignal()
  stopSignal_ = QtCore.pyqtSignal()
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_InputWidget.ui", self)
    self._ui_.folderButton_.clicked.connect(self._showFolderSelectionDialog)
    self._ui_.loadButton_.clicked.connect(self.exploreSignal_)
    self._ui_.stopButton_.clicked.connect(self.stopSignal_)
    
    completer = QtGui.QCompleter(self)
    fsModel = QtGui.QFileSystemModel(completer)
    fsModel.setRootPath("")
    completer.setModel(fsModel)
    self._ui_.folderEdit_.setCompleter(completer)
    
    self.stopSearching()
    
  def startSearching(self):
    self._ui_.progressBar_.setValue(0)
    self._ui_.progressBar_.setVisible(True)
    self._ui_.stopButton_.setVisible(True)
    self._ui_.stopButton_.setEnabled(True)
    self._ui_.loadButton_.setVisible(False)
    
  def stopSearching(self):
    self._ui_.progressBar_.setVisible(False)
    self._ui_.stopButton_.setVisible(False)
    self._ui_.loadButton_.setVisible(True)
    
  def enableControls(self, isEnabled):
    self._ui_.loadButton_.setEnabled(isEnabled)

  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self._ui_.folderEdit_.text())
    if folder:
      self._ui_.folderEdit_.setText(folder)
      
  def getConfig(self):
    data = {"folder" : utils.toString(self._ui_.folderEdit_.text()),
            "recursive" : self._ui_.isRecursiveCheckBox_.isChecked(),
            "extensions" : utils.toString(self._ui_.fileExtensionEdit_.text()) }
    return data
  
  def setConfig(self, data):
    self._ui_.folderEdit_.setText(data.get("folder", os.getcwd()))
    self._ui_.isRecursiveCheckBox_.setChecked(data.get("recursive", True))
    self._ui_.fileExtensionEdit_.setText(data.get("extensions", ""))    
    
  def setProgress(self, progressComplete): 
    self._ui_.inputProgressBar_.setProgress(progressComplete)
    if progress == 100:
      self._progressTimer.start()
    else:
      self._progressTimer.stop()
    
  
  
