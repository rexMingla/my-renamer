#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Widget allowing the user to associate an episode with a given file 
# --------------------------------------------------------------------------------------------------------------------
import copy

from PyQt4 import QtGui
from PyQt4 import uic

from common import fileHelper
from common import outputFormat
from common import utils
from tv import episode
from tv import moveItemCandidate
from tv import season

# --------------------------------------------------------------------------------------------------------------------
class EditEpisodeWidget(QtGui.QDialog):
  """ Allows the user to assign an episode to a given file """
  def __init__(self, parent=None):
    super(QtGui.QDialog, self).__init__(parent)
    self._ui = uic.loadUi("ui/ui_ChangeEpisode.ui", self)
    self.pickFromListRadio.toggled.connect(self.episodeComboBox.setEnabled)
    self.setWindowModality(True)
    
  def showEvent(self, event):
    """ protected Qt function """
    utils.verify(self.episodeComboBox.count() > 0, "No items in list")
    self.setMaximumHeight(self.sizeHint().height())
    self.setMinimumHeight(self.sizeHint().height())
  
  def setData(self, ssn, ep):
    """ Fill the dialog with the data prior to being shown """
    utils.verifyType(ssn, season.Season)
    utils.verifyType(ep, moveItemCandidate.MoveItemCandidate)
    self.episodeComboBox.clear()
    moveItemCandidates = copy.copy(ssn.moveItemCandidates)
    moveItemCandidates = sorted(moveItemCandidates, key=lambda item: item.destination.epNum)
    for mi in moveItemCandidates:
      if mi.destination.epName != episode.UNRESOLVED_NAME:
        displayName = "{}: {}".format(mi.destination.epNum, mi.destination.epName)
        self.episodeComboBox.addItem(displayName, mi.destination.epNum)
    index = self.episodeComboBox.findData(ep.source.epNum)
    if index != -1:
      self.pickFromListRadio.setChecked(True)
      self.episodeComboBox.setCurrentIndex(index)
    else:
      self.ignoreRadio.setChecked(True)
    self.filenameEdit.setText(fileHelper.FileHelper.basename(ep.source.filename))
    self.filenameEdit.setToolTip(ep.source.filename)
    self.episodeComboBox.setEnabled(index != -1)
    
  def episodeNumber(self):
    """ 
    Returns the currently selected episode number from the dialog. 
    Returns episode.UNRESOLVED_KEY if non is selected. 
    """
    if self.ignoreRadio.isChecked():
      return episode.UNRESOLVED_KEY
    else:
      return self.episodeComboBox.itemData(self.episodeComboBox.currentIndex())
   