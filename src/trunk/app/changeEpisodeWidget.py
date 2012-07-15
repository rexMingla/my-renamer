#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Widget allowing the user to associate an episode with a given file 
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui
from PyQt4 import QtGui
from PyQt4 import uic

from common import utils
from tv import episode
from tv import moveItemCandidate
from tv import outputFormat
from tv import season

# --------------------------------------------------------------------------------------------------------------------
class ChangeEpisodeWidget(QtGui.QDialog):
  """ Allows the user to select the episode name for a given file """
  def __init__(self, parent=None):
    super(QtGui.QDialog, self).__init__(parent)
    self._ui = uic.loadUi("ui/ui_ChangeEpisode.ui", self)
    self._ui.pickFromListRadio_.toggled.connect(self._ui.episodeComboBox_.setEnabled)
    self.setWindowModality(True)
    
  def showEvent(self, event):
    """ protected Qt function """
    utils.verify(self._ui.episodeComboBox_.count() > 0, "No items in list")
    self.setMaximumHeight(self.sizeHint().height())
    self.setMinimumHeight(self.sizeHint().height())
  
  def setData(self, ssn, ep):
    """ Fill the dialog with the data prior to being shown """
    utils.verifyType(ssn, season.Season)
    utils.verifyType(ep, moveItemCandidate.MoveItemCandidate)
    self._ui.episodeComboBox_.clear()
    moveItemCandidates = copy.copy(ssn.moveItemCandidates_)
    moveItemCandidates = sorted(moveItemCandidates, key=lambda item: item.destination_.epNum_)
    for mi in moveItemCandidates:
      if mi.destination_.epName_ <> episode.UNRESOLVED_NAME:
        displayName = "%d: %s" % (mi.destination_.epNum_, mi.destination_.epName_)
        self._ui.episodeComboBox_.addItem(displayName, mi.destination_.epNum_)
    index = self._ui.episodeComboBox_.findData(ep.source_.epNum_)
    if index <> -1:
      self._ui.pickFromListRadio_.setChecked(True)
      self._ui.episodeComboBox_.setCurrentIndex(index)
    else:
      self._ui.ignoreRadio_.setChecked(True)
    self._ui.filenameLabel_.setText(ep.source_.filename_)
    self._ui.episodeComboBox_.setEnabled(index <> -1)
    
  def episodeNumber(self):
    """ 
    Returns the currently selected episode number from the dialog. 
    Returns episode.UNRESOLVED_KEY if non is selected. 
    """
    if self._ui.ignoreRadio_.isChecked():
      return episode.UNRESOLVED_KEY
    else:
      return self._ui.episodeComboBox_.itemData(self._ui.episodeComboBox_.currentIndex())
   