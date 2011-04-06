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
  def typeStr(type):
    if type == MoveItem.READY:   return "READY"
    elif type == MoveItem.DONE:  return "DONE"
    elif type == MoveItem.M_NEW: return "MISSING NEW"
    elif type == MoveItem.M_OLD: return "MISSING OLD"
    elif type == MoveItem.U_NEW: return "UNRESOLVED NEW"
    elif type == MoveItem.U_OLD: return "UNRESOLVED OLD"
    else:                        assert(False); return "UNKNOWN"      
  
  def __init__(self, key, matchType, oldName, newName):
    utils.verifyType(key, str)
    utils.verifyType(matchType, int)
    utils.verifyType(oldName, str)
    utils.verifyType(newName, str)
    self.key_ = key
    self.matchType_ = matchType
    self.oldName_ = oldName
    self.newName_ = newName
      
  def __str__(self):
    return "[%s] %s: %s -> %s" % (self.key_, MoveItem.typeStr(self.matchType_), self.oldName_, self.newName_)
