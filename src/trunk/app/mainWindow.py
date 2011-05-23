#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: MainWindow for the application
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui, QtCore, uic

from common import serializer, utils

import seriesRenamerModule

# --------------------------------------------------------------------------------------------------------------------
class MainWindow(QtGui.QMainWindow):
  """ Window widget for the application. """
  def __init__(self, parent = None):
    super(QtGui.QMainWindow, self).__init__(parent)

    self.seriesModule_ = seriesRenamerModule.SeriesRenamerModule(self)

    self._ui_ = uic.loadUi("ui/ui_MainWindow.ui", self)
    self._ui_.setCentralWidget(self.seriesModule_.workBenchWidget_)
        
    #widgets
    dockAreas = QtCore.Qt.AllDockWidgetAreas
    self._addDockWidget(self.seriesModule_.inputWidget_, dockAreas, QtCore.Qt.TopDockWidgetArea, "Input Settings")
    self._addDockWidget(self.seriesModule_.outputWidget_, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Output Settings")
    self._addDockWidget(self.seriesModule_.logWidget_, dockAreas, QtCore.Qt.BottomDockWidgetArea, "Message Log")
    
    self.mainWindowDataItem_ = serializer.DataItem({"geometry":self._ui_.saveGeometry(), \
                                                    "windowState":self._ui_.saveState()})
    self.mainWindowDataItem_.onChangedSignal_.connect(self._mainWindowSettingsChanged)
    self.isShuttingDown_ = False
    
    #serializer
    self.serializer_ = serializer.Serializer("config.p")
    self.serializer_.addItem("input", self.seriesModule_.inputWidget_.dataItem_)
    self.serializer_.addItem("output", self.seriesModule_.outputWidget_.dataItem_)
    self.serializer_.addItem("log", self.seriesModule_.logWidget_.dataItem_)
    self.serializer_.addItem("mainWindow", self.mainWindowDataItem_)
    self.serializer_.loadItems()
    
  def closeEvent(self, event):
    self.isShuttingDown_ = True
    self.mainWindowDataItem_.setData({"geometry":self._ui_.saveGeometry(), \
                                      "windowState":self._ui_.saveState()})
    self.serializer_.saveItems()
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
    
  def _mainWindowSettingsChanged(self):
    if not self.isShuttingDown_:
      geo = self.mainWindowDataItem_.data_["geometry"]
      state = self.mainWindowDataItem_.data_["windowState"]
      self._ui_.restoreGeometry(geo)
      self._ui_.restoreState(state)      
    