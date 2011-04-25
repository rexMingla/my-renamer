#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from app import utils

# -----------------------------------------------------------------------------------
class MoveItem:
  READY          = 1
  DONE           = 2
  MISSING_NEW    = 3
  MISSING_OLD    = 4
  UNRESOLVED_NEW = 5
  UNRESOLVED_OLD = 6
  UNKNOWN        = 7
  
  @staticmethod
  def typeStr(t):
    if t == MoveItem.READY:            return "READY"
    elif t == MoveItem.DONE:           return "DONE"
    elif t == MoveItem.MISSING_NEW:    return "MISSING NEW"
    elif t == MoveItem.MISSING_OLD:    return "MISSING OLD"
    elif t == MoveItem.UNRESOLVED_NEW: return "UNRESOLVED NEW"
    elif t == MoveItem.UNRESOLVED_OLD: return "UNRESOLVED OLD"
    else:                              assert(False); return "UNKNOWN"      

  def __init__(self, key, matchType, oldName, newName):
    utils.verifyType(key, int)
    utils.verifyType(matchType, int)
    utils.verifyType(oldName, str)
    utils.verifyType(newName, str)
    self.key_ = key
    self.matchType_ = matchType
    self.oldName_ = oldName
    self.newName_ = newName
    self.canMove_ = matchType in (MoveItem.READY, MoveItem.DONE) #can execute
    self.canEdit_ = matchType in (MoveItem.READY, MoveItem.DONE, MoveItem.MISSING_NEW) #can execute
    self.performMove_ = self.canMove_                             #will move
  
  def __eq__(self, other):
    return self.key_ == other.key_ and self.matchType_ == other.matchType_ and \
           self.oldName_ == other.oldName_ and self.newName_ == other.newName_
    
  def __str__(self):
    return "[%d] %s: %s -> %s" % (self.key_, MoveItem.typeStr(self.matchType_), self.oldName_, self.newName_)
