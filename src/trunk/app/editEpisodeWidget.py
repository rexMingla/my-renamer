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
from tv import tvTypes

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
    #utils.verifyType(ssn, tvTypes.Season)
    #utils.verifyType(ep, tvTypes.EpisodeRenameItem)
    self.episodeComboBox.clear()
    #episodeMoveItems = copy.copy(ssn.episodeMoveItems)
    #episodeMoveItems = sorted(episodeMoveItems, key=lambda item: item.info.epNum)
    for mi in ssn.episodeMoveItems:
      if mi.info.epNum != tvTypes.UNRESOLVED_KEY:
        displayName = "{}: {}".format(mi.info.epNum, mi.info.epName)
        self.episodeComboBox.addItem(displayName, mi.info.epNum)
    index = self.episodeComboBox.findData(ep.info.epNum)
    if index != -1:
      self.pickFromListRadio.setChecked(True)
      self.episodeComboBox.setCurrentIndex(index)
    else:
      self.ignoreRadio.setChecked(True)
    self.filenameEdit.setText(fileHelper.FileHelper.basename(ep.filename))
    self.filenameEdit.setToolTip(ep.filename)
    self.episodeComboBox.setEnabled(index != -1)
    
  def episodeNumber(self):
    """ 
    Returns the currently selected episode number from the dialog. 
    Returns tvTypes.UNRESOLVED_KEY if non is selected. 
    """
    if self.ignoreRadio.isChecked():
      return tvTypes.UNRESOLVED_KEY
    else:
      return self.episodeComboBox.itemData(self.episodeComboBox.currentIndex()).toInt()[0]
   