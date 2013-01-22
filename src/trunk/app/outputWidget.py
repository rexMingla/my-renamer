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

from common import config
from common import extension
from common import file_helper
from common import formatting
from common import utils

import interfaces

# --------------------------------------------------------------------------------------------------------------------
class NameFormatHelper:
  def __init__(self, formatter, helpInfo, exampleInfo, previewInfo=None):
    self.formatter = formatter
    self.helpInfo = helpInfo
    self.exampleInfo = exampleInfo
    self.previewInfo = previewInfo
    
# --------------------------------------------------------------------------------------------------------------------
class OutputWidget(interfaces.LoadWidgetInterface):
  """ Widget allowing for the configuration of output settings """
  renameSignal = QtCore.pyqtSignal()
  stopSignal = QtCore.pyqtSignal()
  
  def __init__(self, mode, nameFormatHelper, parent=None):
    super(OutputWidget, self).__init__("output/{}".format(mode), parent)    
    uic.loadUi("ui/ui_Output.ui", self)
    
    self._helper = nameFormatHelper
    self._initFormat()
    
    self.renameButton.clicked.connect(self.renameSignal)
    self.renameButton.setIcon(QtGui.QIcon("img/rename.png"))
    self.stopButton.clicked.connect(self.stopSignal)
    self.stopButton.setIcon(QtGui.QIcon("img/stop.png"))
        
    self.specificDirectoryButton.clicked.connect(self._showFolderSelectionDialog)
    
    self.useSpecificDirectoryRadio.toggled.connect(self.specificDirectoryEdit.setEnabled)
    self.useSpecificDirectoryRadio.toggled.connect(self.specificDirectoryButton.setEnabled)
    self.formatEdit.textChanged.connect(self._updatePreviewText)
    self.showHelpLabel.linkActivated.connect(self._showHelp)
    self.hideHelpLabel.linkActivated.connect(self._hideHelp)
    self.subtitleCheckBox.toggled.connect(self.subtitleExtensionsEdit.setEnabled)
    
    completer = QtGui.QCompleter(self)
    fsModel = QtGui.QFileSystemModel(completer)
    fsModel.setRootPath("")
    completer.setModel(fsModel)
    self.specificDirectoryEdit.setCompleter(completer)
    
    self._isActioning = False
    self.stopActioning()
    self.renameButton.setEnabled(False)
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
    
  def _initFormat(self):
    def escapeHtml(text):
      return text.replace("<", "&lt;").replace(">", "&gt;")
    
    if self.formatEdit.text().isEmpty():
      self.formatEdit.setText(self._helper.formatter.DEFAULT_FORMAT_STR)
    #tooltip
    
    helpText = ["Available options:"]
    helpValues = self._helper.formatter.getValues(self._helper.helpInfo)
    for key, value in helpValues.items():
      helpText.append("<b>{}</b>: {}".format(escapeHtml(key), value))
    if formatting.CONDITIONAL_START in self._helper.formatter.DEFAULT_FORMAT_STR:
      helpText += ["", "Enclose text within <b>%( )%</b> to optionally include text is a value is present.",
                   "Eg. <b>%(</b> Disc <b>{}</b> <b>)%</b>".format(escapeHtml("<part>"))]
    self.helpEdit.setText("<html><body>{}</body></html>".format("<br/>".join(helpText)))
    
    self._updatePreviewText()
    
  def _updatePreviewText(self):
    prefixText = "Example"
    info = self._helper.exampleInfo
    if self._helper.previewInfo:
      prefixText = "Preview"
      info = self._helper.previewInfo
    formattedText = self._helper.formatter.getNameFromInfo(utils.toString(self.formatEdit.text()), info)
    color = "red"
    if file_helper.FileHelper.isValidFilename(formattedText):
      color = "gray"
    formattedText = "{}: {}".format(prefixText, file_helper.FileHelper.sanitizeFilename(formattedText))
    self.formatExampleLabel.setText(formattedText)
    self.formatExampleLabel.setStyleSheet("QLabel {{ color: {}; }}".format(color))
    
  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self.specificDirectoryEdit.text())
    if folder:
      self.specificDirectoryEdit.setText(folder)

  def getConfig(self):
    data = config.OutputConfig()
    data.format = utils.toString(self.formatEdit.text())
    data.folder = utils.toString(self.specificDirectoryEdit.text())
    data.useSource = self.useSourceDirectoryRadio.isChecked()
    data.isMove = self.moveRadio.isChecked()
    data.dontOverwrite = self.doNotOverwriteCheckBox.isChecked()
    data.showHelp = self.helpGroupBox.isVisible()
    data.actionSubtitles = self.subtitleCheckBox.isChecked()
    data.subtitleExtensions = extension.FileExtensions(utils.toString(self.subtitleExtensionsEdit.text())).extensionString()
    return data
  
  def setConfig(self, data):
    data = data or config.OutputConfig()
    
    self.formatEdit.setText(data.format or self._helper.formatter.DEFAULT_FORMAT_STR)
    self.specificDirectoryEdit.setText(data.folder)
    if data.useSource:
      self.useSourceDirectoryRadio.setChecked(True)
    else:
      self.useSpecificDirectoryRadio.setChecked(True)      
    self.moveRadio.setChecked(data.isMove)
    self.doNotOverwriteCheckBox.setChecked(data.dontOverwrite)
    self.subtitleExtensionsEdit.setText(data.subtitleExtensions)
    self.subtitleCheckBox.setChecked(data.actionSubtitles)
    
    if data.showHelp:
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
    
  def _onRenameItemChanged(self, item):
    info = item.getInfo() if item else None
    if info != self._helper.previewInfo:
      self._helper.previewInfo = info
      self._updatePreviewText()
    