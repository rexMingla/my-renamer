#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Allows user to select from a list of a results 
# --------------------------------------------------------------------------------------------------------------------
import copy

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from common import fileHelper
from common import outputFormat
from common import utils
from tv import episode
from tv import moveItemCandidate
from tv import season

# --------------------------------------------------------------------------------------------------------------------
class _ResultHolder:
  def __init__(self, obj, source):
    self.obj = obj
    self.source = source
    
  def __str__(self):
    return "{} ({})".format(str(self.obj), self.source)

# --------------------------------------------------------------------------------------------------------------------
class SearchResultsWidget(QtGui.QDialog):
  itemSelectedSignal = QtCore.pyqtSignal(object)
  
  def __init__(self, parent=None):
    super(QtGui.QDialog, self).__init__(parent)
    uic.loadUi("ui/ui_SearchResults.ui", self)
    self._items = []
    self.resultsWidget.itemSelectionChanged.connect(self._onItemClicked)
    
  def clear(self):
    self._items = []
    self.resultsWidget.clearContents()
    self.resultsWidget.setRowCount(0)
    
  def addItem(self, obj, source):
    self._items.append(_ResultHolder(obj, source))
    rc = self.resultsWidget.rowCount()
    self.resultsWidget.insertRow(rc)
    
    w = QtGui.QTableWidgetItem(str(obj))
    w.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
    self.resultsWidget.setItem(rc, 0, w)
    
    w = QtGui.QTableWidgetItem(source)
    w.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
    self.resultsWidget.setItem(rc, 1, w)
    
  def _onItemClicked(self):
    if self.resultsWidget.selectedItems():
      row = self.resultsWidget.selectedItems()[0].row()
      holder = self._items[row]
      self.itemSelectedSignal.emit(holder.obj)
  
  