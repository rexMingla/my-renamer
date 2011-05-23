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
class OutputSettings():
  """ Settings serialized on application start up/shut down."""
  def __init__(self):
    self.outputFileFormat_ = outputFormat.DEFAULT_FORMAT.formatStr_
    self.outputFolder_     = USE_SOURCE_DIRECTORY
    self.keepSourceFiles_  = True
    self.doNotOverwrite_   = True

  def toDictionary(self):
    return {"outputFileFormat":utils.toString(self.outputFileFormat_),
            "outputFolder"    :utils.toString(self.outputFolder_),
            "keepSourceFiles" :utils.toString(self.keepSourceFiles_),
            "doNotOverwrite"  :utils.toString(self.doNotOverwrite_)}

  def fromDictionary(self, dic):
    utils.verifyType(dic, dict)
    if dic.has_key("outputFileFormat") and isinstance(dic["outputFileFormat"], str):  
      self.outputFileFormat_ = dic["outputFileFormat"]
    if dic.has_key("outputFolder") and isinstance(dic["outputFolder"], str): 
      self.outputFolder_ = dic["outputFolder"]
    if dic.has_key("keepSourceFiles") and isinstance(dic["keepSourceFiles"], str): 
      self.keepSourceFiles_ = utils.strToBool(dic["keepSourceFiles"])
    if dic.has_key("doNotOverwrite") and isinstance(dic["doNotOverwrite"], str): 
      self.doNotOverwrite_ = utils.strToBool(dic["doNotOverwrite"])
      
# --------------------------------------------------------------------------------------------------------------------
class OutputWidget(QtGui.QWidget):
  """ Widget allowing for the configuration of output """
  renameSignal_ = QtCore.pyqtSignal()
  
  def __init__(self, parent=None):
    super(QtGui.QWidget, self).__init__(parent)
    self._ui_ = uic.loadUi("ui/ui_OutputWidget.ui", self)
    self.outputSettings_ = OutputSettings()
    self.dataItem_ = serializer.DataItem(self.outputSettings_.toDictionary())
    self.dataItem_.onChangedSignal_.connect(self._onStateChanged)
    self._ui_.renameButton_.clicked.connect(self.renameSignal_)
    self._ui_.renameButton_.setEnabled(False)
    self._onStateChanged()
        
    self._ui_.specificDirectoryButton_.clicked.connect(self._showFolderSelectionDialog)
    
    self._ui_.useSpecificDirectoryRadio_.toggled.connect(self._ui_.specificDirectoryEdit_.setEnabled)
    self._ui_.useSpecificDirectoryRadio_.toggled.connect(self._ui_.specificDirectoryButton_.setEnabled)
    
    self._ui_.formatEdit_.textChanged.connect(self._updatePreviewText)
    self._updatePreviewText()

    self._ui_.formatEdit_.editingFinished.connect(self._readbackGUI)
    self._ui_.specificDirectoryEdit_.editingFinished.connect(self._readbackGUI)
    self._ui_.useSourceDirectoryRadio_.toggled.connect(self._readbackGUI)
    self._ui_.useSpecificDirectoryRadio_.toggled.connect(self._readbackGUI)
    self._ui_.keepSourceCheckBox_.toggled.connect(self._readbackGUI)
    self._ui_.doNotOverwriteCheckBox_.toggled.connect(self._readbackGUI)
    
    completer = QtGui.QCompleter(self)
    fsModel = QtGui.QFileSystemModel(completer)
    fsModel.setRootPath("")
    completer.setModel(fsModel)
    self._ui_.specificDirectoryEdit_.setCompleter(completer)

    self._isUpdating = False
    
  def enableControls(self, isEnabled):
    self._ui_.renameButton_.setEnabled(isEnabled)
    
  def _updatePreviewText(self):
    text = utils.toString(self._ui_.formatEdit_.text())
    oFormat = outputFormat.OutputFormat(text)
    formattedText = oFormat.outputToString(outputFormat.EXAMPLE_INPUT_MAP)
    formattedText = "Example: %s" % fileHelper.FileHelper.sanitizeFilename(formattedText)
    self._ui_.formatExampleLabel_.setText(formattedText)
    
  def _readbackGUI(self):
    """ Update from settings """    
    if not self._isUpdating:
      self.outputSettings_.outputFileFormat_ = utils.toString(self._ui_.formatEdit_.text())
      outputDir = self._ui_.specificDirectoryEdit_.text()
      if self._ui_.useSourceDirectoryRadio_.isChecked():
        outputDir = USE_SOURCE_DIRECTORY
      self.outputSettings_.outputFolder_ = utils.toString(outputDir)
      self.outputSettings_.keepSourceFiles_ = self._ui_.keepSourceCheckBox_.isChecked()
      self.outputSettings_.doNotOverwrite_ = self._ui_.doNotOverwriteCheckBox_.isChecked()
      self.dataItem_.setData(self.outputSettings_.toDictionary())
    
  def _onStateChanged(self):
    self._isUpdating  = True
    self.outputSettings_.fromDictionary(self.dataItem_.data_)
    self._ui_.formatEdit_.setText(self.outputSettings_.outputFileFormat_)
    if self.outputSettings_.outputFolder_ == USE_SOURCE_DIRECTORY:
      self._ui_.useSourceDirectoryRadio_.setChecked(True)
    else:
      self._ui_.specificDirectoryEdit_.setText(self.outputSettings_.outputFolder_)
      self._ui_.useSpecificDirectoryRadio_.setChecked(True)
    self._ui_.keepSourceCheckBox_.setChecked(self.outputSettings_.keepSourceFiles_)
    self._ui_.doNotOverwriteCheckBox_.setChecked(self.outputSettings_.doNotOverwrite_)
    self._isUpdating  = False
      
  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self.outputSettings_.outputFolder_)
    if folder:
      self.outputSettings_.outputFolder_ = folder
      self.dataItem_.setData(self.outputSettings_.toDictionary())  

