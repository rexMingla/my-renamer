#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------
from common import file_helper

# --------------------------------------------------------------------------------------------------------------------
class BaseRenameItem(object):
  """ stores filename and new metadata used to rename file """
  def __init__(self, filename):
    super(BaseRenameItem, self).__init__()
    self.filename = filename
    self.file_size = file_helper.FileHelper.get_file_size(filename)
    self.ext = file_helper.FileHelper.extension(filename)
    self.output_folder = file_helper.FileHelper.dirname(self.filename)
  
  def get_info(self):
    raise NotImplementedError("BaseRenameItem.get_info not implemented")
  
# --------------------------------------------------------------------------------------------------------------------
class BaseInfo(object):
  """ objects retrieved from InfoClients """
  
  def to_search_params(self):
    raise NotImplementedError("BaseInfo.to_search_params not implemented")
  
  def has_data(self):
    return True

# --------------------------------------------------------------------------------------------------------------------
class BaseInfoClientSearchParams(object):
  """ objects sent to the InfoClients so to retrieve BaseInfo objects """
  def get_key(self):
    raise NotImplementedError("BaseInfoClientSearchParams.get_key not implemented")
  
  def to_info(self):
    raise NotImplementedError("BaseInfoClientSearchParams.to_info not implemented")
    
