#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import os
import re

from common import utils
import episode
import extension
import moveItemCandidate
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
    
  def __init__(self, seasonName, seasonNum, source, destination, inputFolder):
    utils.verifyType(seasonName, str)
    utils.verifyType(seasonNum, int)
    utils.verifyType(source, episode.EpisodeMap)
    utils.verifyType(destination, episode.EpisodeMap)
    utils.verifyType(inputFolder, str)
    
    self.seasonName_ = seasonName
    self.seasonNum_ = seasonNum
    self.source_ = source
    self.destination_ = destination
    self.performMove_ = True
    self.inputFolder_ = inputFolder
    self._resolveMoveItemCandidates()
    self._resolveStatus() 
    
  def setInputFolder(self, folder):
    utils.verifyType(folder, str)
    self.inputFolder_ = folder
    
  def updateDestination(self, seasonName, seasonNum, newDestination):
    utils.verifyType(seasonName, str)
    utils.verifyType(seasonNum, int)    
    utils.verifyType(newDestination, episode.EpisodeMap)
    self.seasonName_ = seasonName
    self.seasonNum_ = seasonNum
    self.destination_ = newDestination
    self._resolveMoveItemCandidates()
    self._resolveStatus()    
    
  def updateSource(self, newSource):
    utils.verifyType(newSource, episode.EpisodeMap)
    self.source_ = newSource
    self._resolveMoveItemCandidates()
    self._resolveStatus()    
          
  def _resolveMoveItemCandidates(self):
    self.moveItemCandidates_ = []
    for key in self.source_.matches_:
      destEp = None
      sourceEp = self.source_.matches_[key]
      if key in self.destination_.matches_:
        destEp = self.destination_.matches_[key]
        utils.verifyType(destEp, episode.DestinationEpisode)
      else:
        destEp = episode.DestinationEpisode.createUnresolvedDestination()
      self.moveItemCandidates_.append(moveItemCandidate.MoveItemCandidate(sourceEp, destEp))
      
    for key in self.destination_.matches_:
      if key not in self.source_.matches_:
        sourceEp = episode.SourceEpisode.createUnresolvedSource()
        destEp = self.destination_.matches_[key]
        self.moveItemCandidates_.append(moveItemCandidate.MoveItemCandidate(sourceEp, destEp))
        
    for item in self.source_.unresolved_:
      destEp = episode.DestinationEpisode.createUnresolvedDestination()
      self.moveItemCandidates_.append(moveItemCandidate.MoveItemCandidate(item, destEp))
      
    for item in self.destination_.unresolved_:
      sourceEp = episode.SourceEpisode.createUnresolvedSource()
      #this should never really happen. TV show should always be resolved
      self.moveItemCandidates_.append(moveItemCandidate.MoveItemCandidate(sourceEp, item))
    
    self.moveItemCandidates_ = sorted(self.moveItemCandidates_, key=lambda item: item.source_.epNum_)
          
  def _resolveStatus(self):
    if not self.destination_.matches_:
      self.status_ = Season.SEASON_NOT_FOUND
    elif len(self.moveItemCandidates_) == len(self.source_.matches_) and \
      len(self.moveItemCandidates_) == len(self.destination_.matches_) and \
      not self.destination_.unresolved_ and not self.destination_.unresolved_:
      self.status_ = Season.OK      
    else:
      self.status_ = Season.UNBALANCED_FILES      
 