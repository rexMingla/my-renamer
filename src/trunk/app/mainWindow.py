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

from common import utils

import config
import logWidget
import interfaces
import renamerModule

# --------------------------------------------------------------------------------------------------------------------
class MainWindow(QtGui.QMainWindow):
  """ Window widget for the application. """
  def __init__(self, _configFile="config.txt", logFile="log.txt", parent = None):
    super(QtGui.QMainWindow, self).__init__(parent)
    self._configFile = _configFile
    
    utils.initLogging(logFile)
    utils.logInfo("Starting app")    
    
    uic.loadUi("ui/ui_MainWindow.ui", self)        
    self._inputStackWidget = QtGui.QStackedWidget(parent)
    self._workBenchStackWidget = QtGui.QStackedWidget(parent)
    self._outputStackWidget = QtGui.QStackedWidget(parent)
    self._logWidget = logWidget.LogWidget(parent)
    self.setCentralWidget(self._workBenchStackWidget)
                
    #dock widgets
    dockAreas = QtCore.Qt.AllDockWidgetAreas
    self._addDockWidget(self._inputStackWidget, dockAreas, QtCore.Qt.TopDockWidgetArea, "Input Settings")
    self._addDockWidget(self._outputStackWidget, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Output Settings")
    self._addDockWidget(self._logWidget, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Message Log")
    
    self._modeToModule = {}
    self._addModule(renamerModule.ModuleFactory.createModule(interfaces.Mode.MOVIE_MODE, self))
    self._addModule(renamerModule.ModuleFactory.createModule(interfaces.Mode.TV_MODE, self))
    self._mode = None
    
    self.loadConfig()
    
  def _addModule(self, module):
    self._modeToModule[module.mode] = module
    self._inputStackWidget.addWidget(module.inputWidget)
    self._workBenchStackWidget.addWidget(module.workBenchWidget)
    self._outputStackWidget.addWidget(module.outputWidget) 
    module.workBenchWidget.modeChangedSignal.connect(self._setMode)    
    module.logSignal.connect(self._logWidget.appendMessage)
    
  def closeEvent(self, event):
    self.saveConfig()
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
    
    if self._mode:
      self._modeToModule[self._mode].setInactive()
    
    self._mode = mode
    module = self._modeToModule[self._mode]
    self._inputStackWidget.setCurrentWidget(module.inputWidget)
    self._workBenchStackWidget.setCurrentWidget(module.workBenchWidget)
    self._outputStackWidget.setCurrentWidget(module.outputWidget)
    module.setActive()
    self.setWindowTitle("Tv and Movie ReNamer [{} mode]".format(self._mode))
  
  def saveConfig(self):
    config.ConfigManager.setData("mw/geometry", utils.toString(self.saveGeometry().toBase64()))
    config.ConfigManager.setData("mw/windowState", utils.toString(self.saveState().toBase64()))
    config.ConfigManager.setData("mw/mode", self._mode)
    
    for m in self._modeToModule.values():
      for w in [m.inputWidget, m.outputWidget, m.workBenchWidget]:
        config.ConfigManager.setData(w.configName, w.getConfig())
    config.ConfigManager.saveConfig(self._configFile)
    
  def loadConfig(self):
    config.ConfigManager.loadConfig(self._configFile)
    
    geo = config.ConfigManager.getData("mw/geometry", "AdnQywABAAAAAACWAAAAlgAAA6sAAAKmAAAAngAAALQAAAOjAAACngAAAAAAAA==")
    state = config.ConfigManager.getData("mw/windowState", "AAAA/wAAAAD9AAAAAgAAAAIAAAMGAAAAafwBAAAAAfsAAAAcAEkAbgBwAHUAdAAgAFMAZQB0AHQAaQBuAGcAcwEAAAAAAAADBgAAAOQA////AAAAAwAAAwYAAADa/AEAAAAC+wAAAB4ATwB1AHQAcAB1AHQAIABTAGUAdAB0AGkAbgBnAHMBAAAAAAAAAdwAAAFIAP////sAAAAWAE0AZQBzAHMAYQBnAGUAIABMAG8AZwEAAAHcAAABKgAAAMkA////AAADBgAAAKAAAAAEAAAABAAAAAgAAAAI/AAAAAA=")
    self.restoreGeometry(QtCore.QByteArray.fromBase64(geo))
    self.restoreState(QtCore.QByteArray.fromBase64(state))
    mode = config.ConfigManager.getData("mw/mode")
    if not mode in interfaces.VALID_MODES:
      mode = interfaces.Mode.TV_MODE
    self._setMode(mode)
    
    for m in self._modeToModule.values():
      for w in [m.inputWidget, m.outputWidget, m.workBenchWidget]:
        w.setConfig(config.ConfigManager.getData(w.configName, {}))    
  

    
  
    