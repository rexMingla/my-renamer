#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------
from common import file_helper

MOVIE_MODE = "movie"
TV_MODE = "tv"

VALID_MODES = (MOVIE_MODE, TV_MODE)

# --------------------------------------------------------------------------------------------------------------------
class BaseRenameItem(object):
  READY          = "Ready"
  UNKNOWN        = "Unknown"
  
  """ stores filename and new metadata used to rename file """
  def __init__(self, filename):
    super(BaseRenameItem, self).__init__()
    self.filename = filename
    self.file_size = file_helper.FileHelper.getFileSize(filename)
    self.ext = file_helper.FileHelper.extension(filename)
    self.output_folder = file_helper.FileHelper.dirname(self.filename)

  def getInfo(self):
    raise NotImplementedError("BaseRenameItem.getInfo not implemented")

  def status(self):
    raise NotImplementedError("BaseRenameItem.status not implemented")    

# --------------------------------------------------------------------------------------------------------------------
class BaseInfo(object):
  """ objects retrieved from InfoClients """
  def __init__(self, mode):
    assert(mode in VALID_MODES)
    self.mode = mode
    
  def toSearchParams(self):
    raise NotImplementedError("BaseInfo.toSearchParams not implemented")

  def hasData(self):
    return True

# --------------------------------------------------------------------------------------------------------------------
class BaseInfoClientSearchParams(object):
  """ objects sent to the InfoClients so to retrieve BaseInfo objects """
  def getKey(self):
    raise NotImplementedError("BaseInfoClientSearchParams.getKey not implemented")

  def toInfo(self):
    raise NotImplementedError("BaseInfoClientSearchParams.toInfo not implemented")

