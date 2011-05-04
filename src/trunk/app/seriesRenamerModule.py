#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import glob
import logging
import os
import re
from PyQt4 import QtCore, QtGui

from common import extension, fileHelper, logModel, utils
from tv import outputFormat, season, seasonHelper

import inputWidget
import logging
import logWidget
import outputWidget
import workBenchWidget

# --------------------------------------------------------------------------------------------------------------------
class SeriesRenamerModule(QtCore.QObject):
  def __init__(self, parent=None):
    super(QtCore.QObject, self).__init__(parent)
    
    #input widget
    self.inputWidget_ = inputWidget.InputWidget(parent)
    self.inputWidget_.exploreSignal_.connect(self._explore)
    
    #workbench widget
    self.workBenchWidget_ = workBenchWidget.WorkBenchWidget(parent)
    
    #output widget
    self.outputWidget_ = outputWidget.OutputWidget(parent)
    self.outputWidget_.renameSignal_.connect(self._rename)
    self.workBenchWidget_.workBenchChangedSignal_.connect(self.outputWidget_.enableControls)
    self.inputProgressBar_ = self.inputWidget_.progressBar_
    self.inputProgressBar_.setVisible(False)
    
    #progress widget
    self.outputProgressBar_ = self.outputWidget_.progressBar_
    
    #log widget
    self.logWidget_ = logWidget.LogWidget(parent)
  
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
    self._enableControls(False)
    self.inputProgressBar_.setVisible(True)
    ext = extension.FileExtensions([])
    ext.setExtensionsFromString(self.inputWidget_.inputSettings_.extensions_)
    seasons = seasonHelper.SeasonHelper.getSeasonsForFolders(self.inputWidget_.inputSettings_.folder_, \
                                                             self.inputWidget_.inputSettings_.showRecursive_, \
                                                             ext)
    self.workBenchWidget_.updateModel(seasons)
    self.inputProgressBar_.setVisible(False)
    self._enableControls(True)
    
  def _enableControls(self, isEnabled):
    self.inputWidget_.enableControls(isEnabled)
    self.workBenchWidget_.setEnabled(isEnabled)
    self.outputWidget_.enableControls(isEnabled)
    
  def _rename(self):
    self._enableControls(False)
    self.logWidget_.onRename()
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
    actioner.setMessageCallback(self._addMessage)
    results = actioner.performActions(filenames)
    self._sendSummaryMessages(results)
    self._enableControls(True)

  def _sendSummaryMessages(self, results):
    utils.verifyType(results, dict)
    for key in results.keys():
      text = "*** %s: %d" % (fileHelper.MoveItemActioner.resultStr(key), results[key])
      self._addMessage(logModel.LogItem(logModel.LogLevel.CRITICAL, text))
    
  def _updateProgress(self, percentageComplete):
    utils.verifyType(percentageComplete, int)
    self.outputProgressBar_.setValue(percentageComplete)

  def _addMessage(self, msg):
    utils.verifyType(msg, logModel.LogItem)
    self.logWidget_.appendMessage(msg)
  