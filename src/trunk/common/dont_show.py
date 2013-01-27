#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: don't show this again prompt
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui

# --------------------------------------------------------------------------------------------------------------------
class _DontShowAgainDialog(QtGui.QDialog):
  """ 
  displays dialog with 'don't show this message again' checkbox.
  source: http://qt-project.org/forums/viewthread/21705 
  """  
  def __init__(self, title, text, options=QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, parent=None):
    super(_DontShowAgainDialog, self).__init__(parent)

    self.setWindowTitle(title)
    self._dont_show_check_box = QtGui.QCheckBox("Don't show this dialog again", self)

    self._button_box = QtGui.QDialogButtonBox(options, parent=self, accepted=self.accept, rejected=self.reject)
    self._button_box.clicked.connect(self._button_clicked)
    
    layout = QtGui.QVBoxLayout(self)
    layout.addWidget(QtGui.QLabel(text, self))
    layout.addWidget(self._dont_show_check_box)
    layout.addWidget(self._button_box)
    layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
    self.setLayout(layout)
    self.button = None
    
  def _button_clicked(self, button):
    self.button = self._button_box.standardButton(button)
    
  def is_checked(self):
    return self._dont_show_check_box.isChecked()
  
# --------------------------------------------------------------------------------------------------------------------
class DontShowManager:
  """ displays 'don't show this message again' dialog if previously not shown, otherwise returns result """
  _dont_shows = {}
  
  @classmethod
  def get_answer(cls, title, text, key, options=QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, parent=None): 
    if key in cls._dont_shows:
      return cls._dont_shows[key]
    else:
      dialog = _DontShowAgainDialog(title, text, options, parent)
      if dialog.exec_() == QtGui.QDialog.Accepted and dialog.is_checked():
        cls._dont_shows[key] = dialog.button
      return dialog.button
    
  @classmethod
  def get_config(cls):
    return cls._dont_shows

  @classmethod
  def set_config(cls, data):
    cls._dont_shows = data
