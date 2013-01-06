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

from common import config
from common import extension
from common import utils

import interfaces
      
# --------------------------------------------------------------------------------------------------------------------
class InputWidget(interfaces.LoadWidgetInterface):
  """ Widget allowing for the configuration of source folders """
  exploreSignal = QtCore.pyqtSignal()
  stopSignal = QtCore.pyqtSignal()
  showEditSourcesSignal = QtCore.pyqtSignal()
  
  def __init__(self, mode, store, parent=None):
    super(InputWidget, self).__init__("input/{}".format(mode), parent)
    uic.loadUi("ui/ui_Input.ui", self)
    
    self._store = store
    self.folderButton.clicked.connect(self._showFolderSelectionDialog)
    self.searchButton.clicked.connect(self.exploreSignal)
    self.searchButton.setIcon(QtGui.QIcon("img/search.png"))
    self.folderEdit.returnPressed.connect(self.exploreSignal)
    self.fileExtensionEdit.returnPressed.connect(self.exploreSignal)
    self.stopButton.clicked.connect(self.stopSignal)
    self.stopButton.setIcon(QtGui.QIcon("img/stop.png"))
    self.restrictedExtRadioButton.toggled.connect(self.fileExtensionEdit.setEnabled)
    self.restrictedSizeRadioButton.toggled.connect(self.sizeSpinBox.setEnabled)
    self.restrictedSizeRadioButton.toggled.connect(self.sizeComboBox.setEnabled)
    self.sourceButton.clicked.connect(self.showEditSourcesSignal.emit)
    searchAction = QtGui.QAction(self.searchButton.text(), self)
    searchAction.setIcon(self.searchButton.icon())
    searchAction.setShortcut(QtCore.Qt.ControlModifier + QtCore.Qt.Key_F)
    searchAction.triggered.connect(self.exploreSignal.emit)
    self.addAction(searchAction)
    
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
    self.searchButton.setVisible(False)
  
  def stopExploring(self):
    self.progressBar.setVisible(False)
    self.stopButton.setVisible(False)
    self.searchButton.setVisible(True)

  def startActioning(self):
    self.searchButton.setEnabled(False)

  def stopActioning(self):
    self.searchButton.setEnabled(True)

  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self.folderEdit.text())
    if folder:
      self.folderEdit.setText(folder)
      
  def getConfig(self):
    data = config.InputConfig()
    data.folder = utils.toString(self.folderEdit.text())
    data.recursive = self.isRecursiveCheckBox.isChecked()
    data.allExtensions = self.anyExtRadioButton.isChecked()
    data.extensions = extension.FileExtensions(utils.toString(self.fileExtensionEdit.text())).extensionString()
    data.allFileSizes = self.anySizeRadioButton.isChecked()
    data.minFileSizeBytes = utils.stringToBytes("{} {}".format(self.sizeSpinBox.value(), self.sizeComboBox.currentText()))
    data.sources = self._store.getConfig()
    return data
  
  def setConfig(self, data):
    data = data or config.InputConfig()
    
    self.folderEdit.setText(data.folder or os.path.abspath(os.path.curdir))
    self.isRecursiveCheckBox.setChecked(data.recursive)
    if data.allExtensions:
      self.anyExtRadioButton.setChecked(True)
    else:
      self.restrictedExtRadioButton.setChecked(True)
    if data.allFileSizes:
      self.anySizeRadioButton.setChecked(True)
    else:
      self.restrictedSizeRadioButton.setChecked(True)
    self.fileExtensionEdit.setText(data.extensions)
    fileSize, fileDenom = utils.bytesToString(data.minFileSizeBytes).split()
    self.sizeSpinBox.setValue(int(float(fileSize)))
    self.sizeComboBox.setCurrentIndex(self.sizeComboBox.findText(fileDenom))
    self._store.setConfig(data.sources or [])
    self.onSourcesWidgetFinished()
    
  def onSourcesWidgetFinished(self):
    sources = self._store.getAllActiveNames()
    self.sourcesEdit.setText(", ".join(sources))
    #todo: act if == None
  
  
