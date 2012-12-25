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
  
  def __init__(self, mode, fmt, parent=None):
    super(OutputWidget, self).__init__("output/{}".format(mode), parent)    
    uic.loadUi("ui/ui_OutputWidget.ui", self)
    
    self._setOutputFormat(fmt)
    self.renameButton.clicked.connect(self.renameSignal)
    self.stopButton.clicked.connect(self.stopSignal)
        
    self.specificDirectoryButton.clicked.connect(self._showFolderSelectionDialog)
    
    self.useSpecificDirectoryRadio.toggled.connect(self.specificDirectoryEdit.setEnabled)
    self.useSpecificDirectoryRadio.toggled.connect(self.specificDirectoryButton.setEnabled)
    self.formatEdit.textChanged.connect(self._updatePreviewText)
    self.showHelpLabel.linkActivated.connect(self._showHelp)
    self.hideHelpLabel.linkActivated.connect(self._hideHelp)
    
    completer = QtGui.QCompleter(self)
    fsModel = QtGui.QFileSystemModel(completer)
    fsModel.setRootPath("")
    completer.setModel(fsModel)
    self.specificDirectoryEdit.setCompleter(completer)
    
    self._isActioning = False
    self.stopActioning()
    self.stopExploring()
    self._showHelp()
    
  def isExecuting(self):
    return self._isActioning
      
  def startExploring(self):
    self.renameButton.setEnabled(False)
  
  def stopExploring(self):
    self.renameButton.setEnabled(True)

  def startActioning(self):
    self._isActioning = True
    self.progressBar.setValue(0)    
    self.progressBar.setVisible(True)
    self.stopButton.setEnabled(True)
    self.stopButton.setVisible(True)
    self.renameButton.setVisible(False)

  def stopActioning(self):
    self._isActioning = False
    self.progressBar.setVisible(False)
    self.stopButton.setVisible(False)
    self.renameButton.setVisible(True)
    self.renameButton.setEnabled(True)
    
  def _setOutputFormat(self, fmt):
    def escapeHtml(text):
      return text.replace("<", "&lt;").replace(">", "&gt;")
    
    self._fmt = fmt
    if self.formatEdit.text().isEmpty():
      self.formatEdit.setText(self._fmt.defaultFormatStr())
    #tooltip
    
    helpText = ["Available options:"]
    for key, value in self._fmt.helpInputMap().data.items():
      helpText.append("<b>{}</b>: {}".format(escapeHtml(key), value))
    if self._fmt.defaultFormatStr().find("%(") != -1:
      helpText += ["", "Enclose text within <b>%( )%</b> to optionally include text is a value is present.",
                   "Eg. <b>%(</b> Disc <b>{}</b> <b>)%</b>".format(escapeHtml("<part>"))]
    self.helpEdit.setText("<html><body>{}</body></html>".format("<br/>".join(helpText)))
    
    self._updatePreviewText()
    
  def _updatePreviewText(self):
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
            "dontOverwrite" : self.doNotOverwriteCheckBox.isChecked(),
            "showHelp" : self.helpGroupBox.isVisible()}
    return data
  
  def setConfig(self, data):
    fmt = data.get("format", self._fmt.defaultFormatStr())
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
    if data.get("showHelp", True):
      self._showHelp()
    else:
      self._hideHelp()
    
  def _showHelp(self):
    self.helpGroupBox.setVisible(True)
    self.hideHelpLabel.setVisible(True)
    self.showHelpLabel.setVisible(False)
  
  def _hideHelp(self):
    self.helpGroupBox.setVisible(False)
    self.hideHelpLabel.setVisible(False)
    self.showHelpLabel.setVisible(True)
    