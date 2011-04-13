#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import glob
import os
import re
from PyQt4 import QtCore, QtGui

import inputWidget
import outputWidget
import workBenchWidget

from app import utils
from tv import seasonHelper, season, extension

class SeriesRenamerModule(QtCore.QObject):
  def __init__(self, parent=None):
    super(QtCore.QObject, self).__init__(parent)
    
    #input widget
    self.inputWidget_ = inputWidget.InputWidget()
    self.inputWidget_.exploreSignal_.connect(self._onExplore)
    
    #workbench widget
    self.workBenchWidget_ = workBenchWidget.WorkBenchWidget()
    
    #output widget
    self.outputWidget_ = outputWidget.OutputWidget()
    self.outputWidget_.saveSignal_.connect(self._onSave)
  
  def _getFolders(self, rootFolder, isRecursive):
    dirs = []
    rootFolder = rootFolder.replace("\\", "/")
    if not isRecursive:
      dirs.append(rootFolder)
    else:
      for root, dirs, files in os.walk(rootFolder):
        dirs.append(root)      
    return dirs 

  def _onExplore(self):
    seasons = seasonHelper.SeasonHelper.getSeasonsForFolders(self.inputWidget_.inputSettings_.folder_, \
                                                             self.inputWidget_.inputSettings_.showRecursive_)
    self.workBenchWidget_.updateModel(seasons)
    
  def _onSave(self):
    pass
