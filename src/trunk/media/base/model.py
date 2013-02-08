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
    
  def get_file(self, index):
    raise NotImplementedError("BaseWorkBenchModel.get_file not implemented")
  
  def get_folder(self, index):
    raise NotImplementedError("BaseWorkBenchModel.get_folder not implemented")
  
  def get_delete_item(self, index):
    raise NotImplementedError("BaseWorkBenchModel.get_delete_item not implemented")
  
  def get_available_actions(self, index):
    raise NotImplementedError("BaseWorkBenchModel.get_available_actions not implemented")
  
  def get_rename_item(self, index):
    raise NotImplementedError("BaseWorkBenchModel.get_rename_item not implemented")
  