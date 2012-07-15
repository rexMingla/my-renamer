#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: The output widget and settings
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore, QtGui, uic

from common import fileHelper, serializer, utils
from tv import outputFormat

USE_SOURCE_DIRECTORY = ""
      
# --------------------------------------------------------------------------------------------------------------------
class OutputWidget(QtGui.QWidget):
  """ Widget allowing for the configuration of output """
  renameSignal_ = QtCore.pyqtSignal()
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_OutputWidget.ui", self)
    self._ui_.renameButton_.clicked.connect(self.renameSignal_)
    self._ui_.renameButton_.setEnabled(False)
        
    self._ui_.specificDirectoryButton_.clicked.connect(self._showFolderSelectionDialog)
    
    self._ui_.useSpecificDirectoryRadio_.toggled.connect(self._ui_.specificDirectoryEdit_.setEnabled)
    self._ui_.useSpecificDirectoryRadio_.toggled.connect(self._ui_.specificDirectoryButton_.setEnabled)
    self._ui_.formatEdit_.textChanged.connect(self._updatePreviewText)
    self._updatePreviewText()

    completer = QtGui.QCompleter(self)
    fsModel = QtGui.QFileSystemModel(completer)
    fsModel.setRootPath("")
    completer.setModel(fsModel)
    self._ui_.specificDirectoryEdit_.setCompleter(completer)
    
    #tooltip
    toolTipText = ["Avaible options:"]
    for key in outputFormat.HELP_INPUT_MAP.data_:
      toolTipText.append("%s -> %s" % (key, outputFormat.HELP_INPUT_MAP.data_[key]))
    self._ui_.formatEdit_.setToolTip("\n".join(toolTipText))

    self.stopActioning()
    
  def enableControls(self, isEnabled):
    self._ui_.renameButton_.setEnabled(isEnabled)
    
  def _updatePreviewText(self):
    text = utils.toString(self._ui_.formatEdit_.text())
    oFormat = outputFormat.OutputFormat(text)
    formattedText = oFormat.outputToString(outputFormat.EXAMPLE_INPUT_MAP)
    formattedText = "Example: %s" % fileHelper.FileHelper.sanitizeFilename(formattedText)
    self._ui_.formatExampleLabel_.setText(formattedText)
    
  def startActioning(self):
    self._ui_.progressBar_.setValue(0)    
    self._ui_.progressBar_.setVisible(True)
    self._ui_.stopButton_.setVisible(True)
    self._ui_.renameButton_.setVisible(False)

  def stopActioning(self):
    self._ui_.progressBar_.setVisible(False)
    self._ui_.stopButton_.setVisible(False)
    self._ui_.renameButton_.setVisible(True)    
      
  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self.outputSettings_.outputFolder_)
    if folder:
      self.outputSettings_.outputFolder_ = folder
      self.dataItem_.setData(self.outputSettings_.toDictionary())  

  def getConfig(self):
    outputDir = utils.toString(self._ui_.specificDirectoryEdit_.text())
    if self._ui_.useSourceDirectoryRadio_.isChecked():
      outputDir = USE_SOURCE_DIRECTORY    
    data = {"format" : utils.toString(self._ui_.formatEdit_.text()),
            "folder" : outputDir,
            "move" : self._ui_.moveRadio_.isChecked(),
            "dontOverwrite" : self._ui_.doNotOverwriteCheckBox_.isChecked()}
    return data
  
  def setConfig(self, data):
    self._ui_.formatEdit_.setText(data.get("format", outputFormat.DEFAULT_FORMAT.formatStr_))
    outputDir = data.get("folder", USE_SOURCE_DIRECTORY)
    self._ui_.useSourceDirectoryRadio_.setChecked(outputDir == USE_SOURCE_DIRECTORY)
    if outputDir != USE_SOURCE_DIRECTORY:
      self._ui_.specificDirectoryEdit_.setText(outputDir)
    self._ui_.moveRadio_.setChecked(data.get("move", True))
    self._ui_.doNotOverwriteCheckBox_.setChecked(data.get("dontOverwrite", True))
    self._isUpdating  = False