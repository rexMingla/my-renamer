#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: MainWindow for the application
# --------------------------------------------------------------------------------------------------------------------
import os

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import uic

from common import fileHelper
from common import utils

import config
import factory
import logWidget
import interfaces
import welcomeWidget

import app

# --------------------------------------------------------------------------------------------------------------------
class MainWindow(QtGui.QMainWindow):
  """ Window widget for the application. """
  def __init__(self, configFile="config.txt", cacheFile="cache.txt", logFile="log.txt", parent = None):
    super(QtGui.QMainWindow, self).__init__(parent)
    self._configFile = configFile
    self._cacheFile = cacheFile
    
    utils.initLogging(logFile)
    utils.logInfo("Starting app")    
    
    uic.loadUi("ui/ui_MainWindow.ui", self)
    
    self._inputStackWidget = QtGui.QStackedWidget(parent)
    self._workBenchStackWidget = QtGui.QStackedWidget(parent)
    self._outputStackWidget = QtGui.QStackedWidget(parent)
    self._logWidget = logWidget.LogWidget(parent)
    self.setCentralWidget(self._workBenchStackWidget)
    
    #menu actions
    self.actionMovieMode.triggered.connect(self._setMovieMode)
    self.actionTvMode.triggered.connect(self._setTvMode)
    self.actionExit.triggered.connect(self.close)
    self.actionAbout.triggered.connect(self._showAbout)
    self.actionSave.triggered.connect(self._saveSettings)
    self.actionRestoreDefaults.triggered.connect(self._restoreDefaults)
    self.actionClearCache.triggered.connect(self._clearCache)
    self._modeToAction = {interfaces.Mode.MOVIE_MODE : self.actionMovieMode, interfaces.Mode.TV_MODE: self.actionTvMode}
                
    #dock widgets
    dockAreas = QtCore.Qt.AllDockWidgetAreas
    self._addDockWidget(self._inputStackWidget, dockAreas, QtCore.Qt.TopDockWidgetArea, "Input Settings")
    self._addDockWidget(self._outputStackWidget, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Output Settings")
    self._addDockWidget(self._logWidget, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Message Log")
    
    self._configManager = config.ConfigManager()
    self._cacheManager = config.ConfigManager()
    
    self._modeToModule = {}
    for mode in interfaces.VALID_MODES:
      self._addModule(factory.Factory.getRenamerModule(mode, self))
    self._mode = None
    self._autoStart = False
    
    self._loadSettings()
    
  def _showAbout(self):
    def getText(mode):
      info = []
      holder = factory.Factory.getStoreHolder(mode)
      for s in holder.stores:
        info.append("<li>{0} <a href=\"{1}\">{1}</a> "
                    "(interface to <a href=\"{2}\">{2}</a>)</li>".format(s.displayName, s.url, s.sourceName))
      info.append("</ul>")
      return "{} libraries:<ul>{}</ul>".format(mode, "\n".join(info))
    
    text = []
    for mode in interfaces.VALID_MODES:
      text.append(getText(mode))
    
    msg = ("<html><p>MyRenamer {} is written in python with PyQt.<p/>\n\n"
          "<p>Special thanks to the following libraries:</p>\n\n{}</html>").format(app.__VERSION__, "\n\n".join(text))
    QtGui.QMessageBox.about(self, "About MyRenamer", msg)
    
  def _addModule(self, module):
    self._modeToModule[module.mode] = module
    self._inputStackWidget.addWidget(module.inputWidget)
    self._workBenchStackWidget.addWidget(module.workBenchWidget)
    self._outputStackWidget.addWidget(module.outputWidget) 
    #module.workBenchWidget.modeChangedSignal.connect(self._setMode)    
    module.logSignal.connect(self._logWidget.appendMessage)
    
  def showEvent(self, event):
    super(MainWindow, self).showEvent(event)
    if not self._autoStart:
      ww = welcomeWidget.WelcomeWidget(self._mode, self)
      ww.exec_()
      self._setMode(ww.mode())
      self._autoStart = ww.isAutoStart()
    event.accept()
    
  def closeEvent(self, event):
    module = self._modeToModule[self._mode]
    if module.outputWidget.isExecuting():
      response = QtGui.QMessageBox.warning(self, "You have unfinished renames", 
                                           "Do you want to keep your pending renames?", 
                                           QtGui.QMessageBox.Discard, QtGui.QMessageBox.Cancel)
      if response == QtGui.QMessageBox.Cancel:
        event.ignore()
        return
    self._saveSettings()
    event.accept()
    
  def _addDockWidget(self, widget, areas, defaultArea, name):
    utils.verifyType(widget, QtGui.QWidget)
    utils.verifyType(areas, int)
    utils.verifyType(defaultArea, int)
    utils.verifyType(name, str)
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
    module = self._modeToModule[self._mode]
    self._inputStackWidget.setCurrentWidget(module.inputWidget)
    self._workBenchStackWidget.setCurrentWidget(module.workBenchWidget)
    self._outputStackWidget.setCurrentWidget(module.outputWidget)
    module.setActive()
    self.setWindowTitle("MyRenamer {} [{} mode]".format(app.__VERSION__, self._mode))
  
  def _saveSettings(self):
    self._saveSettingsConfig()
    self._saveCache()
  
  def _saveSettingsConfig(self):
    self._configManager.setData("mw/geometry", utils.toString(self.saveGeometry().toBase64()))
    self._configManager.setData("mw/windowState", utils.toString(self.saveState().toBase64()))
    self._configManager.setData("mw/mode", self._mode)
    self._configManager.setData("mw/autoStart", self._autoStart)
    
    for m in self._modeToModule.values():
      for w in [m.inputWidget, m.outputWidget, m.workBenchWidget]:
        self._configManager.setData(w.configName, w.getConfig())
    self._configManager.saveConfig(self._configFile)
    
  def _saveCache(self):
    for m in interfaces.VALID_MODES:
      manager = factory.Factory.getManager(m)
      self._cacheManager.setData("cache/{}".format(m), manager.cache())  
    self._cacheManager.saveConfig(self._cacheFile)
      
  def _loadSettings(self):
    self._loadSettingsConfig()
    self._loadCache()
    
  def _loadSettingsConfig(self):
    self._configManager.loadConfig(self._configFile)
    
    geo = self._configManager.getData("mw/geometry", "AdnQywABAAAAAACWAAAAlgAAA6sAAAKmAAAAngAAALQAAAOjAAACngAAAAAAAA==")
    state = self._configManager.getData("mw/windowState", "AAAA/wAAAAD9AAAAAgAAAAIAAAMGAAAAafwBAAAAAfsAAAAcAEkAbgBwAHUAdAAgAFMAZQB0AHQAaQBuAGcAcwEAAAAAAAADBgAAAOQA////AAAAAwAAAwYAAADa/AEAAAAC+wAAAB4ATwB1AHQAcAB1AHQAIABTAGUAdAB0AGkAbgBnAHMBAAAAAAAAAdwAAAFIAP////sAAAAWAE0AZQBzAHMAYQBnAGUAIABMAG8AZwEAAAHcAAABKgAAAMkA////AAADBgAAAKAAAAAEAAAABAAAAAgAAAAI/AAAAAA=")
    self.restoreGeometry(QtCore.QByteArray.fromBase64(geo))
    self.restoreState(QtCore.QByteArray.fromBase64(state))
    mode = self._configManager.getData("mw/mode")
    if not mode in interfaces.VALID_MODES:
      mode = interfaces.Mode.TV_MODE
    self._setMode(mode)
    self._autoStart = bool(self._configManager.getData("mw/autoStart", False))
    
    for m in self._modeToModule.values():
      for w in [m.inputWidget, m.outputWidget, m.workBenchWidget]:
        w.setConfig(self._configManager.getData(w.configName, {}))    
          
  def _loadCache(self):
    self._cacheManager.loadConfig(self._cacheFile)
    for m in interfaces.VALID_MODES:
      factory.Factory.getManager(m).setCache(self._cacheManager.getData("cache/{}".format(m), {}))    
  
  def _restoreDefaults(self):
    fileHelper.FileHelper.removeFile(self._configFile)
    self._loadSettingsConfig()
    
  def _clearCache(self):
    fileHelper.FileHelper.removeFile(self._cacheFile)
    self._loadCache()
    
    
    
  
    