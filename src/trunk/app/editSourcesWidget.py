#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Allow the user to edit information sources
# --------------------------------------------------------------------------------------------------------------------
import copy

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

#from common import fileHelper
#from common import thread
from common import utils
#from tv import episode
#from tv import season
#from tv import seasonHelper

# --------------------------------------------------------------------------------------------------------------------
class SourceModel(QtCore.QAbstractTableModel):
  #statuses
  MISSING_LIBRARY = ("Missing Library", "Source could not be loaded") #(status, tooltip)
  MISSING_KEY = ("Missing Key", "Key needs to be set")
  DISABLED = ("Disabled", "Disabled by user")
  ENABLED = ("Enabled", "In use")

  COL_NAME = 0
  COL_STATUS = 1
  NUM_COLS = 2
  RAW_ITEM_ROLE = QtCore.Qt.UserRole + 1
  
  """ SourceItems """
  def __init__(self, store, parent):
    super(QtCore.QAbstractTableModel, self).__init__(parent)
    self._store = store
    self.beginInsertRows(QtCore.QModelIndex(), 0, len(self._store.stores) - 1)
    self.endInsertRows()
      
  def rowCount(self, parent=None):
    return len(self._store.stores)

  def columnCount(self, parent):
    return SourceModel.NUM_COLS
  
  def data(self, index, role):
    if not index.isValid():
      return None
    
    if role not in (SourceModel.RAW_ITEM_ROLE, QtCore.Qt.ForegroundRole, 
                    QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole):
      return None
    
    item = self._store.stores[index.row()]
    if role == SourceModel.RAW_ITEM_ROLE:
      return item
    if role == QtCore.Qt.ForegroundRole and index.column() == SourceModel.COL_STATUS:
      return QtGui.QBrush(QtCore.Qt.green if item.isActive() else QtCore.Qt.red)
    if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:
      if index.column() == SourceModel.COL_NAME:
        return item.prettyName()
      else:
        status = SourceModel.MISSING_LIBRARY
        if item.hasLib:
          if item.isAvailable():
            if item.isActive():
              status = SourceModel.ENABLED
            else:
              status = SourceModel.DISABLED
          else:
            status = SourceModel.MISSING_KEY
        return status[0] if role == QtCore.Qt.DisplayRole else status[1]

  def headerData(self, section, orientation, role):
    if not role in (QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole) or orientation == QtCore.Qt.Vertical:
      return None
    
    if role == QtCore.Qt.DisplayRole:
      return ["Name", "Status"][section]
    if role == QtCore.Qt.ToolTipRole:
      return ["Name of service", "Overall status"][section]
    
  def moveUp(self, index):
    if not index.isValid():
      return    
    row = index.row()
    self._store.stores[row], self._store.stores[row - 1] = self._store.stores[row - 1], self._store.stores[row]
    self.dataChanged.emit(self.index(row - 1, 0), self.index(row, SourceModel.NUM_COLS))
      
  def moveDown(self, index):
    if not index.isValid():
      return    
    row = index.row()
    self._store.stores[row], self._store.stores[row + 1] = self._store.stores[row + 1], self._store.stores[row]
    self.dataChanged.emit(self.index(row, 0), self.index(row + 1, SourceModel.NUM_COLS))
    
  def updateItem(self, index, item):
    #dodge city...
    if not index.isValid():
      return    
    row = index.row()
    self._store.stores[row] = item
    self.dataChanged.emit(self.index(row, 0), self.index(row, SourceModel.NUM_COLS))
          
# --------------------------------------------------------------------------------------------------------------------
class EditSourcesWidget(QtGui.QDialog):
  """
  Allows the user to prioritise the search order for information sources and set keys
  """
  def __init__(self, store, parent=None):
    super(QtGui.QDialog, self).__init__(parent)
    uic.loadUi("ui/ui_EditSources.ui", self)
    self.setWindowModality(True)

    self.keyEdit.textEdited.connect(self._onKeyEdited)
    self.activeCheckBox.clicked.connect(self._onActiveChecked)
    self.upButton.clicked.connect(self._moveUp)
    self.downButton.clicked.connect(self._moveDown)
    self.keyEdit.setPlaceholderText("Enter key here")
    
    self._model = SourceModel(store, self)
    self.sourceView.setModel(self._model)  
    self.sourceView.horizontalHeader().setResizeMode(SourceModel.COL_NAME, QtGui.QHeaderView.Interactive)
    self.sourceView.horizontalHeader().setResizeMode(SourceModel.COL_STATUS, QtGui.QHeaderView.Fixed)
    self.sourceView.horizontalHeader().resizeSection(SourceModel.COL_STATUS, 30)        
    self.sourceView.horizontalHeader().setStretchLastSection(True)    
    self.sourceView.selectionModel().selectionChanged.connect(self._onSelectionChanged)
    self._onSelectionChanged(self.sourceView.selectionModel().selection())
    
  def _onSelectionChanged(self, selection):
    indexes = selection.indexes()
    item  = None
    if not indexes:
      self.upButton.setEnabled(False)
      self.downButton.setEnabled(False)
    else:
      self._currentIndex = indexes[0]
      item = self._model.data(self._currentIndex, SourceModel.RAW_ITEM_ROLE)
      row = self._currentIndex.row()
      self.upButton.setEnabled(row >= 1)
      self.downButton.setEnabled((row + 1) < self._model.rowCount())
    self._setCurrentItem(item)
    
  def _moveDown(self):
    self._model.moveDown(self._currentIndex)
    self.sourceView.selectRow(self._currentIndex.row() + 1)
    
  def _moveUp(self):
    self._model.moveUp(self._currentIndex)
    self.sourceView.selectRow(self._currentIndex.row() - 1)

  def _setCurrentItem(self, item):
    self.detailsGroupBox.setEnabled(bool(item))
    self.loadCheckBox.setChecked(bool(item) and item.hasLib)  
    self.keyGroupBox.setVisible(bool(item) and item.requiresKey)
    if self.keyGroupBox.isVisible():
      keyLabel = "No key required"
      if item.requiresKey:
        """keyLabel = ("<html><body>Enter the key for <a href='{0}'>{0}</a><br/><br/>"
                    "If you need to get one go to:<br/>"
                     "<a href='{1}'>{1}</a>.</body></html>").format(item.sourceName, item.url)"""     
        keyLabel = ("<html><body>Enter the key for <a href='{0}'>{0}</a></body></html>").format(item.sourceName, item.url)      
      self.keyEdit.setText(item.key)
      self.keyLabel.setText(keyLabel)
    self.activeCheckBox.setEnabled(bool(item) and item.isAvailable())
    self.activeCheckBox.setChecked(bool(item) and item.isEnabled)
    
  def _onKeyEdited(self, text):
    item = self._model.data(self._currentIndex, SourceModel.RAW_ITEM_ROLE)
    item.key = str(text)
    self.activeCheckBox.setEnabled(item.isAvailable())
    self._model.updateItem(self._currentIndex, item)
  
  def _onActiveChecked(self):
    item = self._model.data(self._currentIndex, SourceModel.RAW_ITEM_ROLE)
    item.isEnabled = self.activeCheckBox.isChecked()
    self._model.updateItem(self._currentIndex, item)