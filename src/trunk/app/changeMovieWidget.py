#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Allow the user to select an season for a given folder
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtGui
from PyQt4 import uic

from common import utils
from movie import movieHelper

# --------------------------------------------------------------------------------------------------------------------
class ChangeMovieWidget(QtGui.QDialog):
  """
  The widget allows the user to select a movie info. Needs interactive search...
  """
  def __init__(self, parent=None):
    super(ChangeMovieWidget, self).__init__(parent)
    self._ui = uic.loadUi("ui/ui_ChangeMovie.ui", self)
    self.setWindowModality(True)
    
  def showEvent(self, event):
    """ protected Qt function """
    self.setMaximumHeight(self.sizeHint().height())
    self.setMinimumHeight(self.sizeHint().height())
  
  def setData(self, item):
    """ Fill the dialog with the data prior to being shown """
    utils.verifyType(item, movieHelper.Movie)
    self.item = item
    self.filenameLabel.setText(item.filename)
    self.titleEdit.setText(item.title)
    self.yearEdit.setText(item.year or "")
    self.genreEdit.setText(item.genre())
    
  def data(self):
    self.item.title = self.titleEdit.text()
    self.item.year = self.yearEdit.text()
    genre = utils.toString(self.genreEdit.text()).strip()
    if genre:
      genre = [genre]
    else:
      genre = []
    self.item.genres = genre
    return self.item
    

  