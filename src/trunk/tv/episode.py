#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import os

from app import utils

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
    
  def __str__(self):
    return "<SourceEpisode: #:%d name:%s>" % (self.epNum_, self.filename_)   
    
  def __eq__(self, other):
    return self.epNum_ == other.epNum_ and self.filename_ == other.filename_
  
  def __hash__(self):
    return hash(self.epNum_) + hash(self.filename_) 
  
# --------------------------------------------------------------------------------------------------------------------
class DestinationEpisode:
  def __init__(self, epNum, epName):
    utils.verifyType(epNum, int)
    utils.verifyType(epName, str)
    self.epNum_ = epNum
    self.epName_ = epName
    
  def __str__(self):
    return "<DestinationEpisode: #:%d name:%s>" % (self.epNum_, self.epName_)   

  def __eq__(self, other):
    return self.epNum_ == other.epNum_ and self.epName_ == other.epName_
  
  def __hash__(self):
    return hash(self.epNum_) + hash(self.epName_) 

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
      self.unresolved_.append(item)
    else:
      self.matches_[item.epNum_] = item

  def __eq__(self, other):
    #TODO:
    utils.verifyType(other, EpisodeMap)
    return utils.listCompare(self.unresolved_, other.unresolved_) and utils.dictCompare(self.matches_, other.matches_)
  
  def __str__(self):
    return "<EpisodeMap: #matches:%d #unresolved:%d>" % \
             (len(self.matches_), len(self.unresolved_)) 
    