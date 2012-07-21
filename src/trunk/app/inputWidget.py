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

from common import extension
from common import utils

import config
import interfaces
      
# --------------------------------------------------------------------------------------------------------------------
class InputWidget(interfaces.LoadWidgetInterface):
  """ Widget allowing for the configuration of source folders """
  exploreSignal = QtCore.pyqtSignal()
  stopSignal = QtCore.pyqtSignal()
  
  def __init__(self, parent=None):
    super(InputWidget, self).__init__("input", parent)
    uic.loadUi("ui/ui_InputWidget.ui", self)
    self.folderButton_.clicked.connect(self._showFolderSelectionDialog)
    self.findButton.clicked.connect(self.exploreSignal)
    self.folderEdit.returnPressed.connect(self.exploreSignal)
    self.fileExtensionEdit.returnPressed.connect(self.exploreSignal)
    self.stopButton.clicked.connect(self.stopSignal)
    
    completer = QtGui.QCompleter(self)
    fsModel = QtGui.QFileSystemModel(completer)
    fsModel.setRootPath("")
    completer.setModel(fsModel)
    self.folderEdit.setCompleter(completer)
    
    self.stopActioning()
    self.stopExploring()
    
  def _setMovieMode(self):
    pass #load cfg

  def _setTvMode(self):
    pass #load cfg
  
  def startExploring(self):
    self.progressBar.setValue(0)
    self.progressBar.setVisible(True)
    self.stopButton.setVisible(True)
    self.stopButton.setEnabled(True)
    self.findButton.setVisible(False)
  
  def stopExploring(self):
    self.progressBar.setVisible(False)
    self.stopButton.setVisible(False)
    self.findButton.setVisible(True)

  def startActioning(self):
    self.findButton.setEnabled(False)

  def stopActioning(self):
    self.findButton.setEnabled(True)

  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self.folderEdit.text())
    if folder:
      self.folderEdit.setText(folder)
      
  def getConfig(self):
    data = {"folder" : utils.toString(self.folderEdit.text()),
            "recursive" : self.isRecursiveCheckBox.isChecked(),
            "extensions" : utils.toString(self.fileExtensionEdit.text()) }
    return data
  
  def setConfig(self, data):
    self.folderEdit.setText(data.get("folder", ""))
    self.isRecursiveCheckBox.setChecked(data.get("recursive", True))
    self.fileExtensionEdit.setText(data.get("extensions", extension.DEFAULT_VIDEO_EXTENSIONS.extensionString()))
    
  
  
