#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: don't show this again prompt
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui
from PyQt4 import uic

# --------------------------------------------------------------------------------------------------------------------
class _DontShowAgainDialog(QtGui.QDialog):
  """ 
  displays dialog with 'don't show this message again' checkbox.
  source: http://qt-project.org/forums/viewthread/21705 
  """  
  def __init__(self, title, text, options=QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, parent=None):
    super(_DontShowAgainDialog, self).__init__(parent)

    self.setWindowTitle(title)
    self._dontShowCheckBox = QtGui.QCheckBox("Don't show this dialog again", self)

    self._buttonBox = QtGui.QDialogButtonBox(options, parent=self, accepted=self.accept, rejected=self.reject)
    self._buttonBox.clicked.connect(self._buttonClicked)
    
    l = QtGui.QVBoxLayout(self)
    l.addWidget(QtGui.QLabel(text, self))
    l.addWidget(self._dontShowCheckBox)
    l.addWidget(self._buttonBox)
    l.setSizeConstraint(QtGui.QLayout.SetFixedSize)
    self.setLayout(l)
    self.button = None
    
  def _buttonClicked(self, button):
    self.button = self._buttonBox.standardButton(button)
    
  def isChecked(self):
    return self._dontShowCheckBox.isChecked()
  
# --------------------------------------------------------------------------------------------------------------------
class DontShowManager:
  """ displays 'don't show this message again' dialog if previously not shown, otherwise returns result """
  _dontShows = {}
  
  @classmethod
  def getAnswer(cls, title, text, key, options=QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, parent=None): 
    if key in cls._dontShows:
      return cls._dontShows[key]
    else:
      d = _DontShowAgainDialog(title, text, options, parent)
      if d.exec_() == QtGui.QDialog.Accepted and d.isChecked():
        cls._dontShows[key] = d.button
      return d.button
    
  @classmethod
  def getConfig(cls):
    return cls._dontShows

  @classmethod
  def setConfig(cls, data):
    cls._dontShows = data
