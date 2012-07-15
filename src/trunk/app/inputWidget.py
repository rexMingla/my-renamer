#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: The input widget and settings
# --------------------------------------------------------------------------------------------------------------------
import os

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from common import utils
      
# --------------------------------------------------------------------------------------------------------------------
class InputWidget(QtGui.QWidget):
  """ Widget allowing for the configuration of source folders """
  exploreSignal = QtCore.pyqtSignal()
  stopSignal = QtCore.pyqtSignal()
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui = uic.loadUi("ui/ui_InputWidget.ui", self)
    self._ui.folderButton_.clicked.connect(self._showFolderSelectionDialog)
    self._ui.findButton.clicked.connect(self.exploreSignal)
    self._ui.stopButton.clicked.connect(self.stopSignal)
    
    completer = QtGui.QCompleter(self)
    fsModel = QtGui.QFileSystemModel(completer)
    fsModel.setRootPath("")
    completer.setModel(fsModel)
    self._ui.folderEdit.setCompleter(completer)
    
    self.stopSearching()
    
  def startSearching(self):
    self._ui.progressBar.setValue(0)
    self._ui.progressBar.setVisible(True)
    self._ui.stopButton.setVisible(True)
    self._ui.stopButton.setEnabled(True)
    self._ui.findButton.setVisible(False)
    
  def stopSearching(self):
    self._ui.progressBar.setVisible(False)
    self._ui.stopButton.setVisible(False)
    self._ui.findButton.setVisible(True)
    
  def enableControls(self, isEnabled):
    self._ui.findButton.setEnabled(isEnabled)

  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self._ui.folderEdit.text())
    if folder:
      self._ui.folderEdit.setText(folder)
      
  def getConfig(self):
    data = {"folder" : utils.toString(self._ui.folderEdit.text()),
            "recursive" : self._ui.isRecursiveCheckBox.isChecked(),
            "extensions" : utils.toString(self._ui.fileExtensionEdit.text()) }
    return data
  
  def setConfig(self, data):
    self._ui.folderEdit.setText(data.get("folder", os.getcwd()))
    self._ui.isRecursiveCheckBox.setChecked(data.get("recursive", True))
    self._ui.fileExtensionEdit.setText(data.get("extensions", ""))    
    
  def setProgress(self, progressComplete): 
    self._ui.progressBar.setProgress(progressComplete)
    
  
  
