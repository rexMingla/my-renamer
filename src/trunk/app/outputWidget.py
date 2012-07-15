#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: The output widget and settings
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from common import fileHelper
from common import utils

from tv import outputFormat

USE_SOURCE_DIRECTORY = ""
      
# --------------------------------------------------------------------------------------------------------------------
class OutputWidget(QtGui.QWidget):
  """ Widget allowing for the configuration of output """
  renameSignal = QtCore.pyqtSignal()
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui = uic.loadUi("ui/ui_OutputWidget.ui", self)
    self._ui.renameButton.clicked.connect(self.renameSignal)
    self._ui.renameButton.setEnabled(False)
        
    self._ui.specificDirectoryButton.clicked.connect(self._showFolderSelectionDialog)
    
    self._ui.useSpecificDirectoryRadio.toggled.connect(self._ui.specificDirectoryEdit.setEnabled)
    self._ui.useSpecificDirectoryRadio.toggled.connect(self._ui.specificDirectoryButton.setEnabled)
    self._ui.formatEdit.textChanged.connect(self._updatePreviewText)
    self._updatePreviewText()
    
    completer = QtGui.QCompleter(self)
    fsModel = QtGui.QFileSystemModel(completer)
    fsModel.setRootPath("")
    completer.setModel(fsModel)
    self._ui.specificDirectoryEdit.setCompleter(completer)
    
    #tooltip
    toolTipText = ["Available options:"]
    for key, value in outputFormat.TvInputMap.exampleInputMap().data.items():
      toolTipText.append("%s -> %s" % (key, value))
    self._ui.formatEdit.setToolTip("\n".join(toolTipText))

    self.stopActioning()
    self._mode = None
    
  def setMode(self, mode):
    self._mode = mode
    
  def enableControls(self, isEnabled):
    self._ui.renameButton.setEnabled(isEnabled)
    
  def _updatePreviewText(self):
    text = utils.toString(self._ui.formatEdit.text())
    oFormat = outputFormat.OutputFormat(text)
    formattedText = oFormat.outputToString(outputFormat.TvInputMap.exampleInputMap())
    formattedText = "Example: %s" % fileHelper.FileHelper.sanitizeFilename(formattedText)
    self._ui.formatExampleLabel.setText(formattedText)
    
  def startActioning(self):
    self._ui.progressBar.setValue(0)    
    self._ui.progressBar.setVisible(True)
    self._ui.stopButton.setEnabled(True)
    self._ui.stopButton.setVisible(True)
    self._ui.renameButton.setVisible(False)

  def stopActioning(self):
    self._ui.progressBar.setVisible(False)
    self._ui.stopButton.setVisible(False)
    self._ui.renameButton.setVisible(True)    
      
  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self._ui.specificDirectoryEdit.text())
    if folder:
      self._ui.specificDirectoryEdit.setText(folder)

  def getConfig(self):
    outputDir = utils.toString(self._ui.specificDirectoryEdit.text())
    if self._ui.useSourceDirectoryRadio.isChecked():
      outputDir = USE_SOURCE_DIRECTORY    
    data = {"format" : utils.toString(self._ui.formatEdit.text()),
            "folder" : outputDir,
            "move" : self._ui.moveRadio.isChecked(),
            "dontOverwrite" : self._ui.doNotOverwriteCheckBox.isChecked()}
    return data
  
  def setConfig(self, data):
    self._ui.formatEdit.setText(data.get("format", outputFormat.TvInputMap.defaultFormatStr()))
    outputDir = data.get("folder", USE_SOURCE_DIRECTORY)
    self._ui.useSourceDirectoryRadio.setChecked(outputDir == USE_SOURCE_DIRECTORY)
    if outputDir != USE_SOURCE_DIRECTORY:
      self._ui.specificDirectoryEdit.setText(outputDir)
    self._ui.moveRadio.setChecked(data.get("move", True))
    self._ui.doNotOverwriteCheckBox.setChecked(data.get("dontOverwrite", True))