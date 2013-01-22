#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------
class BaseWorkBenchModel(object):
  ACTION_DELETE = "Delete"
  ACTION_LAUNCH = "Launch File"
  ACTION_OPEN = "Open Location"
  ACTION_EPISODE = "Edit Episode"
  ACTION_SEASON = "Edit Season"
  ACTION_MOVIE = "Edit Movie"
  
  ALL_ACTIONS = ()
  
  def __init__(self):
    super(BaseWorkBenchModel, self).__init__()
    
  def getFile(self, index):
    raise NotImplementedError("BaseWorkBenchModel.fileLocation not implemented")
  
  def getFolder(self, index):
    raise NotImplementedError("BaseWorkBenchModel.folder not implemented")
  
  def getDeleteItem(self, index):
    raise NotImplementedError("BaseWorkBenchModel.getDeleteItem not implemented")
  
  def getAvailableActions(self, index):
    raise NotImplementedError("BaseWorkBenchModel.getAvailableActions not implemented")
  
  def getRenameItem(self, index):
    raise NotImplementedError("BaseWorkBenchModel.getRenameItem not implemented")  