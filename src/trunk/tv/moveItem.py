#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from app import utils
from tv import episode

# -----------------------------------------------------------------------------------
class MoveItem:
  READY          = 1
  MISSING_NEW    = 2
  MISSING_OLD    = 3
  UNKNOWN        = 4
  
  @staticmethod
  def typeStr(t):
    if t == MoveItem.READY:            return "READY"
    elif t == MoveItem.MISSING_NEW:    return "MISSING NEW"
    elif t == MoveItem.MISSING_OLD:    return "MISSING OLD"
    else:                              assert(False); return "UNKNOWN"      
  
  def __init__(self, source, destination):
    utils.verifyType(source, episode.SourceEpisode)
    utils.verify(source, episode.SourceEpisode)
    utils.verify(destination, episode.DestinationEpisode)
    self.source_ = source
    self.destination_ = destination
    mt = self.matchType()
    self.canMove_ = mt == MoveItem.READY #can execute
    self.canEdit_ = mt in (MoveItem.READY, MoveItem.MISSING_NEW) #can edit
    self.performMove_ = self.canMove_                             #will move
  
  def matchType(self):
    ret = None
    if self.destination_.epNum_ == episode.UNRESOLVED_KEY:
      ret = MoveItem.MISSING_NEW
    elif self.source_.epNum_ == episode.UNRESOLVED_KEY:
      ret = MoveItem.MISSING_OLD
    else:
      utils.verify(self.source_.epNum_ == self.destination_.epNum_, "Keys must be the same")
      ret = MoveItem.READY
    return ret
  
  def __copy__(self):
    return MoveItem(copy.copy(self.source_, copy(self.destination_)))
    
  def __eq__(self, other):
    return self.source_ == other.source_ and self.destination_ == other.destination_
    
  def __str__(self):
    return "[%d:%d] %s: %s -> %s" % (self.source_.epNum_, \
                                     self.destination_.epNum_, \
                                     MoveItem.typeStr(self.matchType()), \
                                     self.source_.filename_, \
                                     self.destination_.epName_)
