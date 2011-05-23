#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from common import utils
import episode

# -----------------------------------------------------------------------------------
class MoveItemCandidate:
  READY          = 1
  MISSING_NEW    = 2
  MISSING_OLD    = 3
  UNKNOWN        = 4
  
  @staticmethod
  def typeStr(t):
    if t == MoveItemCandidate.READY:            return "READY"
    elif t == MoveItemCandidate.MISSING_NEW:    return "MISSING NEW"
    elif t == MoveItemCandidate.MISSING_OLD:    return "MISSING OLD"
    else:                              assert(False); return "UNKNOWN"      
  
  def __init__(self, source, destination):
    utils.verifyType(source, episode.SourceEpisode)
    utils.verify(source, episode.SourceEpisode)
    utils.verify(destination, episode.DestinationEpisode)
    self.source_ = source
    self.destination_ = destination
    mt = self.matchType()
    self.canMove_ = mt == MoveItemCandidate.READY #can execute
    self.canEdit_ = mt in (MoveItemCandidate.READY, MoveItemCandidate.MISSING_NEW) #can edit
    self.performMove_ = self.canMove_                             #will move
  
  def matchType(self):
    ret = None
    if self.destination_.epNum_ == episode.UNRESOLVED_KEY:
      ret = MoveItemCandidate.MISSING_NEW
    elif self.source_.epNum_ == episode.UNRESOLVED_KEY:
      ret = MoveItemCandidate.MISSING_OLD
    else:
      utils.verify(self.source_.epNum_ == self.destination_.epNum_, "Keys must be the same")
      ret = MoveItemCandidate.READY
    return ret
  
  def __copy__(self):
    return MoveItemCandidate(copy.copy(self.source_, copy(self.destination_)))
    
  def __eq__(self, other):
    return self.source_ == other.source_ and self.destination_ == other.destination_
    
  def __str__(self):
    return "[%d:%d] %s: %s -> %s" % (self.source_.epNum_, \
                                     self.destination_.epNum_, \
                                     MoveItemCandidate.typeStr(self.matchType()), \
                                     self.source_.filename_, \
                                     self.destination_.epName_)
