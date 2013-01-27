#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------
import abc

from common import file_helper

# --------------------------------------------------------------------------------------------------------------------
class BaseRenameItem(object):
  """ stores filename and new metadata used to rename file """
  __metaclass__ = abc.ABCMeta
  
  def __init__(self, filename):
    super(BaseRenameItem, self).__init__()
    self.filename = filename
    self.file_size = file_helper.FileHelper.get_file_size(filename)
    self.ext = file_helper.FileHelper.extension(filename)
    self.output_folder = file_helper.FileHelper.dirname(self.filename)
  
  @abc.abstractmethod  
  def get_info(self):
    pass

# --------------------------------------------------------------------------------------------------------------------
class BaseInfo(object):
  """ objects retrieved from InfoClients """
  __metaclass__ = abc.ABCMeta
  
  @abc.abstractmethod
  def to_search_params(self):
    pass
  
  def has_data(self):
    return True

# --------------------------------------------------------------------------------------------------------------------
class BaseInfoClientSearchParams(object):
  """ objects sent to the InfoClients so to retrieve BaseInfo objects """
  
  __metaclass__ = abc.ABCMeta
    
  @abc.abstractmethod
  def get_key(self):
    pass
  
  @abc.abstractmethod
  def to_info(self):
    pass
    
