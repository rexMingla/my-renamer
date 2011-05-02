#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: MainWindow for the application
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui, QtCore, uic

import serializer
import seriesRenamerModule

# --------------------------------------------------------------------------------------------------------------------
class MainWindow(QtGui.QMainWindow):
  """ """
  def __init__(self, parent = None):
    super(QtGui.QMainWindow, self).__init__(parent)

    self.seriesModule_ = seriesRenamerModule.SeriesRenamerModule(self)

    self._ui_ = uic.loadUi("ui/ui_MainWindow.ui", self)
    self._ui_.setCentralWidget(QtGui.QWidget())
    lo = QtGui.QVBoxLayout(self._ui_.centralWidget())
    lo.setMargin(4)
    lo.setSpacing(4)
        
    #widgets
    lo.addWidget(self.seriesModule_.inputWidget_)
    lo.addWidget(self.seriesModule_.workBenchWidget_)
    lo.addWidget(self.seriesModule_.outputWidget_)
    lo.addWidget(self.seriesModule_.progressBar_)
    lo.addWidget(self.seriesModule_.logWidget_)
    
    self.mainWindowDataItem_ = serializer.DataItem({"geometry":self._ui_.saveGeometry(), \
                                                    "windowState":self._ui_.saveState()})
    self.mainWindowDataItem_.onChangedSignal_.connect(self._mainWindowSettingsChanged)
    self.isShuttingDown_ = False
    
    #serializer
    self.serializer_ = serializer.Serializer("config.p")
    self.serializer_.addItem("input", self.seriesModule_.inputWidget_.dataItem_)
    self.serializer_.addItem("output", self.seriesModule_.outputWidget_.dataItem_)
    self.serializer_.addItem("mainWindow", self.mainWindowDataItem_)
    self.serializer_.loadItems()
    
  def _mainWindowSettingsChanged(self):
    if not self.isShuttingDown_:
      geo = self.mainWindowDataItem_.data_["geometry"]
      state = self.mainWindowDataItem_.data_["windowState"]
      self._ui_.restoreGeometry(geo)
      self._ui_.restoreState(state)
    
  def closeEvent(self, event):
    self.isShuttingDown_ = True
    self.mainWindowDataItem_.setData({"geometry":self._ui_.saveGeometry(), \
                                      "windowState":self._ui_.saveState()})
    self.serializer_.saveItems()
    event.accept()
      
    