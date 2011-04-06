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
    
# --------------------------------------------------------------------------------------------------------------------
class DestinationEpisode:
  def __init__(self, epNum, epName):
    utils.verifyType(epNum, int)
    utils.verifyType(epName, str)
    self.epNum_ = epNum
    self.epName_ = epName

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

  @staticmethod
  def areEqual(left, right):
    utils.verifyType(left, EpisodeMap)
    utils.verifyType(right, EpisodeMap)
    ndiffs = sum(1 for a,b in zip(left.matches_.keys(),right.matches_.keys()) \
               if (a==b==1 and left.matches_[a] == right.matches_[a]))
    if not ndiffs:
      ndiffs = sum(1 for a,b in zip(left.unresolved_,right.unresolved_) if (a==b==1))
    
    return not ndiffs 
     
    