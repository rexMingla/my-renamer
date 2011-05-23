#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Website:             http://code.google.com/p/dps-x509/
# Purpose of document: Class used to decorate the LogModel
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore, QtGui

from common import utils

import logModel

# --------------------------------------------------------------------------------------------------------------------
class LogStyledDelegate(QtGui.QStyledItemDelegate):
  """ Display error message in the log in a noticable fashion. """
  def paint(self, painter, option, index):
    level, isOk = index.model().data(index, logModel.LogModel.LOG_LEVEL_ROLE).toInt()
    utils.verify(isOk, "Cast to int ok")
    if level >= logModel.LogLevel.ERROR:
      text = index.model().data(index, QtCore.Qt.DisplayRole).toString()
      painter.save()
      painter.setPen(QtCore.Qt.red)
      painter.setBrush(QtCore.Qt.blue)
      painter.setBackground(QtCore.Qt.green)
      painter.drawText(option.rect, QtCore.Qt.AlignLeft, text)
      painter.restore()    
    else:
      QtGui.QStyledItemDelegate.paint(self, painter, option, index)
      