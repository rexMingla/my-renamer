  #!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: MainWindow for the application
# --------------------------------------------------------------------------------------------------------------------
import functools
import threading
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import uic

from common import config
from common import file_helper
from common import utils
from common import thread
from common import widget as base_widget
from media.base import types as base_types

import app
from app import config_manager
from app import module
from app import factory

# --------------------------------------------------------------------------------------------------------------------
class MainWindow(QtGui.QMainWindow):
  """ main window for the app """
  def __init__(self, config_file="config.txt", cache_file="cache.txt", parent=None):
    super(MainWindow, self).__init__(parent)
    self.setWindowIcon(QtGui.QIcon("img/icon.ico"))
    self._config_file = config_file
    self._cache_file = cache_file

    uic.loadUi("ui/ui_MainWindow.ui", self)

    self._input_widget = QtGui.QStackedWidget(parent)
    self._work_bench_widget = QtGui.QStackedWidget(parent)
    self._output_widget = QtGui.QStackedWidget(parent)
    self._log_widget = LogWidget(parent)
    self.setCentralWidget(self._work_bench_widget)

    self._mode_to_action = {base_types.MOVIE_MODE : self.action_movie_mode,
                            base_types.TV_MODE: self.action_tv_mode}

    #dock widgets
    dock_areas = QtCore.Qt.AllDockWidgetAreas
    self._addDockWidget(self._input_widget, dock_areas, QtCore.Qt.TopDockWidgetArea, "Input Settings")
    self._addDockWidget(self._output_widget, dock_areas, QtCore.Qt.BottomDockWidgetArea, "Output Settings")
    self._addDockWidget(self._log_widget, dock_areas, QtCore.Qt.BottomDockWidgetArea, "Rename Items")

    self._config_manager = config_manager.ConfigManager()
    self._cache_manager = config_manager.ConfigManager()

    self._mode_to_module = {}
    for mode in base_types.VALID_MODES:
      self._addModule(module.RenamerModule(mode, self))
    self._mode = None
    self._auto_start = False

    #menu actions
    self.action_movie_mode.triggered.connect(functools.partial(self._setMode, mode=base_types.MOVIE_MODE))
    self.action_movie_mode.setIcon(QtGui.QIcon("img/movie.png"))
    self.action_tv_mode.triggered.connect(functools.partial(self._setMode, mode=base_types.TV_MODE))
    self.action_tv_mode.setIcon(QtGui.QIcon("img/tv.png"))
    self.action_exit.triggered.connect(self.close)
    self.action_about.triggered.connect(self._showAbout)
    self.action_about.setIcon(QtGui.QIcon("img/info.png"))
    self.action_save.triggered.connect(self._saveSettings)
    self.action_restore_defaults.triggered.connect(self._restoreDefaults)
    self.action_clear_cache.triggered.connect(self._clearCache)
    self.action_edit_tv_sources.triggered.connect(self._mode_to_module[base_types.TV_MODE].edit_sources_widget.show)
    self.action_edit_movie_sources.triggered.connect(
      self._mode_to_module[base_types.MOVIE_MODE].edit_sources_widget.show)

    self.action_toolbar.addAction(self.action_movie_mode)
    self.action_toolbar.addAction(self.action_tv_mode)

    self._is_restoring_defaults = False # used to check we aren't recursively trying to restore defaults
    self._loadSettings()

  def _showAbout(self):
    def href(link, title=""):
      return "<a href=\"{}\">{}</a>".format(link, title or link)

    def getText(mode):
      info = []
      holder = factory.Factory.getInfoClientHolder(mode)
      for store in holder.clients:
        info.append("<li>{} (interface to {})</li>".format(href(store.url, store.display_name), href(store.source_name)))
      info.append("</ul>")
      return "{} libraries:<ul>{}</ul>".format(mode.capitalize(), "\n".join(info))

    text = []
    for mode in base_types.VALID_MODES:
      text.append(getText(mode))

    msg = ("<html><p>{} is written in python with PyQt.<p/>\n"
          "<p>Special thanks to the following:</p>\n{}"
          "<p>The wand icon come from {}</p>\n"
          "<p>Button images come from {}</p>\n"
          "<p>For (slightly) more information go to {}"
          "</html>").format(app.__NAME__, "\n\n".join(text),
                            href("http://www.designkindle.com/2011/10/07/build-icons/", "Umar Irshad"),
                            href("http://www.smashingmagazine.com/2011/12/29/freebie-free-vector-web-icons-91-icons/",
                                 "Tomas Gajar"),
                            href("http://code.google.com/p/my-renamer/", "google code"))
    QtGui.QMessageBox.about(self, "About {}".format(app.__NAME__), msg)

  def _addModule(self, mod):
    self._mode_to_module[mod.mode] = mod
    self._input_widget.addWidget(mod.input_widget)
    self._work_bench_widget.addWidget(mod.work_bench)
    self._output_widget.addWidget(mod.output_widget)
    mod.new_rename_items_signal.connect(self._log_widget.addItems)

  def showEvent(self, event):
    super(MainWindow, self).showEvent(event)
    if not self._auto_start:
      welcome_widget = WelcomeWidget(self._mode, self)
      welcome_widget.exec_()
      self._setMode(welcome_widget.mode())
      self._auto_start = welcome_widget.isAutoStart()
    event.accept()

  def closeEvent(self, event):
    mod = self._mode_to_module[self._mode]
    if self._log_widget.isExecuting():
      response = QtGui.QMessageBox.warning(self, "You have unfinished renames",
                                           "Do you want to keep your pending requests?",
                                           QtGui.QMessageBox.Discard, QtGui.QMessageBox.Cancel)
      if response == QtGui.QMessageBox.Cancel:
        event.ignore()
        return
    self._saveSettings()
    event.accept()

  def _addDockWidget(self, widget, areas, default_area, name):
    #utils.verifyType(widget, QtGui.QWidget)
    #utils.verifyType(areas, int)
    #utils.verifyType(default_area, int)
    #utils.verifyType(name, str)
    dock = QtGui.QDockWidget(name, widget.parent())
    dock.setObjectName(name)
    dock.setWidget(widget)
    dock.setAllowedAreas(areas)
    self.addDockWidget(default_area, dock)
    return dock

  def _setMode(self, mode):
    assert(mode in base_types.VALID_MODES)
    for _mode, action in self._mode_to_action.items():
      action.setChecked(_mode == mode)

    if self._mode:
      self._mode_to_module[self._mode].setInactive()

    self._mode = mode
    mod = self._mode_to_module[self._mode]
    self._input_widget.setCurrentWidget(mod.input_widget)
    self._work_bench_widget.setCurrentWidget(mod.work_bench)
    self._output_widget.setCurrentWidget(mod.output_widget)
    mod.setActive()
    self.setWindowTitle("{} [{} mode]".format(app.__NAME__, self._mode.capitalize()))

    self.menu_action.clear()
    self.menu_action.addActions(self._mode_to_module[self._mode].input_widget.actions())
    self.menu_action.addSeparator()
    self.menu_action.addActions(self._mode_to_module[self._mode].work_bench.actions())

  def _saveSettings(self):
    self._saveSettingsConfig()
    self._saveCache()

  def _saveSettingsConfig(self):
    data = config.MainWindowConfig()
    data.geo = utils.toString(self.saveGeometry().toBase64())
    data.state = utils.toString(self.saveState().toBase64())
    data.mode = self._mode
    data.auto_start = self._auto_start
    data.dont_shows = base_widget.DontShowManager.getConfig()
    self._config_manager.setData("mw", data)

    for module in self._mode_to_module.values():
      for widget in [module.input_widget, module.output_widget, module.work_bench]:
        self._config_manager.setData(widget.config_name, widget.getConfig())
    self._config_manager.saveConfig(self._config_file)

  def _saveCache(self):
    self._cache_manager.setData("version", config.CACHE_VERSION)
    for m in base_types.VALID_MODES:
      manager = factory.Factory.getManager(m)
      self._cache_manager.setData("cache/{}".format(m), manager.cache())
    self._cache_manager.saveConfig(self._cache_file)

  def _loadSettings(self):
    self._loadSettingsConfig()
    self._loadCache()

  def _loadSettingsConfig(self):
    self._config_manager.loadConfig(self._config_file)

    try:
      data = self._config_manager.getData("mw", config.MainWindowConfig())
      config_version = data.config_version if isinstance(data, config.MainWindowConfig) else "0.0"
      if config_version != config.CONFIG_VERSION:
        utils.logDebug(
            "config version of out date, loading default. old={} new={}".format(config_version, config.CONFIG_VERSION))
        return

      self.restoreGeometry(QtCore.QByteArray.fromBase64(data.geo))
      self.restoreState(QtCore.QByteArray.fromBase64(data.state))
      base_widget.DontShowManager.setConfig(data.dont_shows)
      if not data.mode in base_types.VALID_MODES:
        data.mode = base_types.TV_MODE
      self._setMode(data.mode)
      self._auto_start = data.auto_start

      for module in self._mode_to_module.values():
        for widget in [module.input_widget, module.output_widget, module.work_bench]:
          widget.setConfig(self._config_manager.getData(widget.config_name, None))
    except (AttributeError, ValueError, TypeError, IndexError, KeyError) as ex:
      utils.logWarning("Unable to load config file. reason: {}".format(ex))
      if not self._is_restoring_defaults:
        self._restoreDefaults()
      else:
        QtGui.QMessageBox.warning(self, "Config error", "Default config is in a bad state. Fix me!")

  def _loadCache(self):
    self._cache_manager.loadConfig(self._cache_file)
    cache_version = self._cache_manager.getData("version", "0.0")
    if cache_version != config.CACHE_VERSION:
      utils.logDebug(
          "cache version of out date, loading default. old={} new={}".format(cache_version, config.CACHE_VERSION))
      return

    for mode in base_types.VALID_MODES:
      factory.Factory.getManager(mode).setCache(self._cache_manager.getData("cache/{}".format(mode), {}))

  def _restoreDefaults(self):
    self._is_restoring_defaults = True
    file_helper.FileHelper.removeFile(self._config_file)
    self._loadSettingsConfig()
    self._is_restoring_defaults = False

  def _clearCache(self):
    file_helper.FileHelper.removeFile(self._cache_file)
    self._loadCache()

# --------------------------------------------------------------------------------------------------------------------
class WelcomeWidget(QtGui.QDialog):
  """ First prompt seen by the user, to select movie / tv mode. """
  def __init__(self, mode, parent=None):
    utils.verify(mode in base_types.VALID_MODES, "mode must be valid")
    super(WelcomeWidget, self).__init__(parent)
    uic.loadUi("ui/ui_Welcome.ui", self)
    self.setWindowTitle("Welcome to {}".format(app.__NAME__))
    self.setWindowModality(True)

    if mode == base_types.MOVIE_MODE:
      self.movie_radio.setChecked(True)
    else:
      self.tv_radio.setChecked(True)

  def mode(self):
    return base_types.MOVIE_MODE if self.movie_radio.isChecked() else base_types.TV_MODE

  def isAutoStart(self):
    return self.is_auto_start_check_box.isChecked()

# --------------------------------------------------------------------------------------------------------------------
class _LogModel(QtCore.QAbstractTableModel):
  COL_ACTION      = 0
  COL_DESCRIPTION = 1
  COL_STATUS      = 2
  NUM_COLS        = 3  

  def __init__(self, parent):
    super(_LogModel, self).__init__(parent)
    self._items = []

  def rowCount(self, _parent):
    return len(self._items)

  def columnCount(self, _parent):
    return _LogModel.NUM_COLS

  def data(self, index, role):
    if not index.isValid():
      return None

    if role not in (QtCore.Qt.ForegroundRole, QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole):
      return None

    item, percentage_complete = self._items[index.row()]
    if role == QtCore.Qt.ForegroundRole and index.column() == _LogModel.COL_STATUS:
      if item.status == item.QUEUED:
        return QtGui.QBrush(QtCore.Qt.black)
      elif item.status == item.IN_PROGRESS:
        return QtGui.QBrush(QtCore.Qt.blue)
      elif item.status == item.SUCCESS:
        return QtGui.QBrush(QtCore.Qt.green)
      else:
        return QtGui.QBrush(QtCore.Qt.red)
    elif index.column() == _LogModel.COL_STATUS:
      status = item.status
      if status == item.IN_PROGRESS:
        status = "{} {}%".format(status, percentage_complete)
      return status
    elif index.column() == _LogModel.COL_ACTION:
      return item.action_text
    elif index.column() == _LogModel.COL_DESCRIPTION:
      if role == QtCore.Qt.DisplayRole:
        return item.shortDescription()
      else:
        return item.longDescription()
      
  def headerData(self, section, orientation, role):
    if role != QtCore.Qt.DisplayRole or orientation == QtCore.Qt.Vertical:
      return None
    
    if section == _LogModel.COL_ACTION:
      return "Action"
    elif section == _LogModel.COL_DESCRIPTION:
      return "Description"
    if section == _LogModel.COL_STATUS:
      return "Status"

  #def flags(self, index):
  #  if not index.isValid():
  #    return QtCore.Qt.NoItemFlags
  #  return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
  
  def addItems(self, items):
    if not items:
      return
    rows = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), rows, rows + len(items) - 1)
    self._items.extend([ (i, 0) for i in items]) #item and percentage complete
    self.endInsertRows()
    
  def itemChanged(self, item, percentage=0):
    row = self._findRow(item)
    if row != -1:
      self._items[row] = (item, percentage)
      status_cell = self.index(row, _LogModel.COL_STATUS)
      self.dataChanged.emit(status_cell, status_cell)
    
  def _findRow(self, item):
    return next( (i for i, val in enumerate(self._items) if item.id_ == val[0].id_), -1) 

# --------------------------------------------------------------------------------------------------------------------
class _RenameThread(thread.WorkerThread):
  item_changed_signal = QtCore.pyqtSignal(object, int)
  """ 
  thread responsible for performing the rename
  
  Args:
    items: list of common.renamer.BaseRenamer objects to be renamed
  """
  def __init__(self, name="renamer", items=None):
    super(_RenameThread, self).__init__(name)
    self._mutex = threading.Lock()
    self._items = items or []
    self._current_item = None
    
  def _run(self):
    while not self._user_stopped:
      self._current_item = None
      with self._mutex:
        if not self._items:
          break
        self._current_item = self._items.pop(0)
      self._current_item.performAction(progress_cb=self._itemUpdated)
      self._itemUpdated()
      
  def _itemUpdated(self, percentage=0):
    self.item_changed_signal.emit(self._current_item, percentage)
    return not self._user_stopped

  def addItems(self, items):
    with self._mutex:
      self._items.extend(items)

# --------------------------------------------------------------------------------------------------------------------
class LogWidget(QtGui.QWidget):
  """ Widget to display log messages to the user """
  def __init__(self, parent=None):
    super(LogWidget, self).__init__(parent)
    uic.loadUi("ui/ui_LogWidget.ui", self)
    #self.clear_button.clicked.connect(self._clearLog)
    #self.clear_button.setIcon(QtGui.QIcon("img/clear.png"))
    #self.clear_button.setEnabled(True)

    self._model = _LogModel(self)
    self.log_view.setModel(self._model)
    self.log_view.horizontalHeader().setResizeMode(_LogModel.COL_ACTION, QtGui.QHeaderView.Interactive)
    self.log_view.horizontalHeader().resizeSection(_LogModel.COL_ACTION, 75)
    self.log_view.horizontalHeader().setResizeMode(_LogModel.COL_DESCRIPTION, QtGui.QHeaderView.Interactive)
    self.log_view.horizontalHeader().setResizeMode(_LogModel.COL_STATUS, QtGui.QHeaderView.Interactive)
    self.log_view.horizontalHeader().resizeSection(_LogModel.COL_STATUS, 80)
    self.log_view.horizontalHeader().setStretchLastSection(True)
    
    self._rename_thread = None#_RenameThread()
    #self._rename_thread.item_percentage_changed_signal.connect(self._model.percentageChanged)
    #self._rename_thread.item_status_changed_signal.connect(self._model.itemChanged)
    #self._rename_thread.log_signal.connect(self._onLog)
    
  def __del__(self):
    if self._rename_thread:
      self._rename_thread.join()
    
  def setConfig(self, data):
    """ Update from settings """
    pass
    
  def getConfig(self):
    pass
  
  def addItems(self, items):
    self._model.addItems(items)
    if not self._rename_thread:
      self._rename_thread = _RenameThread(items=items)
      self._rename_thread.item_changed_signal.connect(self._model.itemChanged)
      self._rename_thread.log_signal.connect(self._onLog)      
    else:
      self._rename_thread.addItems(items)      
    if not self.isExecuting():
      self._rename_thread.start()
    
  def isExecuting(self):
    return self._rename_thread and self._rename_thread.isRunning()
    
  def _onLog(self, log):
    utils.logError(log)


