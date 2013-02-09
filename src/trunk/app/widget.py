  #!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: MainWindow for the application
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import uic
import functools

from common import config
from common import interfaces
from common import file_helper
from common import utils
from common import widget as base_widget

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

    self._mode_to_action = {interfaces.MOVIE_MODE : self.action_movie_mode,
                            interfaces.TV_MODE: self.action_tv_mode}

    #dock widgets
    dock_areas = QtCore.Qt.AllDockWidgetAreas
    self._addDockWidget(self._input_widget, dock_areas, QtCore.Qt.TopDockWidgetArea, "Input Settings")
    self._addDockWidget(self._output_widget, dock_areas, QtCore.Qt.BottomDockWidgetArea, "Output Settings")
    self._addDockWidget(self._log_widget, dock_areas, QtCore.Qt.BottomDockWidgetArea, "Message Log")

    self._config_manager = config_manager.ConfigManager()
    self._cache_manager = config_manager.ConfigManager()

    self._mode_to_module = {}
    for mode in interfaces.VALID_MODES:
      self._addModule(module.RenamerModule(mode, self))
    self._mode = None
    self._auto_start = False

    #menu actions
    self.action_movie_mode.triggered.connect(functools.partial(self._setMode, mode=interfaces.MOVIE_MODE))
    self.action_movie_mode.setIcon(QtGui.QIcon("img/movie.png"))
    self.action_tv_mode.triggered.connect(functools.partial(self._setMode, mode=interfaces.TV_MODE))
    self.action_tv_mode.setIcon(QtGui.QIcon("img/tv.png"))
    self.action_exit.triggered.connect(self.close)
    self.action_about.triggered.connect(self._showAbout)
    self.action_about.setIcon(QtGui.QIcon("img/info.png"))
    self.action_save.triggered.connect(self._saveSettings)
    self.action_restore_defaults.triggered.connect(self._restoreDefaults)
    self.action_clear_cache.triggered.connect(self._clearCache)
    self.action_edit_tv_sources.triggered.connect(self._mode_to_module[interfaces.TV_MODE].edit_sources_widget.show)
    self.action_edit_movie_sources.triggered.connect(
      self._mode_to_module[interfaces.MOVIE_MODE].edit_sources_widget.show)

    self.action_toolbar.addAction(self.action_movie_mode)
    self.action_toolbar.addAction(self.action_tv_mode)

    self._is_restoring_defaults = False # used to check we aren't recursively trying to restore defaults
    self._loadSettings()

  def _showAbout(self):
    def href(link, title=""):
      return "<a href=\"{}\">{}</a>".format(link, title or link)

    def getText(mode):
      info = []
      holder = factory.Factory.getStoreHolder(mode)
      for store in holder.stores:
        info.append("<li>{} (interface to {})</li>".format(href(store.url, store.display_name), href(store.source_name)))
      info.append("</ul>")
      return "{} libraries:<ul>{}</ul>".format(mode.capitalize(), "\n".join(info))

    text = []
    for mode in interfaces.VALID_MODES:
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
    mod.log_signal.connect(self._log_widget.appendMessage)

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
    if mod.output_widget.isExecuting():
      response = QtGui.QMessageBox.warning(self, "You have unfinished renames",
                                           "Do you want to keep your pending renames?",
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
    assert(mode in interfaces.VALID_MODES)
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
    for m in interfaces.VALID_MODES:
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
      if not data.mode in interfaces.VALID_MODES:
        data.mode = interfaces.TV_MODE
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

    for mode in interfaces.VALID_MODES:
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
    utils.verify(mode in interfaces.VALID_MODES, "mode must be valid")
    super(WelcomeWidget, self).__init__(parent)
    uic.loadUi("ui/ui_Welcome.ui", self)
    self.setWindowTitle("Welcome to {}".format(app.__NAME__))
    self.setWindowModality(True)

    if mode == interfaces.MOVIE_MODE:
      self.movie_radio.setChecked(True)
    else:
      self.tv_radio.setChecked(True)

  def mode(self):
    return interfaces.MOVIE_MODE if self.movie_radio.isChecked() else interfaces.TV_MODE

  def isAutoStart(self):
    return self.is_auto_start_check_box.isChecked()

# --------------------------------------------------------------------------------------------------------------------
class LogWidget(QtGui.QWidget):
  """ Widget to display log messages to the user """
  def __init__(self, parent=None):
    super(LogWidget, self).__init__(parent)
    uic.loadUi("ui/ui_LogWidget.ui", self)
    self.clear_button.clicked.connect(self._clearLog)
    self.clear_button.setIcon(QtGui.QIcon("img/clear.png"))
    self.clear_button.setEnabled(True)

    self._model = _LogModel(self)
    self.log_view.setModel(self._model)
    self.log_view.horizontalHeader().setResizeMode(_LogColumns.COL_ACTION, QtGui.QHeaderView.Interactive)
    self.log_view.horizontalHeader().resizeSection(_LogColumns.COL_ACTION, 75)
    self.log_view.horizontalHeader().setResizeMode(_LogColumns.COL_MESSAGE, QtGui.QHeaderView.Interactive)
    self.log_view.horizontalHeader().setStretchLastSection(True)

    self._is_updating = False

  def onRename(self):
    if self.autoClearCheckBox.isChecked():
      self._clearLog()

  def appendMessage(self, item):
    #utils.verifyType(item, LogItem)
    self._model.addItem(item)

  def _clearLog(self):
    self._model.clearItems()

  def setConfig(self, data):
    """ Update from settings """
    self.autoClearCheckBox.setChecked(data.get("autoClear", False))

  def getConfig(self):
    return {"autoClear" : self.autoClearCheckBox.isChecked()}

# --------------------------------------------------------------------------------------------------------------------
class _LogColumns:
  """ Columns used in log model. """
  #COL_LEVEL   = 0
  COL_ACTION  = 0
  COL_MESSAGE = 1
  NUM_COLS    = 2

# --------------------------------------------------------------------------------------------------------------------
class _LogModel(QtCore.QAbstractTableModel):
  """ Collection of LogItems wrapped in a QAbstractTableModel """
  LOG_LEVEL_ROLE = QtCore.Qt.UserRole + 1

  def __init__(self, parent):
    super(_LogModel, self).__init__(parent)
    self.items = []

  def rowCount(self, _parent):
    return len(self.items)

  def columnCount(self, _parent):
    return _LogColumns.NUM_COLS

  def data(self, index, role):
    if not index.isValid():
      return None

    if role not in (QtCore.Qt.ForegroundRole, QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole):
      return None

    item = self.items[index.row()]
    if role == QtCore.Qt.ForegroundRole and item.log_level >= utils.LogLevel.ERROR:
      return QtGui.QBrush(QtCore.Qt.red)
    elif role == _LogModel.LOG_LEVEL_ROLE:
      return item.log_level
    elif index.column() == _LogColumns.COL_ACTION:
      return item.action
    elif index.column() == _LogColumns.COL_MESSAGE:
      if role == QtCore.Qt.DisplayRole:
        return item.short_message
      else:
        return item.long_message
    else:
      return None

  def headerData(self, section, orientation, role):
    if role != QtCore.Qt.DisplayRole or orientation == QtCore.Qt.Vertical:
      return None

    #if section == _LogColumns.COL_LEVEL:
    #  return "Type"
    if section == _LogColumns.COL_ACTION:
      return "Action"
    elif section == _LogColumns.COL_MESSAGE:
      return "Message"
    return None

  def addItem(self, item):
    #utils.verifyType(item, LogItem)
    utils.log(item.log_level, msg=item.short_message, long_msg=item.long_message, title=item.action)
    count = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), count, count)
    self.items.append(item)
    self.endInsertRows()

  def clearItems(self):
    count = self.rowCount(QtCore.QModelIndex())
    if count:
      self.beginResetModel()
      self.items = []
      self.endResetModel()
