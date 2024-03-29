#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: don't show this again prompt
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

# --------------------------------------------------------------------------------------------------------------------
def addWidgetToContainer(parent, widget, spacing=4):
  layout = QtGui.QVBoxLayout()
  layout.setContentsMargins(spacing, spacing, spacing, spacing)
  layout.addWidget(widget)
  parent.setLayout(layout)
  return parent

# --------------------------------------------------------------------------------------------------------------------
class ProgressWidget(QtGui.QWidget):
  start_signal = QtCore.pyqtSignal()
  stop_signal = QtCore.pyqtSignal()
  start_signal = QtCore.pyqtSignal()
  stop_signal = QtCore.pyqtSignal()

  def __init__(self, start_label="Start", stop_label="Stop", widget=None, parent=None):
    super(ProgressWidget, self).__init__(parent)
    self.start_button = QtGui.QPushButton(start_label, self)
    self.start_button.setText(start_label)
    self.start_button.setVisible(bool(start_label))
    self.start_button.setIcon(QtGui.QIcon("img/search.png"))
    self.start_button.clicked.connect(self.start)

    self.stop_button = QtGui.QPushButton(stop_label, self)
    self.stop_button.setText(stop_label)
    self.stop_button.setVisible(bool(stop_label))
    self.stop_button.setIcon(QtGui.QIcon("img/stop.png"))
    self.stop_button.clicked.connect(self.stop)

    self.progress_bar = QtGui.QProgressBar(self)
    self.progress_bar.setMinimumHeight(10)
    self.progress_bar.setMaximumHeight(10)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    self.progress_bar.setSizePolicy(sizePolicy)

    layout = QtGui.QHBoxLayout(self)
    layout.setSpacing(4)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(self.start_button)
    layout.addWidget(self.stop_button)
    if widget:
      layout.addWidget(widget)
    layout.addWidget(self.progress_bar)
    layout.addSpacerItem(QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed))

    self.is_running = False
    self.setProgressRange(0, 100)
    self.setProgress(0)
    self.stop(force_update=True)

  def setProgressRange(self, min_, max_):
    self.progress_bar.setRange(min_, max_)
    self.progress_bar.setTextVisible(min_ != max_)

  def setProgress(self, value):
    self.progress_bar.setValue(value)

  def start(self, force_update=False):
    if not force_update and self.is_running:
      return
    self.is_running = True
    self.progress_bar.setVisible(True)
    self.start_button.setVisible(False)
    self.stop_button.setVisible(bool(self.stop_button.text()))
    self.start_signal.emit()

  def stop(self, force_update=False):
    if not force_update and not self.is_running:
      return
    self.is_running = False
    self.progress_bar.setVisible(False)
    self.start_button.setVisible(bool(self.stop_button.text()))
    self.stop_button.setVisible(False)
    self.stop_signal.emit()

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
    self._button_box.clicked.connect(self._buttonClicked)

    layout = QtGui.QVBoxLayout(self)
    layout.addWidget(QtGui.QLabel(text, self))
    layout.addWidget(self._dont_show_check_box)
    layout.addWidget(self._button_box)
    layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
    self.setLayout(layout)
    self.button = None

  def _buttonClicked(self, button):
    self.button = self._button_box.standardButton(button)

  def isChecked(self):
    return self._dont_show_check_box.isChecked()

# --------------------------------------------------------------------------------------------------------------------
class DontShowManager:
  """ displays 'don't show this message again' dialog if previously not shown, otherwise returns result """
  _dont_shows = {}

  @classmethod
  def getAnswer(cls, title, text, key, options=QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, parent=None):
    if key in cls._dont_shows:
      return cls._dont_shows[key]
    else:
      dialog = _DontShowAgainDialog(title, text, options, parent)
      if dialog.exec_() == QtGui.QDialog.Accepted and dialog.isChecked():
        cls._dont_shows[key] = dialog.button
      return dialog.button

  @classmethod
  def getConfig(cls):
    return cls._dont_shows

  @classmethod
  def setConfig(cls, data):
    cls._dont_shows = data

