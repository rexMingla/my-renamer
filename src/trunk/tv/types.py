#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Main class for working the tv seasons
# --------------------------------------------------------------------------------------------------------------------
import copy

from base import types as base_types
from common import utils

UNRESOLVED_KEY = -1
UNRESOLVED_NAME = "" 
  
# --------------------------------------------------------------------------------------------------------------------
class TvSearchParams(base_types.BaseInfoClientSearchParams):
  def __init__(self, showName, seasonNum):
    super(TvSearchParams, self).__init__()
    self.showName = showName
    self.seasonNum = seasonNum    
    
  def getKey(self):
    return utils.sanitizeString("{} ({})".format(self.showName, self.seasonNum))

  def toInfo(self):
    return SeasonInfo(self.showName, self.seasonNum)  
  
# --------------------------------------------------------------------------------------------------------------------
class EpisodeInfo(object):
  """ Information about an output file """
  def __init__(self, epNum, epName):
    super(EpisodeInfo, self).__init__()
    #utils.verifyType(epNum, int)
    #utils.verifyType(epName, basestring)
    self.epNum = epNum
    self.epName = epName
    
  @staticmethod
  def createUnresolvedEpisode():
    return EpisodeInfo(UNRESOLVED_KEY, UNRESOLVED_NAME)

  def __str__(self):
    return "<EpisodeInfo: #:{} name:{}>".format(self.epNum, self.epName)   

  def __eq__(self, other):
    return self.epNum == other.epNum and self.epName == other.epName
  
  #def __hash__(self):
  #  return hash(self.epNum) + hash(self.epName)

  def __copy__(self):
    return EpisodeInfo(self.epNum, self.epName)

# --------------------------------------------------------------------------------------------------------------------
class AdvancedEpisodeInfo(EpisodeInfo):
  """ Information about an output file """
  def __init__(self, showName, seasonNum, epNum, epName):
    super(AdvancedEpisodeInfo, self).__init__(epNum, epName)
    self.showName = showName
    self.seasonNum = seasonNum
    
  def __str__(self):
    return "<AdvancedEpisodeInfo: #:{} name:{}>".format(self.epNum, self.epName)   

  def __copy__(self):
    return AdvancedEpisodeInfo(self.showName, self.seasonNum, self.epNum, self.epName)
  
# -----------------------------------------------------------------------------------
class EpisodeRenameItem(base_types.BaseRenameItem):
  """ An item that may be selected for move/copy action. """
  READY          = 1
  MISSING_NEW    = 2
  MISSING_OLD    = 3
  UNKNOWN        = 4
  
  @staticmethod
  def typeStr(t):
    if t == EpisodeRenameItem.READY:            
      return "Ready"
    elif t == EpisodeRenameItem.MISSING_NEW:    
      return "No Matching Episode"
    elif t == EpisodeRenameItem.MISSING_OLD:    
      return "No Matching File"
    else: 
      assert(False)  
      return "Unknown"      
  
  def __init__(self, filename, info):
    super(EpisodeRenameItem, self).__init__(filename)
    #utils.verifyType(filename, basestring)
    #utils.verifyType(info, EpisodeInfo)
    self.info = info
    mt = self.matchType()
    self.canMove = mt == EpisodeRenameItem.READY #can execute
    self.canEdit = mt in (EpisodeRenameItem.READY, EpisodeRenameItem.MISSING_NEW) #can edit
    self.performMove = self.canMove                             #will move
  
  def matchType(self):
    ret = EpisodeRenameItem.MISSING_OLD
    if self.info.epNum == UNRESOLVED_KEY:
      ret = EpisodeRenameItem.MISSING_NEW
    elif self.filename:
      ret = EpisodeRenameItem.READY
    return ret
  
  def __copy__(self):
    return EpisodeRenameItem(self.filename, copy.copy(self.info))
    
  def __eq__(self, other):
    return self.filename == other.filename and self.info == other.info
    
  def __str__(self):
    return "[{}] {}: {} -> {}".format( self.filename, 
                                       self.info.epNum, 
                                       self.info.epName,
                                       EpisodeRenameItem.typeStr(self.matchType()) )
  
  def getInfo(self):
    return self.info

# -----------------------------------------------------------------------------------
class SourceFile(object):
  def __init__(self, epNum, filename):
    super(SourceFile, self).__init__()
    self.epNum = epNum
    self.filename = filename
    
  def __eq__(self, other):
    return other and self.epNum == other.epNum and self.filename == other.filename

# -----------------------------------------------------------------------------------
class SourceFiles(list):
  """ episode to filename map """
  def removeFile(self, filename):
    source = self.getItemByFilename(filename)
    assert(source)
    self.remove(source) 
        
  def getItemByEpisodeNum(self, epNum):
    for source in self:
      if source.epNum == epNum:
        return source
  
  def getItemByFilename(self, filename):
    for source in self:
      if source.filename == filename:
        return source
      
  def setEpisodeForFilename(self, key, filename):
    newEp = self.getItemByFilename(filename)
    oldEp = self.getItemByEpisodeNum(key)
    if not newEp or oldEp == newEp:
      return
    if oldEp:
      oldEp.epNum = UNRESOLVED_KEY
    newEp.epNum = key
      
  def append(self, item):
    if not isinstance(item, SourceFile):
      raise TypeError("item is not of type {}".format(SourceFile))
    if self.getItemByEpisodeNum(item.epNum):
      item.epNum = UNRESOLVED_KEY
    super(SourceFiles, self).append(item)
    
# -----------------------------------------------------------------------------------
class SeasonInfo(base_types.BaseInfo):
  """ contains list of """
  def __init__(self, showName="", seasonNum=""):
    super(SeasonInfo, self).__init__()
    self.showName = showName
    self.seasonNum = seasonNum
    self.episodes = []
    
  def getEpisodeByNum(self, epNum):
    for ep in self.episodes:
      if ep.epNum == epNum:
        return ep
    return EpisodeInfo.createUnresolvedEpisode()
    
  def getEpisodeByFilename(self, filename):
    for ep in self.episodes:
      if ep.filename == filename:
        return ep    
    
  def __copy__(self):
    ret = SeasonInfo(self.showName, self.seasonNum)
    ret.episodes = list(self.episodes)
    return ret
    
  def __str__(self):
    return "{} season {} - # episodes: {}".format(self.showName, self.seasonNum, len(self.episodes))

  def toSearchParams(self):
    return TvSearchParams(self.showName, self.seasonNum)
  
  def hasData(self):
    return bool(self.episodes)
  
# --------------------------------------------------------------------------------------------------------------------
class Season:
  """ Creates a list of episodeMoveItems given a source and destination input map. """
  OK                = 1
  UNBALANCED_FILES  = -1
  SEASON_UNRESOLVED = -2
  SEASON_NOT_FOUND  = -3
  UNKNOWN           = -4
  
  @staticmethod
  def resultStr(result):
    if   result == Season.OK:                
      return "Ok"
    elif result == Season.UNBALANCED_FILES:  
      return "Partially resolved"
    elif result == Season.SEASON_NOT_FOUND:  
      return "Season not found"
    elif result == Season.SEASON_UNRESOLVED: 
      return "Season unknown"
    else:                                    
      assert(False)
      return "Unknown"
  
  def __str__(self):
    if self.status == Season.SEASON_NOT_FOUND:
      return "Season: {} #: ???".format(self.info.showName)
    else:
      return "Season: {} #: {}".format(self.info.showName, self.info.seasonNum)
  
  def __init__(self, inputFolder, info, sources):
    #utils.verifyType(inputFolder, str)
    #utils.verifyType(sources, SourceFiles)
    #utils.verifyType(info, SeasonInfo)
    
    self.sources = sources
    self.info = info
    self.performMove = True #wtf? #HACK:
    self.inputFolder = inputFolder
    self.status = None
    self.episodeMoveItems = []
    self._resolveEpisodeMoveItems()
    self._resolveStatus() 
    
  def setInputFolder(self, folder):
    #utils.verifyType(folder, basestring)
    self.inputFolder = folder
    
  def removeSourceFile(self, f):
    #utils.verifyType(f, basestring)
    self.sources.removeFile(f)
    self.updateSource(self.sources)
    
  def updateSeasonInfo(self, info):
    #utils.verifyType(info, SeasonInfo)
    self.info = info
    self._resolveEpisodeMoveItems()
    self._resolveStatus()    
    
  def updateSource(self, sources):
    #utils.verifyType(sources, SourceFiles)
    self.sources = sources
    self._resolveEpisodeMoveItems()
    self._resolveStatus()    
          
  def _resolveEpisodeMoveItems(self):
    self.episodeMoveItems = []
    tempSeasonInfo = copy.copy(self.info)
    takenKeys = [] #dodgy...
    for source in self.sources:
      destEp = EpisodeInfo.createUnresolvedEpisode()
      if source.epNum != UNRESOLVED_KEY and not source.epNum in takenKeys:
        destEp = tempSeasonInfo.getEpisodeByNum(source.epNum)
        if destEp.epNum != UNRESOLVED_KEY:
          tempSeasonInfo.episodes.remove(destEp)
        takenKeys.append(source.epNum)
      destEp = AdvancedEpisodeInfo(self.info.showName, self.info.seasonNum, destEp.epNum, destEp.epName)
      self.episodeMoveItems.append(EpisodeRenameItem(source.filename, destEp))
      
    for ep in tempSeasonInfo.episodes:
      self.episodeMoveItems.append(EpisodeRenameItem("", AdvancedEpisodeInfo(self.info.showName, self.info.seasonNum, 
                                                                             ep.epNum, ep.epName)))
        
    self.episodeMoveItems = sorted(self.episodeMoveItems, key=lambda item: item.info.epNum)
          
  def _resolveStatus(self):
    if not self.info:
      self.status = Season.SEASON_NOT_FOUND
    if all([item.info.epNum != UNRESOLVED_KEY and item.filename for item in self.episodeMoveItems]):
      self.status = Season.OK      
    else:
      self.status = Season.UNBALANCED_FILES  
  
  def setEpisodeForFilename(self, key, filename):
    self.sources.setEpisodeForFilename(key, filename)
    self.updateSource(self.sources)
      
  def getInfo(self):
    return self.info

  def isValid(self):
    return self.info.hasData()
 