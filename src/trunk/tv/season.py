#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Main class for working the tv seasons
# --------------------------------------------------------------------------------------------------------------------
from common import utils

import episode
import moveItemCandidate
import seasonHelper

# --------------------------------------------------------------------------------------------------------------------
class Season:
  """ Creates a list of moveItemCandidates given a source and destination input map. """
  OK                = 1
  UNBALANCED_FILES  = -1
  SEASON_UNRESOLVED = -2
  SEASON_NOT_FOUND  = -3
  UNKNOWN           = -4
  
  @staticmethod
  def resultStr(result):
    if   result == Season.OK:                return "Ok"
    elif result == Season.UNBALANCED_FILES:  return "Partially resolved"
    elif result == Season.SEASON_NOT_FOUND:  return "Season not found"
    elif result == Season.SEASON_UNRESOLVED: return "Season unknown"
    else:                                    assert(false); return "Unknown"
  
  def __str__(self):
    return "season: {} season #: {} status: {}".format(self.seasonName, self.seasonNum, Season.resultStr(self.status))
  
  def __init__(self, seasonName, seasonNum, source, destination, inputFolder):
    utils.verifyType(seasonName, str)
    utils.verifyType(seasonNum, int)
    utils.verifyType(source, episode.EpisodeMap)
    utils.verifyType(destination, episode.EpisodeMap)
    utils.verifyType(inputFolder, str)
    
    self.seasonName = seasonName
    self.seasonNum = seasonNum
    self.source = source
    self.destination = destination
    self.performMove = True
    self.inputFolder = inputFolder
    self._resolveMoveItemCandidates()
    self._resolveStatus() 
    
  def setInputFolder(self, folder):
    utils.verifyType(folder, str)
    self.inputFolder = folder
    
  def updateDestination(self, seasonName, seasonNum, newDestination):
    utils.verifyType(seasonName, str)
    utils.verifyType(seasonNum, int)    
    utils.verifyType(newDestination, episode.EpisodeMap)
    self.seasonName = seasonName
    self.seasonNum = seasonNum
    self.destination = newDestination
    self._resolveMoveItemCandidates()
    self._resolveStatus()    
    
  def updateSource(self, newSource):
    utils.verifyType(newSource, episode.EpisodeMap)
    self.source = newSource
    self._resolveMoveItemCandidates()
    self._resolveStatus()    
          
  def _resolveMoveItemCandidates(self):
    self.moveItemCandidates = []
    for key in self.source.matches:
      destEp = None
      sourceEp = self.source.matches[key]
      if key in self.destination.matches:
        destEp = self.destination.matches[key]
        utils.verifyType(destEp, episode.DestinationEpisode)
      else:
        destEp = episode.DestinationEpisode.createUnresolvedDestination()
      self.moveItemCandidates.append(moveItemCandidate.MoveItemCandidate(sourceEp, destEp))
      
    for key in self.destination.matches:
      if key not in self.source.matches:
        sourceEp = episode.SourceEpisode.createUnresolvedSource()
        destEp = self.destination.matches[key]
        self.moveItemCandidates.append(moveItemCandidate.MoveItemCandidate(sourceEp, destEp))
        
    for item in self.source.unresolved:
      destEp = episode.DestinationEpisode.createUnresolvedDestination()
      self.moveItemCandidates.append(moveItemCandidate.MoveItemCandidate(item, destEp))
      
    for item in self.destination.unresolved:
      sourceEp = episode.SourceEpisode.createUnresolvedSource()
      #this should never really happen. TV show should always be resolved
      self.moveItemCandidates.append(moveItemCandidate.MoveItemCandidate(sourceEp, item))
    
    self.moveItemCandidates = sorted(self.moveItemCandidates, key=lambda item: item.source.epNum)
          
  def _resolveStatus(self):
    if not self.destination.matches:
      self.status = Season.SEASON_NOT_FOUND
    elif len(self.moveItemCandidates) == len(self.source.matches) and \
      len(self.moveItemCandidates) == len(self.destination.matches) and \
      not self.destination.unresolved and not self.destination.unresolved:
      self.status = Season.OK      
    else:
      self.status = Season.UNBALANCED_FILES      
 