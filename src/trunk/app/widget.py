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

from common import config
from common import interfaces
from common import file_helper
from common import utils
from common import dont_show

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
    self._add_dock_widget(self._input_widget, dock_areas, QtCore.Qt.TopDockWidgetArea, "Input Settings")
    self._add_dock_widget(self._output_widget, dock_areas, QtCore.Qt.BottomDockWidgetArea, "Output Settings")
    self._add_dock_widget(self._log_widget, dock_areas, QtCore.Qt.BottomDockWidgetArea, "Message Log")
    
    self._config_manager = config_manager.ConfigManager()
    self._cache_manager = config_manager.ConfigManager()
    
    self._mode_to_module = {}
    for mode in interfaces.VALID_MODES:
      self._add_module(module.RenamerModule(mode, self))
    self._mode = None
    self._auto_start = False
    
    #menu actions
    self.action_movie_mode.triggered.connect(self._set_movie_mode)
    self.action_movie_mode.setIcon(QtGui.QIcon("img/movie.png"))
    self.action_tv_mode.triggered.connect(self._set_tv_mode)
    self.action_tv_mode.setIcon(QtGui.QIcon("img/tv.png"))                                     
    self.action_exit.triggered.connect(self.close)
    self.action_about.triggered.connect(self._show_about)
    self.action_about.setIcon(QtGui.QIcon("img/info.png"))
    self.action_save.triggered.connect(self._save_settings)
    self.action_restore_defaults.triggered.connect(self._restore_defaults)
    self.action_clear_cache.triggered.connect(self._clear_cache)
    self.action_edit_tv_sources.triggered.connect(self._mode_to_module[interfaces.TV_MODE].edit_sources_widget.show)
    self.action_edit_movie_sources.triggered.connect(
      self._mode_to_module[interfaces.MOVIE_MODE].edit_sources_widget.show)
    
    self.action_toolbar.addAction(self.action_movie_mode)
    self.action_toolbar.addAction(self.action_tv_mode)
    
    self._is_restoring_defaults = False # used to check we aren't recursively trying to restore defaults
    self._load_settings()
    
  def _show_about(self):
    def href(link, title=""):
      return "<a href=\"{}\">{}</a>".format(link, title or link)
    
    def get_text(mode):
      info = []
      holder = factory.Factory.get_store_helper(mode)
      for store in holder.stores:
        info.append("<li>{} (interface to {})</li>".format(href(store.url, store.display_name), href(store.source_name)))
      info.append("</ul>")
      return "{} libraries:<ul>{}</ul>".format(mode.capitalize(), "\n".join(info))
    
    text = []
    for mode in interfaces.VALID_MODES:
      text.append(get_text(mode))
    
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
    
  def _add_module(self, mod):
    self._mode_to_module[mod.mode] = mod
    self._input_widget.addWidget(mod.input_widget)
    self._work_bench_widget.addWidget(mod.work_bench)
    self._output_widget.addWidget(mod.output_widget) 
    mod.log_signal.connect(self._log_widget.append_message)
    
  def showEvent(self, event):
    super(MainWindow, self).showEvent(event)
    if not self._auto_start:
      welcome_widget = WelcomeWidget(self._mode, self)
      welcome_widget.exec_()
      self._set_mode(welcome_widget.mode())
      self._auto_start = welcome_widget.is_auto_start()
    event.accept()
    
  def closeEvent(self, event):
    mod = self._mode_to_module[self._mode]
    if mod.output_widget.is_executing():
      response = QtGui.QMessageBox.warning(self, "You have unfinished renames", 
                                           "Do you want to keep your pending renames?", 
                                           QtGui.QMessageBox.Discard, QtGui.QMessageBox.Cancel)
      if response == QtGui.QMessageBox.Cancel:
        event.ignore()
        return
    self._save_settings()
    event.accept()
    
  def _add_dock_widget(self, widget, areas, default_area, name):
    #utils.verify_type(widget, QtGui.QWidget)
    #utils.verify_type(areas, int)
    #utils.verify_type(default_area, int)
    #utils.verify_type(name, str)
    dock = QtGui.QDockWidget(name, widget.parent())
    dock.setObjectName(name)
    dock.setWidget(widget)
    dock.setAllowedAreas(areas)
    self.addDockWidget(default_area, dock)
    return dock
  
  def _set_movie_mode(self):
    self._set_mode(interfaces.MOVIE_MODE)
  
  def _set_tv_mode(self):
    self._set_mode(interfaces.TV_MODE)

  def _set_mode(self, mode):
    assert(mode in interfaces.VALID_MODES)
    for _mode, action in self._mode_to_action.items():
      action.setChecked(_mode == mode)
    
    if self._mode:
      self._mode_to_module[self._mode].set_inactive()
    
    self._mode = mode
    mod = self._mode_to_module[self._mode]
    self._input_widget.setCurrentWidget(mod.input_widget)
    self._work_bench_widget.setCurrentWidget(mod.work_bench)
    self._output_widget.setCurrentWidget(mod.output_widget)
    mod.set_active()
    self.setWindowTitle("{} [{} mode]".format(app.__NAME__, self._mode.capitalize()))

    self.menu_action.clear()
    self.menu_action.addActions(self._mode_to_module[self._mode].input_widget.actions())
    self.menu_action.addSeparator()
    self.menu_action.addActions(self._mode_to_module[self._mode].work_bench.actions())
  
  def _save_settings(self):
    self._save_settings_config()
    self._save_cache()
  
  def _save_settings_config(self):
    data = config.MainWindowConfig()
    data.geo = utils.to_string(self.saveGeometry().toBase64())
    data.state = utils.to_string(self.saveState().toBase64())
    data.mode = self._mode
    data.auto_start = self._auto_start
    data.dont_shows = dont_show.DontShowManager.get_config()
    self._config_manager.set_data("mw", data)

    for module in self._mode_to_module.values():
      for widget in [module.input_widget, module.output_widget, module.work_bench]:
        self._config_manager.set_data(widget.config_name, widget.get_config())
    self._config_manager.save_config(self._config_file)
    
  def _save_cache(self):
    self._cache_manager.set_data("version", config.CACHE_VERSION)    
    for m in interfaces.VALID_MODES:
      manager = factory.Factory.get_manager(m)
      self._cache_manager.set_data("cache/{}".format(m), manager.cache())  
    self._cache_manager.save_config(self._cache_file)
      
  def _load_settings(self):
    self._load_settings_config()
    self._load_cache()
    
  def _load_settings_config(self):
    self._config_manager.load_config(self._config_file)
  
    try:
      data = self._config_manager.get_data("mw", config.MainWindowConfig())
      config_version = data.config_version if isinstance(data, config.MainWindowConfig) else "0.0"
      if config_version != config.CONFIG_VERSION:
        utils.log_debug(
            "config version of out date, loading default. old={} new={}".format(config_version, config.CONFIG_VERSION))
        return
      
      self.restoreGeometry(QtCore.QByteArray.fromBase64(data.geo))
      self.restoreState(QtCore.QByteArray.fromBase64(data.state))
      dont_show.DontShowManager.set_config(data.dont_shows)
      if not data.mode in interfaces.VALID_MODES:
        data.mode = interfaces.TV_MODE
      self._set_mode(data.mode)
      self._auto_start = data.auto_start
      
      for module in self._mode_to_module.values():
        for widget in [module.input_widget, module.output_widget, module.work_bench]:
          widget.set_config(self._config_manager.get_data(widget.config_name, None))    
    except (AttributeError, ValueError, TypeError, IndexError, KeyError) as ex:
      utils.log_warning("Unable to load config file. reason: {}".format(ex))
      if not self._is_restoring_defaults:
        self._restore_defaults()
      else:
        QtGui.QMessageBox.warning(self, "Config error", "Default config is in a bad state. Fix me!")
          
  def _load_cache(self):
    self._cache_manager.load_config(self._cache_file)
    cache_version = self._cache_manager.get_data("version", "0.0")
    if cache_version != config.CACHE_VERSION:
      utils.log_debug(
          "cache version of out date, loading default. old={} new={}".format(cache_version, config.CACHE_VERSION))
      return
    
    for mode in interfaces.VALID_MODES:
      factory.Factory.get_manager(mode).set_cache(self._cache_manager.get_data("cache/{}".format(mode), {}))    
  
  def _restore_defaults(self):
    self._is_restoring_defaults = True
    file_helper.FileHelper.remove_file(self._config_file)
    self._load_settings_config()
    self._is_restoring_defaults = False
    
  def _clear_cache(self):
    file_helper.FileHelper.remove_file(self._cache_file)
    self._load_cache()
    
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
  
  def is_auto_start(self):
    return self.is_auto_start_check_box.isChecked()

# --------------------------------------------------------------------------------------------------------------------
class LogWidget(QtGui.QWidget):
  """ Widget to display log messages to the user """
  def __init__(self, parent=None):
    super(LogWidget, self).__init__(parent)
    uic.loadUi("ui/ui_LogWidget.ui", self)
    self.clear_button.clicked.connect(self._clear_log)
    self.clear_button.setIcon(QtGui.QIcon("img/clear.png"))    
    self.clear_button.setEnabled(True)

    self._model = _LogModel(self)
    self.log_view.setModel(self._model)
    self.log_view.horizontalHeader().setResizeMode(_LogColumns.COL_ACTION, QtGui.QHeaderView.Interactive)
    self.log_view.horizontalHeader().resizeSection(_LogColumns.COL_ACTION, 75)
    self.log_view.horizontalHeader().setResizeMode(_LogColumns.COL_MESSAGE, QtGui.QHeaderView.Interactive)
    self.log_view.horizontalHeader().setStretchLastSection(True)
    
    self._is_updating = False
    
  def on_rename(self):
    if self.autoClearCheckBox.isChecked():
      self._clear_log()
    
  def append_message(self, item):
    #utils.verify_type(item, LogItem)
    self._model.add_item(item)
    
  def _clear_log(self):
    self._model.clear_items()
    
  def set_config(self, data):
    """ Update from settings """
    self.autoClearCheckBox.setChecked(data.get("autoClear", False))
  
  def get_config(self):
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
    
  def add_item(self, item):
    #utils.verify_type(item, LogItem)
    utils.log(item.log_level, msg=item.short_message, long_msg=item.long_message, title=item.action)
    count = self.rowCount(QtCore.QModelIndex())
    self.beginInsertRows(QtCore.QModelIndex(), count, count)
    self.items.append(item)
    self.endInsertRows()
    
  def clear_items(self):
    count = self.rowCount(QtCore.QModelIndex())
    if count:
      self.beginResetModel()
      self.items = []
      self.endResetModel()