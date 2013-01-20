#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------
import abc

import fileHelper

# --------------------------------------------------------------------------------------------------------------------
class BaseRenameItem(object):
  """ stores filename and new metadata used to rename file """
  __metaclass__ = abc.ABCMeta
  
  def __init__(self, filename):
    super(BaseRenameItem, self).__init__()
    self.filename = filename
    self.fileSize = fileHelper.FileHelper.getFileSize(filename)
    self.ext = fileHelper.FileHelper.extension(filename)
    self.outputFolder = fileHelper.FileHelper.dirname(self.filename)
  
  @abc.abstractmethod  
  def getInfo(self):
    pass

# --------------------------------------------------------------------------------------------------------------------
class BaseInfo(object):
  """ objects retrieved from InfoClients """
  __metaclass__ = abc.ABCMeta
  
  @abc.abstractmethod
  def toSearchParams(self):
    pass
  
  def hasData(self):
    return True

# --------------------------------------------------------------------------------------------------------------------
class BaseInfoClientSearchParams(object):
  """ objects sent to the InfoClients so to retrieve BaseInfo objects """
  
  __metaclass__ = abc.ABCMeta
    
  @abc.abstractmethod
  def getKey(self):
    pass
  
  @abc.abstractmethod
  def toInfo(self):
    pass
    
