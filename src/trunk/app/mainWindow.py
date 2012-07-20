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

import seriesRenamerModule
import movieRenamerModule
import inputWidget
import logWidget
import outputWidget
import workBenchWidget
import interfaces

# --------------------------------------------------------------------------------------------------------------------
class MainWindow(QtGui.QMainWindow):
  """ Window widget for the application. """
  def __init__(self, _configFile="config.txt", parent = None):
    super(QtGui.QMainWindow, self).__init__(parent)
    self._configFile = _configFile
    
    self._inputWidget = inputWidget.InputWidget(parent)
    self._workBenchWidget = workBenchWidget.WorkBenchWidget(parent)
    self._outputWidget = outputWidget.OutputWidget(parent)
    self._logWidget = logWidget.LogWidget(parent)
    self._workBenchWidget.workBenchChangedSignal.connect(self._outputWidget.renameButton.setEnabled)     
    
    self._seriesModule = seriesRenamerModule.SeriesRenamerModule(self._inputWidget, 
                                                                self._outputWidget,
                                                                self._workBenchWidget, 
                                                                self._logWidget,
                                                                self)
    self._movieModule = movieRenamerModule.MovieRenamerModule(self._inputWidget, 
                                                                self._outputWidget,
                                                                self._workBenchWidget, 
                                                                self._logWidget,
                                                                self)
    self._workBenchWidget.movieButton.clicked.connect(self._setMovieMode)
    self._workBenchWidget.tvButton.clicked.connect(self._setTvMode)

    uic.loadUi("ui/ui_MainWindow.ui", self)
    self.setCentralWidget(self._workBenchWidget)
            
    #widgets
    dockAreas = QtCore.Qt.AllDockWidgetAreas
    self._addDockWidget(self._inputWidget, dockAreas, QtCore.Qt.TopDockWidgetArea, "Input Settings")
    self._addDockWidget(self._outputWidget, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Output Settings")
    self._addDockWidget(self._logWidget, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Message Log")
    
    self._mode = None
    self._modeToModule = {self._seriesModule.mode : self._seriesModule, 
                          self._movieModule.mode : self._movieModule}
    config.ConfigManager.loadConfig(self._configFile)
    self.setConfig()
    
  def closeEvent(self, event):
    self.getConfig()
    if self._mode:
      self._modeToModule[self._mode].setInactive() #force save of data 
    config.ConfigManager.saveConfig(self._configFile)
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
    self._modeToModule[self._mode].setActive()
    self.setWindowTitle("Tv and Movie ReNamer [%s mode]" % self._mode)
  
  def getConfig(self):
    config.ConfigManager.setData("mw/geometry", utils.toString(self.saveGeometry().toBase64()))
    config.ConfigManager.setData("mw/windowState", utils.toString(self.saveState().toBase64()))
    config.ConfigManager.setData("mw/mode", self._mode)
    
  def setConfig(self):
    geo = config.ConfigManager.getData("mw/geometry", "AdnQywABAAAAAACWAAAAlgAAA6sAAAKmAAAAngAAALQAAAOjAAACngAAAAAAAA==")
    state = config.ConfigManager.getData("mw/windowState", "AAAA/wAAAAD9AAAAAgAAAAIAAAMGAAAAafwBAAAAAfsAAAAcAEkAbgBwAHUAdAAgAFMAZQB0AHQAaQBuAGcAcwEAAAAAAAADBgAAAOQA////AAAAAwAAAwYAAADa/AEAAAAC+wAAAB4ATwB1AHQAcAB1AHQAIABTAGUAdAB0AGkAbgBnAHMBAAAAAAAAAdwAAAFIAP////sAAAAWAE0AZQBzAHMAYQBnAGUAIABMAG8AZwEAAAHcAAABKgAAAMkA////AAADBgAAAKAAAAAEAAAABAAAAAgAAAAI/AAAAAA=")
    self.restoreGeometry(QtCore.QByteArray.fromBase64(geo))
    self.restoreState(QtCore.QByteArray.fromBase64(state))
    mode = config.ConfigManager.getData("mw/mode")
    if not mode in interfaces.VALID_MODES:
      mode = interfaces.Mode.TV_MODE
    self._setMode(mode)
  

    
  
    