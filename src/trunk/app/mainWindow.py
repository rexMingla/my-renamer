#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: MainWindow for the application
# --------------------------------------------------------------------------------------------------------------------
import os

from PyQt4 import QtGui, QtCore, uic
import jsonpickle
jsonpickle.set_encoder_options("simplejson", indent=2)

from common import utils

import seriesRenamerModule

# --------------------------------------------------------------------------------------------------------------------
class MainWindow(QtGui.QMainWindow):
  """ Window widget for the application. """
  def __init__(self, configFile="config.txt", parent = None):
    super(QtGui.QMainWindow, self).__init__(parent)
    self.configFile = configFile
    self.seriesModule_ = seriesRenamerModule.SeriesRenamerModule(self)

    self._ui_ = uic.loadUi("ui/ui_MainWindow.ui", self)
    self._ui_.setCentralWidget(self.seriesModule_.workBenchWidget_)
        
    #widgets
    dockAreas = QtCore.Qt.AllDockWidgetAreas
    self._addDockWidget(self.seriesModule_.inputWidget_, dockAreas, QtCore.Qt.TopDockWidgetArea, "Input Settings")
    self._addDockWidget(self.seriesModule_.outputWidget_, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Output Settings")
    self._addDockWidget(self.seriesModule_.logWidget_, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Message Log")
    
    self.isShuttingDown_ = False
    
    #serializer
    self.configItems = {"input" : self.seriesModule_.inputWidget_,
                        "output" : self.seriesModule_.outputWidget_,
                        "log" : self.seriesModule_.logWidget_,
                        "workBench" : self.seriesModule_.workBenchWidget_,
                        "mainWindow" : self}
    self.loadConfig()
    
  def closeEvent(self, event):
    self.isShuttingDown_ = True
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
    self._ui_.addDockWidget(defaultArea, dock)
    return dock
  
  def getConfig(self):
    data = {"geometry" : utils.toString(self._ui_.saveGeometry().toBase64()), 
            "windowState" : utils.toString(self._ui_.saveState().toBase64())}  
    return data
    
  def setConfig(self, data):
    x = data.get("geometry", "")
    geo = QtCore.QByteArray.fromBase64(data.get("geometry", "AdnQywABAAAAAACWAAAAlgAAA6sAAAKmAAAAngAAALQAAAOjAAACngAAAAAAAA=="))
    state = QtCore.QByteArray.fromBase64(data.get("windowState", "AAAA/wAAAAD9AAAAAgAAAAIAAAMGAAAAafwBAAAAAfsAAAAcAEkAbgBwAHUAdAAgAFMAZQB0AHQAaQBuAGcAcwEAAAAAAAADBgAAAOQA////AAAAAwAAAwYAAADa/AEAAAAC+wAAAB4ATwB1AHQAcAB1AHQAIABTAGUAdAB0AGkAbgBnAHMBAAAAAAAAAdwAAAFIAP////sAAAAWAE0AZQBzAHMAYQBnAGUAIABMAG8AZwEAAAHcAAABKgAAAMkA////AAADBgAAAKAAAAAEAAAABAAAAAgAAAAI/AAAAAA="))
    self._ui_.restoreGeometry(geo)
    self._ui_.restoreState(state)
      
  def loadConfig(self):
    obj = None
    if os.path.exists(self.configFile):
      f = open(self.configFile, "r")
      obj = jsonpickle.decode(f.read())
    if not isinstance(obj, dict):
      obj = {}
    for key, widget in self.configItems.items():
      widget.setConfig(obj.get(key, {}))
  
  def saveConfig(self):
    data = {}
    for key, widget in self.configItems.items():
      data[key] = widget.getConfig()
    f = open(self.configFile, "w")
    f.write(jsonpickle.encode(data))
    f.close()
    