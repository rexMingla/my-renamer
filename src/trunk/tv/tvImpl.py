#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Main class for working the tv seasons
# --------------------------------------------------------------------------------------------------------------------
import copy
import os

from common import infoClient
from common import fileHelper
from common import renamer
from common import utils

UNRESOLVED_KEY = -1
UNRESOLVED_NAME = "" 

# --------------------------------------------------------------------------------------------------------------------
class SourceEpisode(object):
  """ Information about an input file """
  def __init__(self, epNum, filename):
    utils.verifyType(epNum, int)
    utils.verifyType(filename, str)
    self.epNum = epNum
    self.filename = filename
    self.fileSize = fileHelper.FileHelper.getFileSize(filename)
    self.ext = fileHelper.FileHelper.extension(filename)
    
  @staticmethod
  def createUnresolvedSource():
    return SourceEpisode(UNRESOLVED_KEY, UNRESOLVED_NAME)

  def __str__(self):
    return "<SourceEpisode: #:{} name:{}>".format(self.epNum, self.filename)   
    
  def __eq__(self, other):
    return self.epNum == other.epNum and self.filename == other.filename
  
  def __hash__(self):
    return hash(self.epNum) + hash(self.filename)
  
  def __copy__(self):
    return SourceEpisode(self.epNum, self.filename)
  
# --------------------------------------------------------------------------------------------------------------------
class DestinationEpisode(object):
  """ Information about an output file """
  def __init__(self, epNum, epName):
    utils.verifyType(epNum, int)
    utils.verifyType(epName, str)
    self.epNum = epNum
    self.epName = epName
    
  @staticmethod
  def createUnresolvedDestination():
    return DestinationEpisode(UNRESOLVED_KEY, UNRESOLVED_NAME)

  def __str__(self):
    return "<DestinationEpisode: #:{} name:{}>".format(self.epNum, self.epName)   

  def __eq__(self, other):
    return self.epNum == other.epNum and self.epName == other.epName
  
  def __hash__(self):
    return hash(self.epNum) + hash(self.epName)

  def __copy__(self):
    return DestinationEpisode(self.epNum, self.epName)
  
# --------------------------------------------------------------------------------------------------------------------
class BaseEpisodeMap(object):
  """ 
  Collection of input or output files mapped by key. In the case of duplicate keys, the first is accepted 
  and all duplicates thereafter are considered unresolved.
  """
  def __init__(self):
    super(BaseEpisodeMap, self).__init__()
    self.matches = {}
    self.unresolved = []
  
  def hasData(self):
    return bool(len(self.matches) or len(self.unresolved))
  
  def addItem(self, item):
    utils.verify((isinstance(item, SourceEpisode) and isinstance(self, SourceEpisodeMap)) or 
                 (isinstance(item, DestinationEpisode) and isinstance(self, DestinationEpisodeMap)), "wrong type!")
    epNumStr = str(item.epNum)
    if item.epNum == UNRESOLVED_KEY:
      self.unresolved.append(item)
    elif epNumStr in self.matches:
      utils.logNotSet("key already exists: {}".format(item.epNum), 1)
      tempItem = copy.copy(item)
      tempItem.epNum = UNRESOLVED_KEY
      self.unresolved.append(tempItem)
    else:
      self.matches[epNumStr] = item #jsonpickle converts dicts with int keys to string keys :(
  
  def setKeyForFilename(self, newKey, filename):
    """ Set a new key for a given filename, performing required sanitization in the event of key collisions. """
    utils.verifyType(newKey, int)
    utils.verifyType(filename, str)    
    
    sourceEp = next( (source for key, source in self.matches.items() if source.filename == filename), None)
    sourceEp = sourceEp or next( (ep for ep in self.unresolved if ep.filename == filename), None)
    if not sourceEp or sourceEp.epNum == newKey:
      return
    
    oldEp = None
    newKeyStr = str(newKey)
    if newKeyStr in self.matches:
      oldEp = self.matches[newKeyStr]
      del self.matches[newKeyStr]
      
    self.removeSoureFile(sourceEp.filename)
    sourceEp.epNum = newKey
    self.addItem(sourceEp)
    if oldEp:
      self.addItem(oldEp)
        
  def removeSoureFile(self, filename):
    utils.verifyType(filename, str)
    self.matches = dict( (k, v) for k, v in self.matches.items() if filename != v.filename)
    self.unresolved = [v for v in self.unresolved if filename != v.filename]

  def __eq__(self, other):
    utils.verifyType(other, BaseEpisodeMap)
    return other and utils.listCompare(self.unresolved, other.unresolved) and utils.dictCompare(self.matches, other.matches)
  
  def __str__(self):
    return "<BaseEpisodeMap: #matches:{} #unresolved:{}>".format(len(self.matches), len(self.unresolved))
  
  def __copy__(self):
    raise NotImplementedError("Base.__copy__ not implemented")
  
class SourceEpisodeMap(BaseEpisodeMap):
  def __copy__(self):
    ret = SourceEpisodeMap()
    for key, value in self.matches.items():
      ret.matches[key] = copy.copy(value)
    ret.unresolved = map(copy.copy, self.unresolved)
    return ret

# -----------------------------------------------------------------------------------
class DestinationEpisodeMap(BaseEpisodeMap, infoClient.BaseInfo):
  def __init__(self, showName="", seasonNum=""):
    super(DestinationEpisodeMap, self).__init__()
    super(infoClient.BaseInfo, self).__init__()
    self.showName = showName
    self.seasonNum = seasonNum 
    
  def __copy__(self):
    ret = DestinationEpisodeMap(self.showName, self.seasonNum)
    for key, value in self.matches.items():
      ret.matches[key] = copy.copy(value)
    ret.unresolved = map(copy.copy, self.unresolved)
    return ret
    
  def __str__(self):
    return "{} season {} - # episodes: {}".format(self.showName, self.seasonNum, len(self.matches))
  
  def toSearchParams(self):
    return tvInfoClient.TvSearchParams(self.showName, self.seasonNum)
  
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
    utils.verifyType(source, SourceEpisode)
    utils.verifyType(destination, DestinationEpisode)
    self.source = source
    self.destination = destination
    mt = self.matchType()
    self.canMove = mt == MoveItemCandidate.READY #can execute
    self.canEdit = mt in (MoveItemCandidate.READY, MoveItemCandidate.MISSING_NEW) #can edit
    self.performMove = self.canMove                             #will move
  
  def matchType(self):
    ret = None
    if self.destination.epNum == UNRESOLVED_KEY:
      ret = MoveItemCandidate.MISSING_NEW
    elif self.source.epNum == UNRESOLVED_KEY:
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

# --------------------------------------------------------------------------------------------------------------------
class Season(renamer.BaseRenameItem):
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
    return "season: {} season #: {} # eps: {}".format(self.seasonName, self.seasonNum, Season.resultStr(self.status))
  
  def __init__(self, seasonName, seasonNum, source, destination, inputFolder):
    utils.verifyType(seasonName, str)
    utils.verifyType(seasonNum, int)
    utils.verifyType(source, SourceEpisodeMap)
    utils.verifyType(destination, DestinationEpisodeMap)
    utils.verifyType(inputFolder, str)
    
    self.seasonName = seasonName
    self.seasonNum = seasonNum
    self.source = source
    self.destination = destination
    self.performMove = True
    self.inputFolder = inputFolder
    self._resolveMoveItemCandidates()
    self._resolveStatus() 
    
  def __str__(self):
    return 
    
  def setInputFolder(self, folder):
    utils.verifyType(folder, str)
    self.inputFolder = folder
    
  def removeSourceFile(self, f):
    utils.verifyType(f, str)
    self.source.removeFile(f)
    self.updateSource(self.source)
    
  def updateDestination(self, newDestination):
    utils.verifyType(newDestination, DestinationEpisodeMap)
    self.seasonName = newDestination.showName
    self.seasonNum = newDestination.seasonNum
    self.destination = newDestination
    self._resolveMoveItemCandidates()
    self._resolveStatus()    
    
  def updateSource(self, newSource):
    utils.verifyType(newSource, SourceEpisodeMap)
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
        utils.verifyType(destEp, DestinationEpisode)
      else:
        destEp = DestinationEpisode.createUnresolvedDestination()
      self.moveItemCandidates.append(MoveItemCandidate(sourceEp, destEp))
      
    for key in self.destination.matches:
      if key not in self.source.matches:
        sourceEp = SourceEpisode.createUnresolvedSource()
        destEp = self.destination.matches[key]
        self.moveItemCandidates.append(MoveItemCandidate(sourceEp, destEp))
        
    for item in self.source.unresolved:
      destEp = DestinationEpisode.createUnresolvedDestination()
      self.moveItemCandidates.append(MoveItemCandidate(item, destEp))
      
    for item in self.destination.unresolved:
      sourceEp = SourceEpisode.createUnresolvedSource()
      #this should never really happen. TV show should always be resolved
      self.moveItemCandidates.append(MoveItemCandidate(sourceEp, item))
    
    self.moveItemCandidates = sorted(self.moveItemCandidates, key=lambda item: max(item.destination.epNum, item.source.epNum))
          
  def _resolveStatus(self):
    if not self.destination.matches:
      self.status = Season.SEASON_NOT_FOUND
    elif len(self.moveItemCandidates) == len(self.source.matches) and \
      len(self.moveItemCandidates) == len(self.destination.matches) and \
      not self.destination.unresolved and not self.destination.unresolved:
      self.status = Season.OK      
    else:
      self.status = Season.UNBALANCED_FILES   
      
  def itemToInfo(self):
    return self.destination

  
 