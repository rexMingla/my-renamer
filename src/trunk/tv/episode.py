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
import episode

UNRESOLVED_KEY = -1
UNRESOLVED_NAME = "" 

# --------------------------------------------------------------------------------------------------------------------
class SourceEpisode(object):
  """ Information about an input file """
  def __init__(self, epNum, filename):
    utils.verifyType(epNum, int)
    utils.verifyType(filename, str)
    self.epNum_ = epNum
    self.filename_ = filename
    (dummy, self.extension_) = os.path.splitext(filename)
    
  @staticmethod
  def createUnresolvedSource():
    return SourceEpisode(episode.UNRESOLVED_KEY, episode.UNRESOLVED_NAME)

  def __str__(self):
    return "<SourceEpisode: #:%d name:%s>" % (self.epNum_, self.filename_)   
    
  def __eq__(self, other):
    return self.epNum_ == other.epNum_ and self.filename_ == other.filename_
  
  def __hash__(self):
    return hash(self.epNum_) + hash(self.filename_)
  
  def __copy__(self):
    return SourceEpisode(self.epNum_, self.filename_)
  
# --------------------------------------------------------------------------------------------------------------------
class DestinationEpisode(object):
  """ Information about an output file """
  def __init__(self, epNum, epName):
    utils.verifyType(epNum, int)
    utils.verifyType(epName, str)
    self.epNum_ = epNum
    self.epName_ = epName
    
  @staticmethod
  def createUnresolvedDestination():
    return DestinationEpisode(episode.UNRESOLVED_KEY, episode.UNRESOLVED_NAME)

  def __str__(self):
    return "<DestinationEpisode: #:%d name:%s>" % (self.epNum_, self.epName_)   

  def __eq__(self, other):
    return self.epNum_ == other.epNum_ and self.epName_ == other.epName_
  
  def __hash__(self):
    return hash(self.epNum_) + hash(self.epName_)

  def __copy__(self):
    return DestinationEpisode(self.epNum_, self.epName_)
  
# --------------------------------------------------------------------------------------------------------------------
class EpisodeMap(object):
  """ 
  Collection of input or output files mapped by key. In the case of duplicate keys, the first is accepted 
  and all duplicates thereafter are considered unresolved.
  """
  def __init__(self):
    super(EpisodeMap, self).__init__()
    self.matches_ = {}
    self.unresolved_ = []
  
  def addItem(self, item):
    epNumStr = str(item.epNum_)
    if item.epNum_ == UNRESOLVED_KEY:
      self.unresolved_.append(item)
    elif epNumStr in self.matches_:
      utils.out("key already exists: %d" % item.epNum_, 1)
      tempItem = copy.copy(item)
      tempItem.epNum_ = UNRESOLVED_KEY
      self.unresolved_.append(tempItem)
    else:
      self.matches_[epNumStr] = item #jsonpickle converts dicts with int keys to string keys :(
  
  def setKeyForFilename(self, newKey, filename):
    """ Set a new key for a given filename, performing required sanitization in the event of key collisions. """
    utils.verifyType(newKey, int)
    utils.verifyType(filename, str)
    
    sourceEp = None
    for key, source in self.matches_.items():
      if source.filename_ == filename:
        sourceEp = source
        break
    if not sourceEp:
      for ep in self.unresolved_:
        if ep.filename_ == filename:
          sourceEp = ep
          break
        
    if not sourceEp or sourceEp.epNum_ == newKey:
      return

    #todo: filthy. clean me!!
    oldEpNum = sourceEp.epNum_
    sourceEp.epNum_ = newKey
    if oldEpNum == episode.UNRESOLVED_KEY:
      utils.verify(not newKey == episode.UNRESOLVED_KEY, "old key <> new key")
      self.unresolved_.remove(sourceEp)
      newKeyStr = str(newKey)
      if newKeyStr in self.matches_:
        oldEp = copy.copy(self.matches_[newKeyStr])
        oldEp.epNum_ = episode.UNRESOLVED_KEY
        self.unresolved_.append(oldEp)
      self.matches_[str(sourceEp.epNum_)] = sourceEp
    else: #oldEpNum in matches
      del self.matches_[str(oldEpNum)]
      if newKey == episode.UNRESOLVED_KEY:
        self.unresolved_.append(sourceEp)
      else: #newEp in matches
        newKeyStr = str(newKey)
        if newKeyStr in self.matches_:
          oldEp = copy.copy(self.matches_[newKeyStr])
          oldEp.epNum_ = episode.UNRESOLVED_KEY          
          self.unresolved_.append(oldEp)
        self.matches_[str(sourceEp.epNum_)] = sourceEp

  def __eq__(self, other):
    utils.verifyType(other, EpisodeMap)
    return utils.listCompare(self.unresolved_, other.unresolved_) and utils.dictCompare(self.matches_, other.matches_)
  
  def __str__(self):
    return "<EpisodeMap: #matches:%d #unresolved:%d>" % (len(self.matches_), len(self.unresolved_))
  
  def __copy__(self):
    ret = EpisodeMap()
    for key in self.matches_:
      ret.matches_[key] = copy.copy(self.matches_[key])
    for item in self.unresolved_:
      ret.unresolved_.append(copy.copy(item))
    return ret
      