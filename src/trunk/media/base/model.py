#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------
import abc

# --------------------------------------------------------------------------------------------------------------------
class BaseWorkBenchModel(object):
  __metaclass__ = abc.ABCMeta
  
  ACTION_DELETE = "Delete"
  ACTION_LAUNCH = "Launch File"
  ACTION_OPEN = "Open Location"
  ACTION_EPISODE = "Edit Episode"
  ACTION_SEASON = "Edit Season"
  ACTION_MOVIE = "Edit Movie"
  
  ALL_ACTIONS = ()
  
  def __init__(self):
    super(BaseWorkBenchModel, self).__init__()
    
  @abc.abstractmethod
  def get_file(self, index):
    pass
  
  @abc.abstractmethod
  def get_folder(self, index):
    pass
  
  @abc.abstractmethod
  def get_delete_item(self, index):
    pass
  
  @abc.abstractmethod
  def get_available_actions(self, index):
    pass
  
  @abc.abstractmethod
  def get_rename_item(self, index):
    pass
  