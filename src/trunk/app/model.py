#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

class SeriesRenamerModel(QtCore.QAbstractTableModel):
  """ """
  def __init__(self, parent=None):
    super(QtCore.QAbstractTableModel, self).__init__(parent)
  
  def rowCount(self, parent=QtCore.QModelIndex()):
    return 0
  
  def columnCount(self, parent=QtCore.QModelIndex()):
    return 0
  
  def data(self, index, role):
    return None