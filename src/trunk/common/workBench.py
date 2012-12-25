#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic
from send2trash import send2trash

from common import utils

import interfaces

# --------------------------------------------------------------------------------------------------------------------
class BaseWorkBenchModel(object):
  ACTION_DELETE = "Delete"
  ACTION_LAUNCH = "Open location"
  ACTION_OPEN = "Open file"
  ACTION_EPISODE = "Edit episode"
  ACTION_SEASON = "Edit season"
  ACTION_MOVIE = "Edit movie"
  
  ALL_ACTIONS = ()
  
  def __init__(self):
    super(BaseWorkBenchModel, self).__init__()
    
  def getFile(self, index):
    raise NotImplementedError("BaseWorkBenchModel.fileLocation not implemented")
  
  def getFolder(self, index):
    raise NotImplementedError("BaseWorkBenchModel.folder not implemented")
  
  def getDeleteItem(self, index):
    raise NotImplementedError("BaseWorkBenchModel.getDeleteItem not implemented")
  
  def getAvailableActions(self, index):
    raise NotImplementedError("BaseWorkBenchModel.getAvailableActions not implemented")  
   
  @staticmethod 
  def getDefaultAvailableActions():    
    ret = { BaseWorkBenchModel.ACTION_DELETE: False,
            BaseWorkBenchModel.ACTION_LAUNCH: False,
            BaseWorkBenchModel.ACTION_OPEN: False,
            BaseWorkBenchModel.ACTION_EPISODE: False,
            BaseWorkBenchModel.ACTION_SEASON: False,
            BaseWorkBenchModel.ACTION_MOVIE: False} 
    return ret
      
# --------------------------------------------------------------------------------------------------------------------
class BaseWorkBenchWidget(interfaces.LoadWidgetInterface):
  workBenchChangedSignal = QtCore.pyqtSignal(bool)
  showEditSourcesSignal = QtCore.pyqtSignal()
  
  def __init__(self, mode, manager, parent=None):
    super(BaseWorkBenchWidget, self).__init__("workBench/{}".format(mode), parent)
    uic.loadUi("ui/ui_WorkBench.ui", self)
    self._model = None
    self._manager = manager
    self.selectAllCheckBox.clicked.connect(self._setOverallCheckedState)
    self.launchButton.clicked.connect(self._launch)
    self.openButton.clicked.connect(self._open)    
    self.deleteButton.clicked.connect(self._delete)
    self.editEpisodeButton.clicked.connect(self._editEpisode)
    self.editSeasonButton.clicked.connect(self._editSeason)
    self.editMovieButton.clicked.connect(self._editMovie)    
    self._actionToButton = {BaseWorkBenchModel.ACTION_DELETE: self.deleteButton,
                            BaseWorkBenchModel.ACTION_LAUNCH: self.launchButton,
                            BaseWorkBenchModel.ACTION_OPEN: self.openButton,
                            BaseWorkBenchModel.ACTION_EPISODE: self.editEpisodeButton,
                            BaseWorkBenchModel.ACTION_SEASON: self.editSeasonButton,
                            BaseWorkBenchModel.ACTION_MOVIE: self.editMovieButton}
    
  def _editEpisode(self):
    raise NotImplementedError("BaseWorkBenchWidget.editEpisode not implemented")
    
  def _editSeason(self):
    raise NotImplementedError("BaseWorkBenchWidget.editEpisode not implemented")
    
  def _editMovie(self):
    raise NotImplementedError("BaseWorkBenchWidget.editEpisode not implemented")
    
  def _setModel(self, m):
    self._model = m
    self._model.workBenchChangedSignal.connect(self._onWorkBenchChanged)
    self._onWorkBenchChanged(False)
    self._model.beginUpdateSignal.connect(self.startWorkBenching)
    self._model.endUpdateSignal.connect(self.stopWorkBenching)
    for action, button in self._actionToButton.items():
      button.setVisible(action in self._model.ALL_ACTIONS)
    
  def _launchLocation(self, location):
    path = QtCore.QDir.toNativeSeparators(location)
    if not QtGui.QDesktopServices.openUrl(QtCore.QUrl("file:///{}".format(path))):
      QtGui.QMessageBox.information(self, "An error occured", 
                                    "Could not find path:\n{}".format(path))
    
  def _launch(self):
    f = self._model.getFile(self._currentIndex)
    if f:
      self._launchLocation(f)
  
  def _open(self):
    f = self._model.getFolder(self._currentIndex)
    if f:
      self._launchLocation(f)
      
  def _enable(self):
    self.setEnabled(True)
        
  def _disable(self):
    self.setEnabled(False)
    
  def startWorkBenching(self):
    self._disable()
        
  def stopWorkBenching(self):
    self._enable()
        
  def startExploring(self):
    self._model.clear()
    self._disable()
    self._model.beginUpdate()
  
  def stopExploring(self):
    self._enable()
    self.editEpisodeButton.setEnabled(False)    
    self.editSeasonButton.setEnabled(False)
    self.editMovieButton.setEnabled(False)    
    self.launchButton.setEnabled(False)
    self.openButton.setEnabled(False)
    self.deleteButton.setEnabled(False)    
    self._model.endUpdate()
    self._onWorkBenchChanged(bool(self._model.items())) #HACK: TODO: 
    
  def startActioning(self):
    self._disable()

  def stopActioning(self):
    self.tvView.expandAll()    
    self._enable()
    
  def getConfig(self):
    raise NotImplementedError("BaseWorkBenchWidget.getConfig not implemented")
  
  def setConfig(self, data):
    raise NotImplementedError("BaseWorkBenchWidget.getConfig not implemented")

  def _setOverallCheckedState(self, state):
    self._disable()
    self._model.setOverallCheckedState(state)
    self._enable()
    
  def _onWorkBenchChanged(self, hasChecked):
    utils.verifyType(hasChecked, bool)
    cs = self._model.overallCheckedState()
    self.selectAllCheckBox.setEnabled(not cs is None)
    if cs == None:
      cs = QtCore.Qt.Unchecked
    self.selectAllCheckBox.setCheckState(cs)
    self.workBenchChangedSignal.emit(hasChecked)
    
  def _delete(self):
    f = self._model.getDeleteItem(self._currentIndex)
    if f and self._deleteLocation(f):
      self._model.delete(self._currentIndex)
      self.tvView.expandAll()
  
  def _updateActions(self):
    for action, isEnabled in self._model.getAvailableActions(self._currentIndex).items():
      self._actionToButton[action].setEnabled(isEnabled)
    
  def _deleteLocation(self, location):
    isDel = False
    try:
      send2trash(location)
      isDel = True
    except OSError as e:
      mb = QtGui.QMessageBox(QtGui.QMessageBox.Information, 
                                   "An error occured", "Unable to move to trash. Path:\n{}".format(location))
      mb.setDetailedText("Error:\n{}".format(str(e)))
      mb.exec_()  
    return isDel
    
  def addItem(self, item):
    self._model.addItem(item)
    
  def actionableItems(self):
    return self._model.items()