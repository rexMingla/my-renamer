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
from common import thread
from common import widget as common_widget

from media.base import client as base_client

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
  RAW_DATA_ROLE = QtCore.Qt.UserRole + 1

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

    if role not in (_SourceModel.RAW_DATA_ROLE, QtCore.Qt.ForegroundRole,
                    QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole):
      return None

    item = self._holder.stores[index.row()]
    if role == _SourceModel.RAW_DATA_ROLE:
      return item
    if role == QtCore.Qt.ForegroundRole and index.column() == _SourceModel.COL_STATUS:
      return QtGui.QBrush(QtCore.Qt.green if item.isActive() else QtCore.Qt.red)
    if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:
      if index.column() == _SourceModel.COL_NAME:
        return item.prettyName()
      else:
        status = _SourceModel.MISSING_LIBRARY
        if item.has_lib:
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
class BaseSearchParamsWidget(QtGui.QWidget):
  search_signal = QtCore.pyqtSignal()

  def __init__(self, parent=None):
    super(BaseSearchParamsWidget, self).__init__(parent)

  def reset(self):
    self.setItem(None)

  def setItem(self, item):
    raise NotImplementedError("BaseSearchParamsWidget.setItem not implemented")

  def getSearchParams(self):
    raise NotImplementedError("BaseSearchParamsWidget.getSearchParams not implemented")

  def _setEditWidgets(self, widgets):
    for widget in widgets:
      widget.installEventFilter(self)
    self._edit_widgets = widgets

  def eventFilter(self, obj, event):
    if obj in self._edit_widgets and \
        event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Return:
      #event.ignore()
      self.search_signal.emit()
      return True
    return super(BaseSearchParamsWidget, self).eventFilter(obj, event)

# --------------------------------------------------------------------------------------------------------------------
class BaseEditInfoWidget(QtGui.QWidget):
  def __init__(self, parent=None):
    super(BaseEditInfoWidget, self).__init__(parent)

  def setItem(self, item):
    self._setItem(item)
    self.setInfo(item.getInfo() if item else None)

  def _setItem(self):
    raise NotImplementedError("BaseEditInfo._setItem not implemented")

  def setInfo(self):
    raise NotImplementedError("BaseEditInfo.setInfo not implemented")

  def getItem(self):
    raise NotImplementedError("BaseEditInfo.getItem not implemented")

# --------------------------------------------------------------------------------------------------------------------
class SearchThread(thread.WorkerThread):
  def __init__(self, search_params, store, is_lucky):
    super(SearchThread, self).__init__("search")
    self._search_params = search_params
    self._store = store
    self._is_lucky = is_lucky

  def run(self):
    for info in self._store.getAllInfo(self._search_params):
      self._onData(info)
      if self._user_stopped or (info and self._is_lucky):
        break

# --------------------------------------------------------------------------------------------------------------------
class EditItemWidget(QtGui.QDialog):
    show_edit_sources_signal = QtCore.pyqtSignal()
    """ The widget allows the user to search and modify tv info. """
    def __init__(self, mode, holder, search_widget, edit_info_widget, parent=None):
      super(EditItemWidget, self).__init__(parent)
      self.setWindowTitle("Edit {}".format(mode.capitalize()))
      self.setWindowModality(True)
      self.holder = holder
      self._worker_thread = None

      self._search_widget = search_widget
      self._search_widget.setParent(self)
      self._edit_info_widget = edit_info_widget
      self._edit_info_widget.setParent(self)

      self._is_lucky_check_box = QtGui.QCheckBox("I'm feeling lucky")
      self._is_lucky_check_box.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed))
      self._is_lucky_check_box.setToolTip("Return after first match found or search sources for all matches")
      self._search_buttons = common_widget.ProgressWidget(
          start_label="Search", widget=self._is_lucky_check_box, parent=self)
      self._search_buttons.setProgressRange(0, 0) #spin indefinitely
      self._search_widget.search_signal.connect(self._search_buttons.start)

      edit_sources_button = QtGui.QPushButton("Edit Sources...")
      edit_sources_button.clicked.connect(self.show_edit_sources_signal)

      search_buttons = QtGui.QHBoxLayout()
      search_buttons.setContentsMargins(0, 0, 0, 0)
      search_buttons.setSpacing(4)
      search_buttons.addWidget(self._search_buttons)
      search_buttons.addWidget(edit_sources_button)

      self._search_results = SearchResultsWidget(self)
      self._search_buttons.start_signal.connect(self._search)
      self._search_results.item_selected_signal.connect(self._edit_info_widget.setInfo)

      self._button_box = QtGui.QDialogButtonBox(self)
      self._button_box.setOrientation(QtCore.Qt.Horizontal)
      self._button_box.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
      #self._button_box.setCenterButtons(False)
      self._button_box.accepted.connect(self.accept)
      self._button_box.rejected.connect(self.reject)

      self._hide_label = QtGui.QLabel("hide results")
      self._hide_label.setOpenExternalLinks(False)
      self._hide_label.setText("<html><a href=\"xxx\">hide results</a>")
      self._hide_label.linkActivated.connect(self._hideResults)

      self._show_label = QtGui.QLabel("show results")
      self._show_label.setOpenExternalLinks(False)
      self._show_label.setText("<html><a href=\"xxx\">show results</a>")
      self._show_label.linkActivated.connect(self._showResults)

      bottom_widgets = QtGui.QVBoxLayout()
      bottom_widgets.setContentsMargins(0, 0, 0, 0)
      bottom_widgets.setSpacing(4)
      bottom_widgets.addWidget(self._button_box)
      bottom_widgets.addWidget(self._hide_label)
      bottom_widgets.addWidget(self._show_label)

      vbox = QtGui.QVBoxLayout()
      vbox.addWidget(self._search_widget)
      vbox.addLayout(search_buttons)
      vbox.addWidget(self._edit_info_widget)
      vbox.addLayout(bottom_widgets)

      layout = QtGui.QHBoxLayout(self)
      layout.setContentsMargins(4, 4, 4, 4)
      layout.setSpacing(4)
      layout.addLayout(vbox)
      layout.addWidget(self._search_results)

      self._item = None
      self._is_lucky = False
      self._found_data = True
      self._onThreadFinished()
      self._hideResults()
      self._show_label.setVisible(False)

    def __del__(self):
      self._stopThread()

    def showEvent(self, e):
      self._found_data = True
      self._onThreadFinished()
      self._hideResults()
      self._show_label.setVisible(False)
      super(EditItemWidget, self).showEvent(e)

    def _search(self):
      if self._worker_thread and self._worker_thread.isRunning():
        return
      self._is_lucky = self._is_lucky_check_box.isChecked()
      self._found_data = False

      self._search_buttons.start()
      self._button_box.setEnabled(False)
      self._edit_info_widget.setEnabled(False)
      self._search_widget.setEnabled(False)

      self._worker_thread = SearchThread(self._search_widget.getSearchParams(),
          self.holder, self._is_lucky)
      self._worker_thread.new_data_signal.connect(self._onDataFound)
      self._worker_thread.finished.connect(self._onThreadFinished)
      self._worker_thread.terminated.connect(self._onThreadFinished)
      self._worker_thread.start()

    def _stopThread(self):
      if self._worker_thread:
        self._worker_thread.join()

    def _onThreadFinished(self):
      self._search_buttons.stop()
      self._button_box.setEnabled(True)
      self._search_widget.setEnabled(True)
      self._edit_info_widget.setEnabled(True)

      if not self._found_data:
        QtGui.QMessageBox.information(self, "Nothing found", "No results found for search")

    def _onDataFound(self, data):
      if not data:
        return

      if self._is_lucky:
        self._setSeasonInfo(data.info)
      else:
        if not self._found_data:
          self._search_results.clear()
          self._search_results.addItem(base_client.ResultHolder(self.getItem().getInfo(), "current"))
        self._search_results.addItem(data)
        self._showResults()
      self._found_data = True

    def setItem(self, item):
      """ Fill the dialog with the data prior to being shown """
      #utils.verifyType(s, tv_types.Season)
      self._search_widget.setItem(item)
      self._edit_info_widget.setItem(item)

    def getItem(self):
      return self._edit_info_widget.getItem()

    def _showResults(self):
      self._search_results.setVisible(True)
      self._hide_label.setVisible(True)
      self._show_label.setVisible(False)

    def _hideResults(self):
      self._search_results.setVisible(False)
      self._hide_label.setVisible(False)
      self._show_label.setVisible(True)

# --------------------------------------------------------------------------------------------------------------------
class EditSourcesWidget(QtGui.QDialog):
  """ Allows the user to prioritise the search order for information sources and set keys """
  def __init__(self, mode, holder, parent=None):
    super(EditSourcesWidget, self).__init__(parent)
    uic.loadUi("ui/ui_EditSources.ui", self)
    self.setWindowModality(True)
    self.setWindowTitle("Edit {} Sources".format(mode.capitalize()))

    self.key_edit.textEdited.connect(self._onKeyEdited)
    self.is_enabled_check_box.clicked.connect(self._onActiveChecked)
    self.up_button.clicked.connect(self._moveUp)
    self.down_button.clicked.connect(self._moveDown)
    self.key_edit.setPlaceholderText("Enter key here")

    self._current_index = None
    self._model = _SourceModel(holder, self)
    self.source_view.setModel(self._model)
    self.source_view.horizontalHeader().setResizeMode(_SourceModel.COL_NAME, QtGui.QHeaderView.Interactive)
    self.source_view.horizontalHeader().setResizeMode(_SourceModel.COL_STATUS, QtGui.QHeaderView.Fixed)
    self.source_view.horizontalHeader().resizeSection(_SourceModel.COL_STATUS, 30)
    self.source_view.horizontalHeader().setStretchLastSection(True)
    self.source_view.selectionModel().selectionChanged.connect(self._onSelectionChanged)
    self._onSelectionChanged()

  def _onSelectionChanged(self):
    indexes = self.source_view.selectionModel().selection().indexes()
    item  = None
    self._current_index = indexes[0] if indexes else None
    if not indexes:
      self.up_button.setEnabled(False)
      self.down_button.setEnabled(False)
    else:
      item = self._model.data(self._current_index, _SourceModel.RAW_DATA_ROLE)
      row = self._current_index.row()
      self.up_button.setEnabled(row >= 1)
      self.down_button.setEnabled((row + 1) < self._model.rowCount())
    self._setCurrentItem(item)

  def _moveDown(self):
    self._model.moveDown(self._current_index)
    self.source_view.selectRow(self._current_index.row() + 1)

  def _moveUp(self):
    self._model.moveUp(self._current_index)
    self.source_view.selectRow(self._current_index.row() - 1)

  def _setCurrentItem(self, item):
    self.details_group_box.setEnabled(bool(item))
    self.could_load_check_box.setChecked(bool(item) and item.has_lib)
    self.key_group_box.setVisible(bool(item) and item.requires_key)
    if self.key_group_box.isVisible():
      key_label = "No key required"
      if item.requires_key:
        key_label = ("<html><body>Enter the key for <a href='{0}'>{0}</a>"
                    "</body></html>").format(item.source_name, item.url)
      self.key_edit.setText(item.key)
      self.key_label.setText(key_label)
    self.is_enabled_check_box.setEnabled(bool(item) and item.isAvailable())
    self.is_enabled_check_box.setChecked(bool(item) and item.is_enabled)

  def _onKeyEdited(self, text):
    item = self._model.data(self._current_index, _SourceModel.RAW_DATA_ROLE)
    item.key = str(text)
    self.is_enabled_check_box.setEnabled(item.isAvailable())
    self._model.updateItem(self._current_index, item)

  def _onActiveChecked(self):
    item = self._model.data(self._current_index, _SourceModel.RAW_DATA_ROLE)
    item.is_enabled = self.is_enabled_check_box.isChecked()
    self._model.updateItem(self._current_index, item)

# --------------------------------------------------------------------------------------------------------------------
class InputWidget(interfaces.ActionWidgetInterface):
  """ Widget allowing for the configuration of source folders """
  explore_signal = QtCore.pyqtSignal()
  stop_signal = QtCore.pyqtSignal()
  show_edit_sources_signal = QtCore.pyqtSignal()

  def __init__(self, mode, holder, parent=None):
    super(InputWidget, self).__init__("input/{}".format(mode), parent)
    uic.loadUi("ui/ui_Input.ui", self)
    self.progress_widget = common_widget.ProgressWidget(start_label="Search", parent=self)
    common_widget.addWidgetToContainer(self.placeholder_widget, self.progress_widget, spacing=0)

    self._holder = holder
    self.folder_button.clicked.connect(self._showFolderSelectionDialog)
    self.progress_widget.start_signal.connect(self.explore_signal)
    self.folder_edit.returnPressed.connect(self.explore_signal)
    self.file_extension_edit.returnPressed.connect(self.explore_signal)
    self.progress_widget.stop_signal.connect(self.stop_signal)
    self.restricted_extension_radio_button.toggled.connect(self.file_extension_edit.setEnabled)
    self.restricted_size_radio_button.toggled.connect(self.filesize_spin_box.setEnabled)
    self.restricted_size_radio_button.toggled.connect(self.filesize_combo_box.setEnabled)
    self.show_source_button.clicked.connect(self.show_edit_sources_signal.emit)
    search_action = QtGui.QAction(self.progress_widget.start_button.text(), self)
    search_action.setIcon(self.progress_widget.start_button.icon())
    search_action.setShortcut(QtCore.Qt.ControlModifier + QtCore.Qt.Key_F)
    search_action.triggered.connect(self.explore_signal.emit)
    self.addAction(search_action)

    completer = QtGui.QCompleter(self)
    fs_model = QtGui.QFileSystemModel(completer)
    fs_model.setRootPath("")
    completer.setModel(fs_model)
    self.folder_edit.setCompleter(completer)

    self.stopActioning()
    self.stopExploring()

  def startExploring(self):
    pass

  def stopExploring(self):
    self.progress_widget.stop()

  def startActioning(self):
    self.progress_widget.setEnabled(False)

  def stopActioning(self):
    self.progress_widget.setEnabled(True)

  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self.folder_edit.text())
    if folder:
      self.folder_edit.setText(folder)

  def getConfig(self):
    data = config.InputConfig()
    data.folder = utils.toString(self.folder_edit.text())
    data.recursive = self.is_recursive_check_box.isChecked()
    data.all_extensions = self.any_extension_radio_button.isChecked()
    data.extensions = extension.FileExtensions(utils.toString(self.file_extension_edit.text())).extensionString()
    data.all_file_sizes = self.any_size_radio_button.isChecked()
    data.min_file_size_bytes = utils.stringToBytes("{} {}".format(self.filesize_spin_box.value(),
                                                                  self.filesize_combo_box.currentText()))
    data.sources = self._holder.getConfig()
    return data

  def setConfig(self, data):
    data = data or config.InputConfig()

    self.folder_edit.setText(data.folder or os.path.abspath(os.path.curdir))
    self.is_recursive_check_box.setChecked(data.recursive)
    if data.all_extensions:
      self.any_extension_radio_button.setChecked(True)
    else:
      self.restricted_extension_radio_button.setChecked(True)
    if data.all_file_sizes:
      self.any_size_radio_button.setChecked(True)
    else:
      self.restricted_size_radio_button.setChecked(True)
    self.file_extension_edit.setText(data.extensions)
    file_size, file_denom = utils.bytesToString(data.min_file_size_bytes).split()
    self.filesize_spin_box.setValue(int(float(file_size)))
    self.filesize_combo_box.setCurrentIndex(self.filesize_combo_box.findText(file_denom))
    self._holder.setConfig(data.sources or [])
    self.onSourcesWidgetFinished()

  def onSourcesWidgetFinished(self):
    sources = self._holder.getAllActiveNames()
    self.sources_edit.setText(", ".join(sources))
    #todo: act if == None

# --------------------------------------------------------------------------------------------------------------------
class NameFormatHelper:
  """ used by the output widget """
  def __init__(self, formatter, help_info, example_info, preview_info=None):
    self.formatter = formatter
    self.help_info = help_info
    self.example_info = example_info
    self.preview_info = preview_info

# --------------------------------------------------------------------------------------------------------------------
class OutputWidget(interfaces.ActionWidgetInterface):
  """ Widget allowing for the configuration of output settings """
  rename_signal = QtCore.pyqtSignal()
  stop_signal = QtCore.pyqtSignal()

  def __init__(self, mode, name_format_helper, parent=None):
    super(OutputWidget, self).__init__("output/{}".format(mode), parent)
    uic.loadUi("ui/ui_Output.ui", self)

    self._helper = name_format_helper
    self._initFormat()

    self.rename_button.clicked.connect(self.rename_signal)
    self.rename_button.setIcon(QtGui.QIcon("img/rename.png"))
    self.stop_button.clicked.connect(self.stop_signal)
    self.stop_button.setIcon(QtGui.QIcon("img/stop.png"))

    self.directory_button.clicked.connect(self._showFolderSelectionDialog)

    self.use_specific_radio.toggled.connect(self.directory_edit.setEnabled)
    self.use_specific_radio.toggled.connect(self.directory_button.setEnabled)
    self.format_edit.textChanged.connect(self._updatePreviewText)
    self.show_help_label.linkActivated.connect(self._showHelp)
    self.hide_help_label.linkActivated.connect(self._hideHelp)
    self.subtitle_check_box.toggled.connect(self.subtitle_edit.setEnabled)

    completer = QtGui.QCompleter(self)
    fs_model = QtGui.QFileSystemModel(completer)
    fs_model.setRootPath("")
    completer.setModel(fs_model)
    self.directory_edit.setCompleter(completer)

    self._is_actioning = False
    self.stopActioning()
    self.rename_button.setEnabled(False)
    self._showHelp()

  def isExecuting(self):
    return self._is_actioning

  def startExploring(self):
    self.rename_button.setEnabled(False)

  def stopExploring(self):
    self.rename_button.setEnabled(True)

  def startActioning(self):
    self._is_actioning = True
    self.progress_bar.setValue(0)
    self.progress_bar.setVisible(True)
    self.stop_button.setEnabled(True)
    self.stop_button.setVisible(True)
    self.rename_button.setVisible(False)

  def stopActioning(self):
    self._is_actioning = False
    self.progress_bar.setVisible(False)
    self.stop_button.setVisible(False)
    self.rename_button.setVisible(True)
    self.rename_button.setEnabled(True)

  def _initFormat(self):
    def escapeHtml(text):
      return text.replace("<", "&lt;").replace(">", "&gt;")

    if self.format_edit.text().isEmpty():
      self.format_edit.setText(self._helper.formatter.DEFAULT_FORMAT_STR)
    #tooltip

    help_text = ["Available options:"]
    help_values = self._helper.formatter.getValues(self._helper.help_info)
    for key, value in help_values.items():
      help_text.append("<b>{}</b>: {}".format(escapeHtml(key), value))
    if formatting.CONDITIONAL_START in self._helper.formatter.DEFAULT_FORMAT_STR:
      help_text += ["", "Enclose text within <b>%( )%</b> to optionally include text is a value is present.",
                   "Eg. <b>%(</b> Disc <b>{}</b> <b>)%</b>".format(escapeHtml("<part>"))]
    self.help_edit.setText("<html><body>{}</body></html>".format("<br/>".join(help_text)))

    self._updatePreviewText()

  def _updatePreviewText(self):
    prefix_text = "Example"
    info = self._helper.example_info
    if self._helper.preview_info:
      prefix_text = "Preview"
      info = self._helper.preview_info
    formatted_text = self._helper.formatter.getNameFromInfo(utils.toString(self.format_edit.text()), info)
    color = "red"
    if file_helper.FileHelper.isValidFilename(formatted_text):
      color = "gray"
    formatted_text = "{}: {}".format(prefix_text, file_helper.FileHelper.sanitizeFilename(formatted_text))
    self.format_example_label.setText(formatted_text)
    self.format_example_label.setStyleSheet("QLabel {{ color: {}; }}".format(color))

  def _showFolderSelectionDialog(self):
    folder = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder", self.directory_edit.text())
    if folder:
      self.directory_edit.setText(folder)

  def getConfig(self):
    data = config.OutputConfig()
    data.format = utils.toString(self.format_edit.text())
    data.folder = utils.toString(self.directory_edit.text())
    data.use_source = self.use_source_radio.isChecked()
    data.is_move = self.is_move_radio.isChecked()
    data.dont_overwrite = self.is_no_overwrite_check_box.isChecked()
    data.show_help = self.help_group_box.isVisible()
    data.action_subtitles = self.subtitle_check_box.isChecked()
    ext = utils.toString(self.subtitle_edit.text())
    data.subtitle_exts = extension.FileExtensions(ext).extensionString()
    return data

  def setConfig(self, data):
    data = data or config.OutputConfig()

    self.format_edit.setText(data.format or self._helper.formatter.DEFAULT_FORMAT_STR)
    self.directory_edit.setText(data.folder)
    if data.use_source:
      self.use_source_radio.setChecked(True)
    else:
      self.use_specific_radio.setChecked(True)
    self.is_move_radio.setChecked(data.is_move)
    self.is_no_overwrite_check_box.setChecked(data.dont_overwrite)
    self.subtitle_edit.setText(data.subtitle_exts)
    self.subtitle_check_box.setChecked(data.action_subtitles)

    if data.show_help:
      self._showHelp()
    else:
      self._hideHelp()

  def _showHelp(self):
    self.help_group_box.setVisible(True)
    self.hide_help_label.setVisible(True)
    self.show_help_label.setVisible(False)

  def _hideHelp(self):
    self.help_group_box.setVisible(False)
    self.hide_help_label.setVisible(False)
    self.show_help_label.setVisible(True)

  def onRenameItemChanged(self, item):
    info = item.getInfo() if item else None
    if info != self._helper.preview_info:
      self._helper.preview_info = info
      self._updatePreviewText()

# --------------------------------------------------------------------------------------------------------------------
class _ActionHolder:
  """ used by BaseWorkBenchWidget """
  def __init__(self, button, parent, callback, shortcut, index):
    self.name = str(button.text()) #assumes the names match
    self.button = button
    self.action = QtGui.QAction(self.name, parent)
    self.button.clicked.connect(self.action.trigger)
    self.action.triggered.connect(callback)
    self.action.setIcon(button.icon())
    if shortcut:
      self.action.setShortcut(shortcut)
    self.index = index # to keep them ordered

# --------------------------------------------------------------------------------------------------------------------
class BaseWorkBenchWidget(interfaces.ActionWidgetInterface):
  """ hacky and horrible base workbench widget """
  workbench_changed_signal = QtCore.pyqtSignal(bool)
  show_edit_sources_signal = QtCore.pyqtSignal()
  renameItemChangedSignal = QtCore.pyqtSignal(object)

  def __init__(self, mode, manager, parent=None):
    super(BaseWorkBenchWidget, self).__init__("workBench/{}".format(mode), parent)
    uic.loadUi("ui/ui_WorkBench.ui", self)
    self._model = None
    self._manager = manager
    self.select_all_check_box.clicked.connect(self._setOverallCheckedState)

    #images
    self.open_button.setIcon(QtGui.QIcon("img/open.png"))
    self.launch_button.setIcon(QtGui.QIcon("img/launch.png"))
    self.delete_button.setIcon(QtGui.QIcon("img/delete.png"))
    self.edit_episode_button.setIcon(QtGui.QIcon("img/edit.png"))
    self.edit_season_button.setIcon(QtGui.QIcon("img/edit.png"))
    self.edit_movie_button.setIcon(QtGui.QIcon("img/edit.png"))

    def createAction(actions, button, callback, shortcut=None):
      holder = _ActionHolder(button, self, callback, shortcut, len(actions))
      actions[holder.name] = holder

    self._actions = {}
    createAction(self._actions, self.open_button, self._open, QtCore.Qt.ControlModifier + QtCore.Qt.Key_O)
    createAction(self._actions, self.launch_button, self._launch, QtCore.Qt.ControlModifier + QtCore.Qt.Key_L)
    createAction(self._actions, self.edit_episode_button, self._editEpisode)
    createAction(self._actions, self.edit_season_button, self._editSeason)
    createAction(self._actions, self.edit_movie_button, self._editMovie)
    createAction(self._actions, self.delete_button, self._delete, QtCore.Qt.Key_Delete)

    self._current_index = QtCore.QModelIndex()
    self._view = self.tv_view if mode == interfaces.TV_MODE else self.movie_view #HACK. yuck
    self._view.viewport().installEventFilter(self) #filter out double right click
    self._view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

  def eventFilter(self, obj, event):
    if obj in (self.tv_view.viewport(), self.movie_view.viewport()):
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

  def _setModel(self, model):
    self._model = model
    self._model.workbench_changed_signal.connect(self._onWorkBenchChanged)
    self._onWorkBenchChanged(False)
    self._model.begin_update_signal.connect(self.startWorkBenching)
    self._model.end_update_signal.connect(self.stopWorkBenching)
    for action in self._actions.values():
      action.button.setVisible(action.name in self._model.ALL_ACTIONS)
    actions = []
    for action, enabled in self._model.getAvailableActions(self._current_index).items():
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
    file_obj = self._model.getFile(self._current_index)
    if file_obj:
      self._launchLocation(file_obj)

  def _open(self):
    file_obj = self._model.getFolder(self._current_index)
    if file_obj:
      self._launchLocation(file_obj)

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
    self.edit_episode_button.setEnabled(False)
    self.edit_season_button.setEnabled(False)
    self.edit_movie_button.setEnabled(False)
    self.launch_button.setEnabled(False)
    self.open_button.setEnabled(False)
    self.delete_button.setEnabled(False)
    self._model.endUpdate()
    self._onWorkBenchChanged(bool(self._model.items())) #HACK: TODO:

  def startActioning(self):
    self._disable()

  def stopActioning(self):
    self.tv_view.expandAll()
    self._enable()

  def _setOverallCheckedState(self, state):
    self._disable()
    self._model.setOverallCheckedState(state)
    self._enable()

  def _onWorkBenchChanged(self, has_checked):
    #utils.verifyType(has_checked, bool)
    checkState = self._model.overallCheckedState()
    self.select_all_check_box.setEnabled(not checkState is None)
    if checkState == None:
      checkState = QtCore.Qt.Unchecked
    self.select_all_check_box.setCheckState(checkState)
    self.workbench_changed_signal.emit(has_checked)

  def _delete(self):
    file_obj = self._model.getDeleteItem(self._current_index)
    if file_obj and self._deleteLocation(file_obj):
      self._model.delete(self._current_index)
      self.tv_view.expandAll()

  def _updateActions(self):
    for action, requires_key in self._model.getAvailableActions(self._current_index).items():
      self._actions[action].button.setEnabled(requires_key)
      self._actions[action].action.setEnabled(requires_key)

  def _deleteLocation(self, location):
    is_del = False
    ret = common_widget.DontShowManager.getAnswer("Please confirm delete",
      "Are you sure you want to delete this file?\n"
      "{}".format(location), "delete", parent=self)
    if ret != QtGui.QDialogButtonBox.Ok:
      return False
    try:
      send2trash(location)
      is_del = True
    except OSError as ex:
      message_box = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                             "An error occured", "Unable to move to trash. Path:\n{}".format(location))
      message_box.setDetailedText("Error:\n{}".format(str(ex)))
      message_box.exec_()
    return is_del

  def addItem(self, item):
    self._model.addItem(item)

  def actionableItems(self):
    return self._model.items()

# --------------------------------------------------------------------------------------------------------------------
class SearchResultsWidget(QtGui.QWidget):
  """ lists search results found in an info widget """
  item_selected_signal = QtCore.pyqtSignal(object)

  def __init__(self, parent=None):
    super(SearchResultsWidget, self).__init__(parent)
    uic.loadUi("ui/ui_SearchResults.ui", self)
    self._items = []
    self.results_widget.itemSelectionChanged.connect(self._onItemClicked)

  def clear(self):
    self._items = []
    self.results_widget.clearContents()
    self.results_widget.setRowCount(0)

  def addItem(self, result_holder):
    self._items.append(result_holder)
    row_count = self.results_widget.rowCount()
    self.results_widget.insertRow(row_count)

    widget = QtGui.QTableWidgetItem(str(result_holder.info))
    widget.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
    self.results_widget.setItem(row_count, 0, widget)

    widget = QtGui.QTableWidgetItem(result_holder.source_name)
    widget.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
    self.results_widget.setItem(row_count, 1, widget)

  def _onItemClicked(self):
    if self.results_widget.selectedItems():
      row = self.results_widget.selectedItems()[0].row()
      holder = self._items[row]
      self.item_selected_signal.emit(holder.info)

