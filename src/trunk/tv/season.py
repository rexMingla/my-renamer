#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import re

import tvdb_api

from app import utils

import episode
import extension
import moveItem
import outputFormat
import seasonHelper

# --------------------------------------------------------------------------------------------------------------------
class Season:
  OK                = 1
  UNBALANCED_FILES  = -1
  SEASON_UNRESOLVED = -2
  SEASON_NOT_FOUND  = -3
  UNKNOWN           = -4
  
  @staticmethod
  def resultStr(result):
    if   result == Season.OK:                return "OK"
    elif result == Season.UNBALANCED_FILES:  return "UNBALANCED FILES"
    elif result == Season.SEASON_NOT_FOUND:  return "SEASON NOT FOUND"
    elif result == Season.SEASON_UNRESOLVED: return "SEASON UNRESOLVED"
    else:                                    assert(false); return "UNKNOWN"
  
  def __str__(self):
    return "season: %s season #: %d status: %s" % (self.seasonName_, self.seasonNum_, Season.resultStr(self.status_))
    
  def __init__(self, seasonName, seasonNum, source, destination, format=outputFormat.DEFAULT_FORMAT):
    utils.verifyType(seasonName, str)
    utils.verifyType(seasonNum, int)
    utils.verifyType(source, episode.EpisodeMap)
    utils.verifyType(destination, episode.EpisodeMap)
    utils.verifyType(format, outputFormat.OutputFormat)
    
    self.seasonName_ = seasonName
    self.seasonNum_ = seasonNum
    self.source_ = source
    self.destination_ = destination
    self.resolveForFormat(format)
  
  def resolveForFormat(self, format):
    utils.verifyType(format, outputFormat.OutputFormat)
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
        utils.verifyType(destEp, episode.DestinationEpisode)
        inputMap = outputFormat.InputMap(self.seasonName_, self.seasonNum_, destEp.epNum_, destEp.epName_)
        destName = self.format_.outputToString(inputMap, sourceEp.extension_)
        if destName == sourceEp.filename_:
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
        self.moveItems_.append(moveItem.MoveItem(key, moveItem.MoveItem.MISSING_OLD, episode.UNRESOLVED_NAME, outname))
        
    for item in self.source_.unresolved_:
      self.moveItems_.append(moveItem.MoveItem(episode.UNRESOLVED_KEY, moveItem.MoveItem.UNRESOLVED_OLD, item.filename_, episode.UNRESOLVED_NAME))
      
    for item in self.destination_.unresolved_:
      #this should never really happen. TV show should always be resolved
      self.moveItems_.append(moveItem.MoveItem(episode.UNRESOLVED_KEY, moveItem.MoveItem.UNRESOLVED_NEW, episode.UNRESOLVED_NAME, episode.UNRESOLVED_NAME))
    
    self.moveItems_ = sorted(self.moveItems_, key=lambda item: item.key_)
          
  def _resolveStatus(self):
    if not self.destination_.matches_:
      self.status_ = Season.SEASON_NOT_FOUND
    elif len(self.moveItems_) == len(self.source_.matches_) and \
    len(self.moveItems_) == len(self.destination_.matches_) and \
    not self.destination_.unresolved_ and not self.destination_.unresolved_:
      self.status_ = Season.OK      
    else:
      self.status_ = Season.UNBALANCED_FILES      
 