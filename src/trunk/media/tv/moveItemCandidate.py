#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: An item that may be selected for move/copy action
# --------------------------------------------------------------------------------------------------------------------
import copy

from common import utils
import episode

# -----------------------------------------------------------------------------------
class MoveItemCandidate:
  """ An item that may be selected for move/copy action. """
  READY          = 1
  MISSING_NEW    = 2
  MISSING_OLD    = 3
  UNKNOWN        = 4
  
  @staticmethod
  def typeStr(t):
    if t == MoveItemCandidate.READY:            return "Ready"
    elif t == MoveItemCandidate.MISSING_NEW:    return "No Matching Episode"
    elif t == MoveItemCandidate.MISSING_OLD:    return "No Matching File"
    else:                              assert(False); return "Unknown"      
  
  def __init__(self, source, destination):
    utils.verifyType(source, episode.SourceEpisode)
    utils.verifyType(destination, episode.DestinationEpisode)
    self.source = source
    self.destination = destination
    mt = self.matchType()
    self.canMove = mt == MoveItemCandidate.READY #can execute
    self.canEdit = mt in (MoveItemCandidate.READY, MoveItemCandidate.MISSING_NEW) #can edit
    self.performMove = self.canMove                             #will move
  
  def matchType(self):
    ret = None
    if self.destination.epNum == episode.UNRESOLVED_KEY:
      ret = MoveItemCandidate.MISSING_NEW
    elif self.source.epNum == episode.UNRESOLVED_KEY:
      ret = MoveItemCandidate.MISSING_OLD
    else:
      utils.verify(self.source.epNum == self.destination.epNum, "Keys must be the same")
      ret = MoveItemCandidate.READY
    return ret
  
  def __copy__(self):
    return MoveItemCandidate(copy.copy(self.source), copy.copy(self.destination))
    
  def __eq__(self, other):
    return self.source == other.source and self.destination == other.destination
    
  def __str__(self):
    return "[{}:{}] {}: {} -> {}".format( self.source.epNum, 
                                          self.destination.epNum, 
                                          MoveItemCandidate.typeStr(self.matchType()), 
                                          self.source.filename, 
                                          self.destination.epName)
