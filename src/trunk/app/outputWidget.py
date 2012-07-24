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
from common import outputFormat
from common import utils

import interfaces
import config
      
# --------------------------------------------------------------------------------------------------------------------
class OutputWidget(interfaces.LoadWidgetInterface):
  """ Widget allowing for the configuration of output """
  renameSignal = QtCore.pyqtSignal()
  stopSignal = QtCore.pyqtSignal()
  
  def __init__(self, parent=None):
    super(OutputWidget, self).__init__("output", parent)
    self._fmt = None
    
    uic.loadUi("ui/ui_OutputWidget.ui", self)
    self.renameButton.clicked.connect(self.renameSignal)
    self.stopButton.clicked.connect(self.stopSignal)
        
    self.specificDirectoryButton.clicked.connect(self._showFolderSelectionDialog)
    
    self.useSpecificDirectoryRadio.toggled.connect(self.specificDirectoryEdit.setEnabled)
    self.useSpecificDirectoryRadio.toggled.connect(self.specificDirectoryButton.setEnabled)
    self.formatEdit.textChanged.connect(self._updatePreviewText)
    
    completer = QtGui.QCompleter(self)
    fsModel = QtGui.QFileSystemModel(completer)
    fsModel.setRootPath("")
    completer.setModel(fsModel)
    self.specificDirectoryEdit.setCompleter(completer)
    
    self.stopActioning()
    self.stopExploring()
    
  def _setMovieMode(self):
    self._setOutputFormat(outputFormat.MovieInputMap)

  def _setTvMode(self):
    self._setOutputFormat(outputFormat.TvInputMap)
  
  def startExploring(self):
    self.renameButton.setEnabled(False)
  
  def stopExploring(self):
    self.renameButton.setEnabled(True)

  def startActioning(self):
    self.progressBar.setValue(0)    
    self.progressBar.setVisible(True)
    self.stopButton.setEnabled(True)
    self.stopButton.setVisible(True)
    self.renameButton.setVisible(False)

  def stopActioning(self):
    self.progressBar.setVisible(False)
    self.stopButton.setVisible(False)
    self.renameButton.setVisible(True)
    self.renameButton.setEnabled(True)
    
  def _setOutputFormat(self, fmt):
    self._fmt = fmt
    if not self._fmt:
      self.formatEdit.setText("")
      self.formatEdit.setToolTip("")
      return
    
    if self.formatEdit.text().isEmpty():
      self.formatEdit.setText(self._fmt.defaultFormatStr())
    #tooltip
    toolTipText = ["Available options:"]
    for key, value in self._fmt.exampleInputMap().data.items():
      toolTipText.append("%s -> %s" % (key, value))
    if self.mode == interfaces.Mode.MOVIE_MODE:
      toolTipText.append("Enclose text withihn %( )% to optionally include text is a value is present.")
      toolTipText.append("Eg. %( Disc <part> )%")
    self.formatEdit.setToolTip("\n".join(toolTipText))
    
    self._updatePreviewText()
    
  def _updatePreviewText(self):
    if self._fmt:
      text = utils.toString(self.formatEdit.text())
      oFormat = outputFormat.OutputFormat(text)
      formattedText = oFormat.outputToString(self._fmt.exampleInputMap())
      color = "red"
      if fileHelper.FileHelper.isValidFilename(formattedText):
        color = "black"
      formattedText = "Example: {}".format(fileHelper.FileHelper.sanitizeFilename(formattedText))
      self.formatExampleLabel.setText(formattedText)
      self.formatExampleLabel.setStyleSheet("QLabel {{ color: {}; }}".format(color))
      
  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self.specificDirectoryEdit.text())
    if folder:
      self.specificDirectoryEdit.setText(folder)

  def getConfig(self):
    outputDir = utils.toString(self.specificDirectoryEdit.text())
    if self.useSourceDirectoryRadio.isChecked():
      outputDir = config.USE_SOURCE_DIRECTORY    
    data = {"format" : utils.toString(self.formatEdit.text()),
            "folder" : outputDir,
            "move" : self.moveRadio.isChecked(),
            "dontOverwrite" : self.doNotOverwriteCheckBox.isChecked()}
    return data
  
  def setConfig(self, data):
    fmt = data.get("format", "")
    if not fmt and self._fmt:
      fmt = self._fmt.defaultFormatStr()
    if fmt:
      self.formatEdit.setText(fmt)
    outputDir = data.get("folder", config.USE_SOURCE_DIRECTORY)
    if outputDir == config.USE_SOURCE_DIRECTORY:
      self.specificDirectoryEdit.setText("")
      self.useSourceDirectoryRadio.setChecked(True)
    else:
      self.specificDirectoryEdit.setText(outputDir)
      self.useSpecificDirectoryRadio.setChecked(True)      
    self.moveRadio.setChecked(data.get("move", True))
    self.doNotOverwriteCheckBox.setChecked(data.get("dontOverwrite", True))