#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore, QtGui

import inputWidget
import outputWidget
import workBenchWidget

class SeriesRenamerModule(QtCore.QObject):
  def __init__(self, parent=None):
    super(QtCore.QObject, self).__init__(parent)
    
    #input widget
    self.inputWidget_ = inputWidget.InputWidget()
    self.inputWidget_.exploreSignal_.connect(self._onExplore)
    
    #workbench widget
    self.workBenchWidget_ = workBenchWidget.WorkBenchWidget()
    
    #output widget
    self.outputWidget_ = outputWidget.OutputWidget()
    self.outputWidget_.saveSignal_.connect(self._onSave)
    
  def _onExplore(self):
    pass
    
  def _onSave(self):
    pass
