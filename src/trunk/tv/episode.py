#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import copy
import os

from app import utils
import episode

UNRESOLVED_KEY = -1 
UNRESOLVED_NAME = "" 

# --------------------------------------------------------------------------------------------------------------------
class SourceEpisode:
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
class DestinationEpisode:
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
class EpisodeMap:
  def __init__(self):
    self.matches_ = {}
    self.unresolved_ = []
  
  def addItem(self, item):
    if item.epNum_ == UNRESOLVED_KEY:
      self.unresolved_.append(item)
    elif self.matches_.has_key(item.epNum_):
      utils.out("key already exists: %d" % item.epNum_, 1)
      tempItem = copy.copy(item)
      tempItem.epNum_ = UNRESOLVED_KEY
      self.unresolved_.append(tempItem)
    else:
      self.matches_[item.epNum_] = item
  
  def setKeyForFilename(self, newKey, filename):
    utils.verifyType(newKey, int)
    utils.verifyType(filename, str)
    
    sourceEp = None
    for key in self.matches_.keys():
      if self.matches_[key].filename_ == filename:
        sourceEp = self.matches_[key]
        break
    if not sourceEp:
      for ep in self.unresolved_:
        if ep.filename_ == filename:
          sourceEp = ep
          break
        
    if not sourceEp or sourceEp.epNum_ == newKey:
      return

    oldEpNum = sourceEp.epNum_
    sourceEp.epNum_ = newKey
    if oldEpNum == episode.UNRESOLVED_KEY:
      utils.verify(not newKey == episode.UNRESOLVED_KEY, "old key <> new key")
      self.unresolved_.remove(sourceEp)
      if self.matches_.has_key(newKey):
        oldEp = copy.copy(self.matches_[newKey])
        oldEp.epNum_ = episode.UNRESOLVED_KEY
        self.unresolved_.append(oldEp)
      self.matches_[sourceEp.epNum_] = sourceEp
    else: #oldEpNum in matches
      del self.matches_[oldEpNum]
      if newKey == episode.UNRESOLVED_KEY:
        self.unresolved_.append(sourceEp)
      else: #newEp in matches
        if self.matches_.has_key(newKey):
          oldEp = copy.copy(self.matches_[newKey])
          oldEp.epNum_ = episode.UNRESOLVED_KEY          
          self.unresolved_.append(oldEp)
        self.matches_[sourceEp.epNum_] = sourceEp

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
      