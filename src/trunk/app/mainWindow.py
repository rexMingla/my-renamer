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

    self.ui_ = uic.loadUi("ui/ui_MainWindow.ui", self)
    self.ui_.setCentralWidget(QtGui.QWidget())
    lo = QtGui.QVBoxLayout(self.ui_.centralWidget())
    lo.setMargin(4)
    lo.setSpacing(4)
        
    #widgets
    lo.addWidget(self.seriesModule_.inputWidget_)
    lo.addWidget(self.seriesModule_.workBenchWidget_)
    lo.addWidget(self.seriesModule_.outputWidget_)
    lo.addWidget(self.seriesModule_.progressBar_)
    lo.addWidget(self.seriesModule_.logWidget_)

    #serializer
    self.serializer_ = serializer.Serializer("config.p")
    self.serializer_.addItem("input", self.seriesModule_.inputWidget_.dataItem_)
    self.serializer_.addItem("output", self.seriesModule_.outputWidget_.dataItem_)
    self.serializer_.loadItems()
    
  def closeEvent(self, event):
    self.serializer_.saveItems()
    event.accept()
      
    