#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import sys 
import os
sys.path.insert(0, os.path.abspath(__file__+"/../../"))

import app.utils

UNRESOLVED_KEY = -1 

# --------------------------------------------------------------------------------------------------------------------
class SourceEpisode:
  def __init__(self, epNum, filename):
    app.utils.verifyType(epNum, int)
    app.utils.verifyType(filename, int)
    self.epNum_ = epNum
    self.filename_ = filename
    (dummy, self.extension_) = os.path.splitext(filename)
    
# --------------------------------------------------------------------------------------------------------------------
class DestinationEpisode:
  def __init__(self, epNum, epName):
    app.utils.verifyType(epNum, int)
    app.utils.verifyType(epName, str)
    self.epNum_ = epNum
    self.epName_ = epName

# --------------------------------------------------------------------------------------------------------------------
class EpisodeMap:
  def __init__(self):
    self.matches_ = {}
    self.unresolved_ = []
  
  def addItem(item):
    if item.epNum_ == UNRESOLVED_KEY:
      self.unresolved_.append(item)
    elif self.matches_.has_key(item.epNum_):
      app.utils.out("key already exists: %d" % item.epNum_, 1)
      self.unresolved_.append(item)
    else:
      self.matches_[item.epNum_] = item
    