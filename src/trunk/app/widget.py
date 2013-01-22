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
  def __init__(self, configFile="config.txt", cacheFile="cache.txt", parent = None):
    super(MainWindow, self).__init__(parent)
    self.setWindowIcon(QtGui.QIcon("img/icon.ico"))
    self._configFile = configFile
    self._cacheFile = cacheFile
    
    uic.loadUi("ui/ui_MainWindow.ui", self)
    
    self._inputStackWidget = QtGui.QStackedWidget(parent)
    self._workBenchStackWidget = QtGui.QStackedWidget(parent)
    self._outputStackWidget = QtGui.QStackedWidget(parent)
    self._logWidget = LogWidget(parent)
    self.setCentralWidget(self._workBenchStackWidget)
    
    self._modeToAction = {interfaces.Mode.MOVIE_MODE : self.actionMovieMode, 
                          interfaces.Mode.TV_MODE: self.actionTvMode}
                
    #dock widgets
    dockAreas = QtCore.Qt.AllDockWidgetAreas
    self._addDockWidget(self._inputStackWidget, dockAreas, QtCore.Qt.TopDockWidgetArea, "Input Settings")
    self._addDockWidget(self._outputStackWidget, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Output Settings")
    self._addDockWidget(self._logWidget, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Message Log")
    
    self._config_manager = config_manager.ConfigManager()
    self._cacheManager = config_manager.ConfigManager()
    
    self._modeToModule = {}
    for mode in interfaces.VALID_MODES:
      self._addModule(module.RenamerModule(mode, self))
    self._mode = None
    self._autoStart = False
    
    #menu actions
    self.actionMovieMode.triggered.connect(self._setMovieMode)
    self.actionMovieMode.setIcon(QtGui.QIcon("img/movie.png"))
    self.actionTvMode.triggered.connect(self._setTvMode)
    self.actionTvMode.setIcon(QtGui.QIcon("img/tv.png"))                                     
    self.actionExit.triggered.connect(self.close)
    self.actionAbout.triggered.connect(self._showAbout)
    self.actionAbout.setIcon(QtGui.QIcon("img/info.png"))
    self.actionSave.triggered.connect(self._saveSettings)
    self.actionRestoreDefaults.triggered.connect(self._restoreDefaults)
    self.actionClearCache.triggered.connect(self._clearCache)
    self.actionEditTvSources.triggered.connect(self._modeToModule[interfaces.Mode.TV_MODE].editSourcesWidget.show)
    self.actionEditMovieSources.triggered.connect(self._modeToModule[interfaces.Mode.MOVIE_MODE].editSourcesWidget.show)
    
    self.actionToolBar.addAction(self.actionMovieMode)
    self.actionToolBar.addAction(self.actionTvMode)
    
    self._restoringDefaults = False # used to check we aren't recursively trying to restore defaults
    self._loadSettings()
    
  def _showAbout(self):
    def href(link, title=""):
      return "<a href=\"{}\">{}</a>".format(link, title or link)
    
    def getText(mode):
      info = []
      holder = factory.Factory.getStoreHolder(mode)
      for s in holder.stores:
        info.append("<li>{} (interface to {})</li>".format(href(s.url, s.displayName), href(s.sourceName)))
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
    self._modeToModule[mod.mode] = mod
    self._inputStackWidget.addWidget(mod.inputWidget)
    self._workBenchStackWidget.addWidget(mod.workBenchWidget)
    self._outputStackWidget.addWidget(mod.outputWidget) 
    mod.logSignal.connect(self._logWidget.appendMessage)
    
  def showEvent(self, event):
    super(MainWindow, self).showEvent(event)
    if not self._autoStart:
      ww = WelcomeWidget(self._mode, self)
      ww.exec_()
      self._setMode(ww.mode())
      self._autoStart = ww.isAutoStart()
    event.accept()
    
  def closeEvent(self, event):
    mod = self._modeToModule[self._mode]
    if mod.outputWidget.isExecuting():
      response = QtGui.QMessageBox.warning(self, "You have unfinished renames", 
                                           "Do you want to keep your pending renames?", 
                                           QtGui.QMessageBox.Discard, QtGui.QMessageBox.Cancel)
      if response == QtGui.QMessageBox.Cancel:
        event.ignore()
        return
    self._saveSettings()
    event.accept()
    
  def _addDockWidget(self, widget, areas, defaultArea, name):
    #utils.verifyType(widget, QtGui.QWidget)
    #utils.verifyType(areas, int)
    #utils.verifyType(defaultArea, int)
    #utils.verifyType(name, str)
    dock = QtGui.QDockWidget(name, widget.parent())
    dock.setObjectName(name)
    dock.setWidget(widget)
    dock.setAllowedAreas(areas)
    self.addDockWidget(defaultArea, dock)
    return dock
  
  def _setMovieMode(self):
    self._setMode(interfaces.Mode.MOVIE_MODE)
  
  def _setTvMode(self):
    self._setMode(interfaces.Mode.TV_MODE)

  def _setMode(self, mode):
    assert(mode in interfaces.VALID_MODES)
    for m, action in self._modeToAction.items():
      action.setChecked(m == mode)
    
    if self._mode:
      self._modeToModule[self._mode].setInactive()
    
    self._mode = mode
    mod = self._modeToModule[self._mode]
    self._inputStackWidget.setCurrentWidget(mod.inputWidget)
    self._workBenchStackWidget.setCurrentWidget(mod.workBenchWidget)
    self._outputStackWidget.setCurrentWidget(mod.outputWidget)
    mod.setActive()
    self.setWindowTitle("{} [{} mode]".format(app.__NAME__, self._mode.capitalize()))

    self.menuAction.clear()
    self.menuAction.addActions(self._modeToModule[self._mode].inputWidget.actions())
    self.menuAction.addSeparator()
    self.menuAction.addActions(self._modeToModule[self._mode].workBenchWidget.actions())
  
  def _saveSettings(self):
    self._saveSettingsConfig()
    self._saveCache()
  
  def _saveSettingsConfig(self):
    data = config.MainWindowConfig()
    data.geo = utils.toString(self.saveGeometry().toBase64())
    data.state = utils.toString(self.saveState().toBase64())
    data.mode = self._mode
    data.autoStart = self._autoStart
    data.dontShows = dont_show.DontShowManager.getConfig()
    data.configVersion = config.CONFIG_VERSION
    self._config_manager.setData("mw", data)

    for m in self._modeToModule.values():
      for w in [m.inputWidget, m.outputWidget, m.workBenchWidget]:
        self._config_manager.setData(w.configName, w.getConfig())
    self._config_manager.saveConfig(self._configFile)
    
  def _saveCache(self):
    for m in interfaces.VALID_MODES:
      manager = factory.Factory.getManager(m)
      self._cacheManager.setData("cache/{}".format(m), manager.cache())  
    self._cacheManager.saveConfig(self._cacheFile)
      
  def _loadSettings(self):
    self._loadSettingsConfig()
    self._loadCache()
    
  def _loadSettingsConfig(self):
    self._config_manager.loadConfig(self._configFile)
  
    try:
      data = self._config_manager.getData("mw", config.MainWindowConfig())
      self.restoreGeometry(QtCore.QByteArray.fromBase64(data.geo))
      self.restoreState(QtCore.QByteArray.fromBase64(data.state))
      dont_show.DontShowManager.setConfig(data.dontShows)
      if not data.mode in interfaces.VALID_MODES:
        data.mode = interfaces.Mode.TV_MODE
      self._setMode(data.mode)
      self._autoStart = data.autoStart
      
      for m in self._modeToModule.values():
        for w in [m.inputWidget, m.outputWidget, m.workBenchWidget]:
          w.setConfig(self._config_manager.getData(w.configName, None))    
    except (ValueError, TypeError, IndexError, KeyError) as e:
      utils.logWarning("Unable to load config file. reason: {}".format(e))
      if not self._restoringDefaults:
        self._restoreDefaults()
      else:
        QtGui.QMessageBox.warning(self, "Config error", "Default config is in a bad state. Fix me!")
          
  def _loadCache(self):
    self._cacheManager.loadConfig(self._cacheFile)
    for m in interfaces.VALID_MODES:
      factory.Factory.getManager(m).setCache(self._cacheManager.getData("cache/{}".format(m), {}))    
  
  def _restoreDefaults(self):
    self._restoringDefaults = True
    file_helper.FileHelper.removeFile(self._configFile)
    self._loadSettingsConfig()
    self._restoringDefaults = False
    
  def _clearCache(self):
    file_helper.FileHelper.removeFile(self._cacheFile)
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
    
    if mode == interfaces.Mode.MOVIE_MODE:
      self.movieRadio.setChecked(True)
    else:
      self.tvRadio.setChecked(True)
  
  def mode(self):
    return interfaces.Mode.MOVIE_MODE if self.movieRadio.isChecked() else interfaces.Mode.TV_MODE
  
  def isAutoStart(self):
    return self.autoStartCheckBox.isChecked()

# --------------------------------------------------------------------------------------------------------------------
class LogWidget(QtGui.QWidget):
  """ Widget to display log messages to the user """
  def __init__(self, parent=None):
    super(LogWidget, self).__init__(parent)
    uic.loadUi("ui/ui_LogWidget.ui", self)
    self.clearButton.clicked.connect(self._clearLog)
    self.clearButton.setIcon(QtGui.QIcon("img/clear.png"))    
    self.clearButton.setEnabled(True)

    self._model = _LogModel(self)
    self.logView.setModel(self._model)
    self.logView.horizontalHeader().setResizeMode(_LogColumns.COL_ACTION, QtGui.QHeaderView.Interactive)
    self.logView.horizontalHeader().resizeSection(_LogColumns.COL_ACTION, 75)
    self.logView.horizontalHeader().setResizeMode(_LogColumns.COL_MESSAGE, QtGui.QHeaderView.Interactive)
    self.logView.horizontalHeader().setStretchLastSection(True)
    
    self._isUpdating = False
    
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
    if role == QtCore.Qt.ForegroundRole and item.logLevel >= utils.LogLevel.ERROR:
      return QtGui.QBrush(QtCore.Qt.red)      
    elif role == _LogModel.LOG_LEVEL_ROLE:
      return item.logLevel
    elif index.column() == _LogColumns.COL_ACTION:
      return item.action
    elif index.column() == _LogColumns.COL_MESSAGE: 
      if role == QtCore.Qt.DisplayRole:
        return item.shortMessage
      else:
        return item.longMessage
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
    utils.log(item.logLevel, msg=item.shortMessage, longMsg=item.longMessage, title=item.action)
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