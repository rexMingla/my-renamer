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
from tv import fileHelper, outputFormat, seasonHelper, season, extension

class SeriesRenamerModule(QtCore.QObject):
  def __init__(self, parent=None):
    super(QtCore.QObject, self).__init__(parent)
    
    #input widget
    self.inputWidget_ = inputWidget.InputWidget()
    self.inputWidget_.exploreSignal_.connect(self._explore)
    
    #workbench widget
    self.workBenchWidget_ = workBenchWidget.WorkBenchWidget()
    
    #output widget
    self.outputWidget_ = outputWidget.OutputWidget()
    self.outputWidget_.renameSignal_.connect(self._rename)
    self.workBenchWidget_.workBenchChangedSignal_.connect(self.outputWidget_.enableControls)
    
    #progress widget
    self.progressBar_ = QtGui.QProgressBar()
    self.progressBar_.setMinimum(0)
    self.progressBar_.setMaximum(100)
    #self.progressBar_.setVisible(False)
  
  def _getFolders(self, rootFolder, isRecursive):
    dirs = []
    rootFolder = rootFolder.replace("\\", "/")
    if not isRecursive:
      dirs.append(rootFolder)
    else:
      for root, dirs, files in os.walk(rootFolder):
        dirs.append(root)      
    return dirs 

  def _explore(self):
    self.inputWidget_.enableControls(False)
    ext = extension.FileExtensions([])
    ext.setExtensionsFromString(self.inputWidget_.inputSettings_.extensions_)
    seasons = seasonHelper.SeasonHelper.getSeasonsForFolders(self.inputWidget_.inputSettings_.folder_, \
                                                             self.inputWidget_.inputSettings_.showRecursive_, \
                                                             ext)
    self.workBenchWidget_.updateModel(seasons)
    self.inputWidget_.enableControls(True)
    
  def _enableControls(self, isEnabled):
    self.inputWidget_.enableControls(isEnabled)
    self.workBenchWidget_.setEnabled(isEnabled)
    self.outputWidget_.enableControls(isEnabled)
    
  def _rename(self):
    self._enableControls(False)
    #self.progressBar_.setVisible(True)
    formatSettings = self.outputWidget_.outputSettings_
    filenames = []
    seasons = self.workBenchWidget_.seasons()
    utils.verify(seasons, "Must have seasons to have gotten this far")
    for season in seasons:
      outputFolder = formatSettings.outputFolder_
      if outputFolder == outputWidget.USE_SOURCE_DIRECTORY:
        outputFolder = season.inputFolder_
      oFormat = outputFormat.OutputFormat(formatSettings.outputFileFormat_)
      for ep in season.moveItems_:
        if ep.performMove_:
          im = outputFormat.InputMap(season.seasonName_, 
                                     season.seasonNum_, 
                                     ep.destination_.epNum_, 
                                     ep.destination_.epName_)
          outputBaseName = oFormat.outputToString(im, ep.source_.extension_)
          newName = fileHelper.FileHelper.joinPath(outputFolder, outputBaseName)
          filenames.append((ep.source_.filename_, newName))
    utils.verify(filenames, "Must have files to have gotten this far")
    actioner = fileHelper.MoveItemActioner(canOverwrite= not formatSettings.doNotOverwrite_, \
                                           keepSource=formatSettings.keepSourceFiles_)
    actioner.setPercentageCompleteCallback(self._updateProgress)
    actioner.performActions(filenames)
  
  def _updateProgress(self, percentageComplete):
    utils.verifyType(percentageComplete, int)
    self.progressBar_.setValue(percentageComplete)
    if percentageComplete == 100:
      self._enableControls(True)
      #self.progressBar_.setVisible(False)
