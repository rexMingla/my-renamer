#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: The input widget and settings
# --------------------------------------------------------------------------------------------------------------------
import os

from send2trash import send2trash
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from common import config
from common import interfaces
from common import extension
from common import file_helper
from common import formatting
from common import utils
from common import dont_show
   
# --------------------------------------------------------------------------------------------------------------------
class _SourceModel(QtCore.QAbstractTableModel):
  #statuses
  MISSING_LIBRARY = ("Missing Library", "Source could not be loaded") #(status, tooltip)
  MISSING_KEY = ("Missing Key", "Key needs to be set")
  DISABLED = ("Disabled", "Disabled by user")
  ENABLED = ("Enabled", "In use")

  COL_NAME = 0
  COL_STATUS = 1
  NUM_COLS = 2
  RAW_ITEM_ROLE = QtCore.Qt.UserRole + 1
  
  def __init__(self, holder, parent):
    super(_SourceModel, self).__init__(parent)
    self._holder = holder
    self.beginInsertRows(QtCore.QModelIndex(), 0, len(self._holder.stores) - 1)
    self.endInsertRows()
      
  def rowCount(self, _parent=None):
    return len(self._holder.stores)

  def columnCount(self, _parent):
    return _SourceModel.NUM_COLS
  
  def data(self, index, role):
    if not index.isValid():
      return None
    
    if role not in (_SourceModel.RAW_ITEM_ROLE, QtCore.Qt.ForegroundRole, 
                    QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole):
      return None
    
    item = self._holder.stores[index.row()]
    if role == _SourceModel.RAW_ITEM_ROLE:
      return item
    if role == QtCore.Qt.ForegroundRole and index.column() == _SourceModel.COL_STATUS:
      return QtGui.QBrush(QtCore.Qt.green if item.isActive() else QtCore.Qt.red)
    if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:
      if index.column() == _SourceModel.COL_NAME:
        return item.prettyName()
      else:
        status = _SourceModel.MISSING_LIBRARY
        if item.hasLib:
          if item.isAvailable():
            if item.isActive():
              status = _SourceModel.ENABLED
            else:
              status = _SourceModel.DISABLED
          else:
            status = _SourceModel.MISSING_KEY
        return status[0] if role == QtCore.Qt.DisplayRole else status[1]

  def headerData(self, section, orientation, role):
    if not role in (QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole) or orientation == QtCore.Qt.Vertical:
      return None
    
    if role == QtCore.Qt.DisplayRole:
      return ["Name", "Status"][section]
    if role == QtCore.Qt.ToolTipRole:
      return ["Name of service", "Overall status"][section]
    
  def moveUp(self, index):
    if not index.isValid():
      return    
    row = index.row()
    self._holder.stores[row], self._holder.stores[row - 1] = self._holder.stores[row - 1], self._holder.stores[row]
    self.dataChanged.emit(self.index(row - 1, 0), self.index(row, _SourceModel.NUM_COLS))
      
  def moveDown(self, index):
    if not index.isValid():
      return    
    row = index.row()
    self._holder.stores[row], self._holder.stores[row + 1] = self._holder.stores[row + 1], self._holder.stores[row]
    self.dataChanged.emit(self.index(row, 0), self.index(row + 1, _SourceModel.NUM_COLS))
    
  def updateItem(self, index, item):
    #dodge city...
    if not index.isValid():
      return    
    row = index.row()
    self._holder.stores[row] = item
    self.dataChanged.emit(self.index(row, 0), self.index(row, _SourceModel.NUM_COLS))
          
# --------------------------------------------------------------------------------------------------------------------
class EditSourcesWidget(QtGui.QDialog):
  """ Allows the user to prioritise the search order for information sources and set keys """
  def __init__(self, mode, holder, parent=None):
    super(EditSourcesWidget, self).__init__(parent)
    uic.loadUi("ui/ui_EditSources.ui", self)
    self.setWindowModality(True)
    self.setWindowTitle("Edit {} Sources".format(mode.capitalize()))

    self.keyEdit.textEdited.connect(self._onKeyEdited)
    self.activeCheckBox.clicked.connect(self._onActiveChecked)
    self.upButton.clicked.connect(self._moveUp)
    self.downButton.clicked.connect(self._moveDown)
    self.keyEdit.setPlaceholderText("Enter key here")
    
    self._currentIndex = None
    self._model = _SourceModel(holder, self)
    self.sourceView.setModel(self._model)  
    self.sourceView.horizontalHeader().setResizeMode(_SourceModel.COL_NAME, QtGui.QHeaderView.Interactive)
    self.sourceView.horizontalHeader().setResizeMode(_SourceModel.COL_STATUS, QtGui.QHeaderView.Fixed)
    self.sourceView.horizontalHeader().resizeSection(_SourceModel.COL_STATUS, 30)        
    self.sourceView.horizontalHeader().setStretchLastSection(True)    
    self.sourceView.selectionModel().selectionChanged.connect(self._onSelectionChanged)
    self._onSelectionChanged()
    
  def _onSelectionChanged(self):
    indexes = self.sourceView.selectionModel().selection().indexes()
    item  = None
    self._currentIndex = indexes[0] if indexes else None
    if not indexes:
      self.upButton.setEnabled(False)
      self.downButton.setEnabled(False)
    else:
      item = self._model.data(self._currentIndex, _SourceModel.RAW_ITEM_ROLE)
      row = self._currentIndex.row()
      self.upButton.setEnabled(row >= 1)
      self.downButton.setEnabled((row + 1) < self._model.rowCount())
    self._setCurrentItem(item)
    
  def _moveDown(self):
    self._model.moveDown(self._currentIndex)
    self.sourceView.selectRow(self._currentIndex.row() + 1)
    
  def _moveUp(self):
    self._model.moveUp(self._currentIndex)
    self.sourceView.selectRow(self._currentIndex.row() - 1)

  def _setCurrentItem(self, item):
    self.detailsGroupBox.setEnabled(bool(item))
    self.loadCheckBox.setChecked(bool(item) and item.hasLib)  
    self.keyGroupBox.setVisible(bool(item) and item.requiresKey)
    if self.keyGroupBox.isVisible():
      keyLabel = "No key required"
      if item.requiresKey:
        keyLabel = ("<html><body>Enter the key for <a href='{0}'>{0}</a>"
                    "</body></html>").format(item.sourceName, item.url)      
      self.keyEdit.setText(item.key)
      self.keyLabel.setText(keyLabel)
    self.activeCheckBox.setEnabled(bool(item) and item.isAvailable())
    self.activeCheckBox.setChecked(bool(item) and item.isEnabled)
    
  def _onKeyEdited(self, text):
    item = self._model.data(self._currentIndex, _SourceModel.RAW_ITEM_ROLE)
    item.key = str(text)
    self.activeCheckBox.setEnabled(item.isAvailable())
    self._model.updateItem(self._currentIndex, item)
  
  def _onActiveChecked(self):
    item = self._model.data(self._currentIndex, _SourceModel.RAW_ITEM_ROLE)
    item.isEnabled = self.activeCheckBox.isChecked()
    self._model.updateItem(self._currentIndex, item)
      
# --------------------------------------------------------------------------------------------------------------------
class InputWidget(interfaces.LoadWidgetInterface):
  """ Widget allowing for the configuration of source folders """
  exploreSignal = QtCore.pyqtSignal()
  stopSignal = QtCore.pyqtSignal()
  showEditSourcesSignal = QtCore.pyqtSignal()
  
  def __init__(self, mode, holder, parent=None):
    super(InputWidget, self).__init__("input/{}".format(mode), parent)
    uic.loadUi("ui/ui_Input.ui", self)
    
    self._holder = holder
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
    data.minFileSizeBytes = utils.stringToBytes("{} {}".format(self.sizeSpinBox.value(), 
                                                               self.sizeComboBox.currentText()))
    data.sources = self._holder.getConfig()
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
    self._holder.setConfig(data.sources or [])
    self.onSourcesWidgetFinished()
    
  def onSourcesWidgetFinished(self):
    sources = self._holder.getAllActiveNames()
    self.sourcesEdit.setText(", ".join(sources))
    #todo: act if == None

# --------------------------------------------------------------------------------------------------------------------
class NameFormatHelper:
  """ used by the output widget """
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
    
  def onRenameItemChanged(self, item):
    info = item.getInfo() if item else None
    if info != self._helper.previewInfo:
      self._helper.previewInfo = info
      self._updatePreviewText()

# --------------------------------------------------------------------------------------------------------------------
class _ActionHolder:
  """ used by BaseWorkBenchWidget """
  def __init__(self, button, parent, cb, shortcut, index):
    self.name = str(button.text()) #assumes the names match
    self.button = button
    self.action = QtGui.QAction(self.name, parent)
    self.button.clicked.connect(self.action.trigger)
    self.action.triggered.connect(cb)
    self.action.setIcon(button.icon())
    if shortcut:
      self.action.setShortcut(shortcut)
    self.index = index # to keep them ordered
      
# --------------------------------------------------------------------------------------------------------------------
class BaseWorkBenchWidget(interfaces.LoadWidgetInterface):
  """ hacky and horrible base workbench widget """
  workBenchChangedSignal = QtCore.pyqtSignal(bool)
  showEditSourcesSignal = QtCore.pyqtSignal()
  renameItemChangedSignal = QtCore.pyqtSignal(object)
  
  def __init__(self, mode, manager, parent=None):
    super(BaseWorkBenchWidget, self).__init__("workBench/{}".format(mode), parent)
    uic.loadUi("ui/ui_WorkBench.ui", self)
    self._model = None
    self._manager = manager
    self.selectAllCheckBox.clicked.connect(self._setOverallCheckedState)
    
    #images
    self.openButton.setIcon(QtGui.QIcon("img/open.png"))
    self.launchButton.setIcon(QtGui.QIcon("img/launch.png"))
    self.deleteButton.setIcon(QtGui.QIcon("img/delete.png"))
    self.editEpisodeButton.setIcon(QtGui.QIcon("img/edit.png"))
    self.editSeasonButton.setIcon(QtGui.QIcon("img/edit.png"))
    self.editMovieButton.setIcon(QtGui.QIcon("img/edit.png"))
    
    def createAction(actions, button, cb, shortcut=None):
      holder = _ActionHolder(button, self, cb, shortcut, len(actions))
      actions[holder.name] = holder

    self._actions = {}
    createAction(self._actions, self.openButton, self._open, QtCore.Qt.ControlModifier + QtCore.Qt.Key_O)
    createAction(self._actions, self.launchButton, self._launch, QtCore.Qt.ControlModifier + QtCore.Qt.Key_L)
    createAction(self._actions, self.editEpisodeButton, self._editEpisode)
    createAction(self._actions, self.editSeasonButton, self._editSeason)
    createAction(self._actions, self.editMovieButton, self._editMovie)
    createAction(self._actions, self.deleteButton, self._delete, QtCore.Qt.Key_Delete)
    
    self._currentIndex = QtCore.QModelIndex()
    self._view = self.tvView if mode == interfaces.Mode.TV_MODE else self.movieView #HACK. yuck
    self._view.viewport().installEventFilter(self) #filter out double right click
    self._view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
    
  def eventFilter(self, obj, event):
    if obj in (self.tvView.viewport(), self.movieView.viewport()):
      if event.type() == QtCore.QEvent.MouseButtonDblClick and event.button() == QtCore.Qt.RightButton:
        event.accept() #do nothing
        return True
    return super(BaseWorkBenchWidget, self).eventFilter(obj, event)
    
  def _showItem(self):
    raise NotImplementedError("BaseWorkBenchWidget._showItem not implemented")    
    
  def _onSelectionChanged(self, selection=None):
    raise NotImplementedError("BaseWorkBenchWidget._onSelectionChanged not implemented")
    
  def _editEpisode(self):
    raise NotImplementedError("BaseWorkBenchWidget._editEpisode not implemented")
    
  def _editSeason(self):
    raise NotImplementedError("BaseWorkBenchWidget._editSeason not implemented")
    
  def _editMovie(self):
    raise NotImplementedError("BaseWorkBenchWidget._editMovie not implemented")
    
  def _setModel(self, m):
    self._model = m
    self._model.workBenchChangedSignal.connect(self._onWorkBenchChanged)
    self._onWorkBenchChanged(False)
    self._model.beginUpdateSignal.connect(self.startWorkBenching)
    self._model.endUpdateSignal.connect(self.stopWorkBenching)
    for action in self._actions.values():
      action.button.setVisible(action.name in self._model.ALL_ACTIONS)
    actions = []
    for action, enabled in self._model.getAvailableActions(self._currentIndex).items():
      actions.append(self._actions[action])
    actions.sort(key=lambda a: a.index)
    self.addActions([a.action for a in actions])
    self._view.addActions([a.action for a in actions])
    
  def _launchLocation(self, location):
    path = QtCore.QDir.toNativeSeparators(location)
    if not QtGui.QDesktopServices.openUrl(QtCore.QUrl("file:///{}".format(path))):
      QtGui.QMessageBox.information(self, "An error occured", 
                                    "Could not find path:\n{}".format(path))
    
  def _launch(self):
    f = self._model.getFile(self._currentIndex)
    if f:
      self._launchLocation(f)
  
  def _open(self):
    f = self._model.getFolder(self._currentIndex)
    if f:
      self._launchLocation(f)
      
  def _enable(self):
    self.setEnabled(True)
        
  def _disable(self):
    self.setEnabled(False)
    
  def startWorkBenching(self):
    self._disable()
        
  def stopWorkBenching(self):
    self._enable()
        
  def startExploring(self):
    self._model.clear()
    self._disable()
    self._onSelectionChanged()
    self._model.beginUpdate()
  
  def stopExploring(self):
    self._enable()
    self.editEpisodeButton.setEnabled(False)    
    self.editSeasonButton.setEnabled(False)
    self.editMovieButton.setEnabled(False)    
    self.launchButton.setEnabled(False)
    self.openButton.setEnabled(False)
    self.deleteButton.setEnabled(False)    
    self._model.endUpdate()
    self._onWorkBenchChanged(bool(self._model.items())) #HACK: TODO: 
    
  def startActioning(self):
    self._disable()

  def stopActioning(self):
    self.tvView.expandAll()    
    self._enable()
    
  def getConfig(self):
    raise NotImplementedError("BaseWorkBenchWidget.getConfig not implemented")
  
  def setConfig(self, data):
    raise NotImplementedError("BaseWorkBenchWidget.getConfig not implemented")

  def _setOverallCheckedState(self, state):
    self._disable()
    self._model.setOverallCheckedState(state)
    self._enable()
    
  def _onWorkBenchChanged(self, hasChecked):
    #utils.verifyType(hasChecked, bool)
    cs = self._model.overallCheckedState()
    self.selectAllCheckBox.setEnabled(not cs is None)
    if cs == None:
      cs = QtCore.Qt.Unchecked
    self.selectAllCheckBox.setCheckState(cs)
    self.workBenchChangedSignal.emit(hasChecked)
    
  def _delete(self):
    f = self._model.getDeleteItem(self._currentIndex)
    if f and self._deleteLocation(f):
      self._model.delete(self._currentIndex)
      self.tvView.expandAll()
  
  def _updateActions(self):
    for action, isEnabled in self._model.getAvailableActions(self._currentIndex).items():
      self._actions[action].button.setEnabled(isEnabled)
      self._actions[action].action.setEnabled(isEnabled)
    
  def _deleteLocation(self, location):
    isDel = False
    ret = dont_show.DontShowManager.getAnswer("Please confirm delete", 
      "Are you sure you want to delete this file?\n"
      "{}".format(location), "delete", parent=self)
    if ret != QtGui.QDialogButtonBox.Ok:
      return False
    try:
      send2trash(location)
      isDel = True
    except OSError as e:
      mb = QtGui.QMessageBox(QtGui.QMessageBox.Information, 
                             "An error occured", "Unable to move to trash. Path:\n{}".format(location))
      mb.setDetailedText("Error:\n{}".format(str(e)))
      mb.exec_()  
    return isDel
    
  def addItem(self, item):
    self._model.addItem(item)
    
  def actionableItems(self):
    return self._model.items()

# --------------------------------------------------------------------------------------------------------------------
class SearchResultsWidget(QtGui.QDialog):
  """ lists search results found in an info widget """
  itemSelectedSignal = QtCore.pyqtSignal(object)
  
  def __init__(self, parent=None):
    super(SearchResultsWidget, self).__init__(parent)
    uic.loadUi("ui/ui_SearchResults.ui", self)
    self._items = []
    self.resultsWidget.itemSelectionChanged.connect(self._onItemClicked)
    
  def clear(self):
    self._items = []
    self.resultsWidget.clearContents()
    self.resultsWidget.setRowCount(0)
    
  def addItem(self, resultHolder):
    self._items.append(resultHolder)
    rc = self.resultsWidget.rowCount()
    self.resultsWidget.insertRow(rc)
    
    w = QtGui.QTableWidgetItem(str(resultHolder.info))
    w.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
    self.resultsWidget.setItem(rc, 0, w)
    
    w = QtGui.QTableWidgetItem(resultHolder.sourceName)
    w.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
    self.resultsWidget.setItem(rc, 1, w)
    
  def _onItemClicked(self):
    if self.resultsWidget.selectedItems():
      row = self.resultsWidget.selectedItems()[0].row()
      holder = self._items[row]
      self.itemSelectedSignal.emit(holder.info)