#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: MainWindow for the application
# --------------------------------------------------------------------------------------------------------------------
import os

from PyQt4 import QtGui, QtCore, uic

from common import utils

import inputWidget
import logWidget
import outputWidget
import renamerModule
import seriesRenamerModule
import movieRenamerModule
import workBenchWidget

import jsonpickle
jsonpickle.set_encoder_options("simplejson", indent=2)

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
    self._workBenchWidget.movieButton.setVisible(False)
    self._workBenchWidget.tvButton.setVisible(False)

    uiPath = os.path.join(os.path.dirname(__file__), "../ui/ui_MainWindow.ui")
    self._ui = uic.loadUi(uiPath, self)
    self._ui.setCentralWidget(self._workBenchWidget)
            
    #widgets
    dockAreas = QtCore.Qt.AllDockWidgetAreas
    self._addDockWidget(self._inputWidget, dockAreas, QtCore.Qt.TopDockWidgetArea, "Input Settings")
    self._addDockWidget(self._outputWidget, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Output Settings")
    self._addDockWidget(self._logWidget, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Message Log")
    
    #serializer
    self._configItems = {"log" : self._logWidget,
                        "tv" : self._seriesModule,
                        "movie" : self._movieModule,
                        "mainWindow" : self}
    self._mode = None
    self._modeToModule = {self._seriesModule.mode : self._seriesModule, 
                          self._movieModule.mode : self._movieModule}
    self.loadConfig()
    
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
    self._ui.addDockWidget(defaultArea, dock)
    return dock
  
  def _setMovieMode(self):
    self._setMode(renamerModule.Mode.MOVIE_MODE)
  
  def _setTvMode(self):
    self._setMode(renamerModule.Mode.TV_MODE)

  def _setMode(self, mode):
    assert(mode in renamerModule.VALID_MODES)
    if self._mode:
      self._modeToModule[self._mode].setInactive()
    self._mode = mode
    self._modeToModule[self._mode].setActive()
    self.setWindowTitle("Tv and Movie ReNamer [%s mode]" % self._mode)
  
  def getConfig(self):
    data = {"geometry" : utils.toString(self._ui.saveGeometry().toBase64()), 
            "windowState" : utils.toString(self._ui.saveState().toBase64()),
            "mode" : self._mode}  
    return data
    
  def setConfig(self, data):
    x = data.get("geometry", "")
    geo = QtCore.QByteArray.fromBase64(data.get("geometry", "AdnQywABAAAAAACWAAAAlgAAA6sAAAKmAAAAngAAALQAAAOjAAACngAAAAAAAA=="))
    state = QtCore.QByteArray.fromBase64(data.get("windowState", "AAAA/wAAAAD9AAAAAgAAAAIAAAMGAAAAafwBAAAAAfsAAAAcAEkAbgBwAHUAdAAgAFMAZQB0AHQAaQBuAGcAcwEAAAAAAAADBgAAAOQA////AAAAAwAAAwYAAADa/AEAAAAC+wAAAB4ATwB1AHQAcAB1AHQAIABTAGUAdAB0AGkAbgBnAHMBAAAAAAAAAdwAAAFIAP////sAAAAWAE0AZQBzAHMAYQBnAGUAIABMAG8AZwEAAAHcAAABKgAAAMkA////AAADBgAAAKAAAAAEAAAABAAAAAgAAAAI/AAAAAA="))
    self._ui.restoreGeometry(geo)
    self._ui.restoreState(state)
    mode = data.get("mode")
    if not mode in renamerModule.VALID_MODES:
      mode = renamerModule.Mode.TV_MODE
    self._setMode(mode)
  
  def loadConfig(self):
    obj = None
    if os.path.exists(self._configFile):
      f = open(self._configFile, "r")
      obj = jsonpickle.decode(f.read())
    if not isinstance(obj, dict):
      obj = {}
    for key, item in self._configItems.items():
      item.setConfig(obj.get(key, {}))
    #set the mode at the end
    self._setMode(self._mode)
  
  def saveConfig(self):
    data = {}
    for key, item in self._configItems.items():
      data[key] = item.getConfig()
    f = open(self._configFile, "w")
    f.write(jsonpickle.encode(data))
    f.close()
    
  
    