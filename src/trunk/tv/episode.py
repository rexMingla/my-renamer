#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: State classes storing input and output file information
# --------------------------------------------------------------------------------------------------------------------
import copy
import os

from common import utils
from common import fileHelper

import episode
import tvInfoClient

UNRESOLVED_KEY = -1
UNRESOLVED_NAME = "" 

# --------------------------------------------------------------------------------------------------------------------
class SourceEpisode(object):
  """ Information about an input file """
  def __init__(self, epNum, filename):
    utils.verifyType(epNum, int)
    utils.verifyType(filename, str)
    self.epNum = epNum
    self.filename = filename
    self.fileSize = fileHelper.FileHelper.getFileSize(filename)
    self.ext = fileHelper.FileHelper.extension(filename)
    
  @staticmethod
  def createUnresolvedSource():
    return SourceEpisode(episode.UNRESOLVED_KEY, episode.UNRESOLVED_NAME)

  def __str__(self):
    return "<SourceEpisode: #:{} name:{}>".format(self.epNum, self.filename)   
    
  def __eq__(self, other):
    return self.epNum == other.epNum and self.filename == other.filename
  
  def __hash__(self):
    return hash(self.epNum) + hash(self.filename)
  
  def __copy__(self):
    return SourceEpisode(self.epNum, self.filename)
  
# --------------------------------------------------------------------------------------------------------------------
class DestinationEpisode(object):
  """ Information about an output file """
  def __init__(self, epNum, epName):
    utils.verifyType(epNum, int)
    utils.verifyType(epName, str)
    self.epNum = epNum
    self.epName = epName
    
  @staticmethod
  def createUnresolvedDestination():
    return DestinationEpisode(episode.UNRESOLVED_KEY, episode.UNRESOLVED_NAME)

  def __str__(self):
    return "<DestinationEpisode: #:{} name:{}>".format(self.epNum, self.epName)   

  def __eq__(self, other):
    return self.epNum == other.epNum and self.epName == other.epName
  
  def __hash__(self):
    return hash(self.epNum) + hash(self.epName)

  def __copy__(self):
    return DestinationEpisode(self.epNum, self.epName)
  
# --------------------------------------------------------------------------------------------------------------------
class BaseEpisodeMap(object):
  """ 
  Collection of input or output files mapped by key. In the case of duplicate keys, the first is accepted 
  and all duplicates thereafter are considered unresolved.
  """
  def __init__(self):
    super(BaseEpisodeMap, self).__init__()
    self.matches = {}
    self.unresolved = []
  
  def hasData(self):
    return bool(len(self.matches) or len(self.unresolved))
  
  def addItem(self, item):
    utils.verify((isinstance(item, SourceEpisode) and isinstance(self, SourceEpisodeMap)) or 
                 (isinstance(item, DestinationEpisode) and isinstance(self, DestinationEpisodeMap)), "wrong type!")
    epNumStr = str(item.epNum)
    if item.epNum == UNRESOLVED_KEY:
      self.unresolved.append(item)
    elif epNumStr in self.matches:
      utils.logNotSet("key already exists: {}".format(item.epNum), 1)
      tempItem = copy.copy(item)
      tempItem.epNum = UNRESOLVED_KEY
      self.unresolved.append(tempItem)
    else:
      self.matches[epNumStr] = item #jsonpickle converts dicts with int keys to string keys :(
  
  def setKeyForFilename(self, newKey, filename):
    """ Set a new key for a given filename, performing required sanitization in the event of key collisions. """
    utils.verifyType(newKey, int)
    utils.verifyType(filename, str)    
    
    sourceEp = next( (source for key, source in self.matches.items() if source.filename == filename), None)
    sourceEp = sourceEp or next( (ep for ep in self.unresolved if ep.filename == filename), None)
    if not sourceEp or sourceEp.epNum == newKey:
      return
    
    oldEp = None
    newKeyStr = str(newKey)
    if newKeyStr in self.matches:
      oldEp = self.matches[newKeyStr]
      del self.matches[newKeyStr]
      
    self.removeSoureFile(sourceEp.filename)
    sourceEp.epNum = newKey
    self.addItem(sourceEp)
    if oldEp:
      self.addItem(oldEp)
        
  def removeSoureFile(self, filename):
    utils.verifyType(filename, str)
    self.matches = dict( (k, v) for k, v in self.matches.items() if filename != v.filename)
    self.unresolved = [v for v in self.unresolved if filename != v.filename]

  def __eq__(self, other):
    utils.verifyType(other, BaseEpisodeMap)
    return other and utils.listCompare(self.unresolved, other.unresolved) and utils.dictCompare(self.matches, other.matches)
  
  def __str__(self):
    return "<BaseEpisodeMap: #matches:{} #unresolved:{}>".format(len(self.matches), len(self.unresolved))
  
  def __copy__(self):
    raise NotImplementedError("Base.__copy__ not implemented")
  
class SourceEpisodeMap(BaseEpisodeMap):
  def __copy__(self):
    ret = SourceEpisodeMap()
    for key, value in self.matches.items():
      ret.matches[key] = copy.copy(value)
    ret.unresolved = map(copy.copy, self.unresolved)
    return ret

from common import infoClient

class DestinationEpisodeMap(BaseEpisodeMap, infoClient.BaseInfo):
  def __init__(self, showName="", seasonNum=""):
    super(DestinationEpisodeMap, self).__init__()
    super(infoClient.BaseInfo, self).__init__()
    self.showName = showName
    self.seasonNum = seasonNum 
    
  def __copy__(self):
    ret = DestinationEpisodeMap(self.showName, self.seasonNum)
    for key, value in self.matches.items():
      ret.matches[key] = copy.copy(value)
    ret.unresolved = map(copy.copy, self.unresolved)
    return ret
    
  def __str__(self):
    return "{} season {} - # episodes: {}".format(self.showName, self.seasonNum, len(self.matches))
  
  def toSearchParams(self):
    return tvInfoClient.TvSearchParams(self.showName, self.seasonNum)
  