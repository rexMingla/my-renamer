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
import re

import tvdb_api

import app.utils
import episode
import extension
import outputFormat
import seasonHelper

# --------------------------------------------------------------------------------------------------------------------
class Season:
  OK                          = 1
  UNBALANCED_FILES            = -1
  SEASON_UNRESOLVED           = -4
  UNKNOWN                     = -5
  
  @staticmethod
  def resultStr(result):
    if   result == Season.OK:                return "OK"
    elif result == Season.UNBALANCED_FILES:  return "UNBALANCED_FILES"
    elif result == Season.SEASON_UNRESOLVED: return "SEASON_UNRESOLVED"
    else:                                    assert(false); return "UNKNOWN"
  
  def __init__(self, seasonName, seasonNum, source, destination, format):
    app.utils.verifyType(showName, str)
    app.utils.verifyType(seasonNum, int)
    app.utils.verifyType(source, episode.EpisodeMap)
    app.utils.verifyType(destination, episode.EpisodeMap)
    app.utils.verifyType(format, outputFormat.OutputFormat)
    
    self.seasonName_ = seasonName
    self.seasonNum_ = seasonNum
    self.source_ = source
    self.destination_ = destination
    self.format_ = format
    
    self._resolveMoveItems()
    self._resolveStatus()
    
  def _resolveMoveItems(self):
    self.moveItems_ = []
    for key in self.source_.matches_:
      state = moveItem.MoveItem.MISSING_NEW
      destName = ""
      sourceEp = self.source_.matches_[key]
      if key in self.destination_.matches_:
        destEp = self.destination_.matches_[key]
        app.utils.verifyType(destEp, episode.DestinationEpisode)
        inputMap = outputFormat.InputMap(self.seasonName_, self.seasonNum_, destEp.epNum_, destEp.epName_)
        outname = self.format_.outputToString(inputMap, sourceEp.extension_)
        if outname == sourceEp.self.filename_:
          state = moveItem.MoveItem.DONE
        else:
          state = moveItem.MoveItem.READY          
      else:
        state = moveItem.MoveItem.MISSING_NEW
      self.moveItems_.append(moveItem.MoveItem(key, state, sourceEp.filename_, destName))
      
    for key in self.destination_.matches_:
      if key not in self.source_.matches_:
        destEp = self.destination_.matches_[key]
        inputMap = outputFormat.InputMap(self.seasonName_, self.seasonNum_, destEp.epNum_, destEp.epName_)
        outname = self.format_.outputToString(inputMap, ".avi")
        self.moveItems_.append(moveItem.MoveItem(key, moveItem.MoveItem.MISSING_OLD, "", outname))
        
    for item in self.source_.unresolved_:
      self.moveItems_.append(moveItem.MoveItem(episode.UNRESOLVED_KEY, moveItem.MoveItem.UNRESOLVED_OLD, item.filename_, ""))
      
    for item in self.destination_.unresolved_:
      inputMap = outputFormat.InputMap(self.seasonName_, self.seasonNum_, destEp.epNum_, destEp.epName_)
      outname = self.format_.outputToString(inputMap, ".avi")      
      self.moveItems_.append(moveItem.MoveItem(episode.UNRESOLVED_KEY, moveItem.MoveItem.UNRESOLVED_NEW, "", outname))
    
    self.moveItems_ = sorted(self.moveItems_, key=lambda item: item.key_)
          
  def _resolveStatus(self, outputFormat):
    if len(self.moveItems_) == len(self.source_.moveItems_) and \
       len(self.moveItems_) == len(self.destination_.moveItems_):
      self.status_ = Season.OK      
    if not self.destination_.matches_ and not self.destination_.unresolved_:
      self.status_ = Season.SEASON_NOT_FOUND
    else:
      self.status_ = Season.UNBALANCED_FILES      
 