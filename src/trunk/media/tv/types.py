#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Main class for working the tv seasons
# --------------------------------------------------------------------------------------------------------------------
import copy
import os

from media.base import types as base_types
from common import utils

UNRESOLVED_KEY = -1
UNRESOLVED_NAME = ""

# --------------------------------------------------------------------------------------------------------------------
class TvSearchParams(base_types.BaseSearchParams):
  def __init__(self, show_name, season_num):
    super(TvSearchParams, self).__init__()
    self.show_name = show_name
    self.season_num = season_num

  def getKey(self):
    return utils.sanitizeString("{} ({})".format(self.show_name, self.season_num))

  def getInfo(self):
    return SeasonInfo(self.show_name, self.season_num)

# --------------------------------------------------------------------------------------------------------------------
class EpisodeInfo(base_types.BaseInfo):
  """ Information about an output file """
  def __init__(self, ep_num, ep_name):
    super(EpisodeInfo, self).__init__(base_types.TV_MODE)
    #utils.verifyType(ep_num, int)
    #utils.verifyType(ep_name, basestring)
    self.ep_num = ep_num
    self.ep_name = ep_name

  @staticmethod
  def createUnresolvedEpisode():
    return EpisodeInfo(UNRESOLVED_KEY, UNRESOLVED_NAME)

  def __str__(self):
    return "<EpisodeInfo: #:{} name:{}>".format(self.ep_num, self.ep_name)

  def __eq__(self, other):
    return self.ep_num == other.ep_num and self.ep_name == other.ep_name

  #def __hash__(self):
  #  return hash(self.ep_num) + hash(self.ep_name)

  def __copy__(self):
    return EpisodeInfo(self.ep_num, self.ep_name)

# --------------------------------------------------------------------------------------------------------------------
class AdvancedEpisodeInfo(EpisodeInfo):
  """ Information about an output file """
  def __init__(self, show_name, season_num, ep_num, ep_name):
    super(AdvancedEpisodeInfo, self).__init__(ep_num, ep_name)
    self.show_name = show_name
    self.season_num = season_num

  def __str__(self):
    return "<AdvancedEpisodeInfo: #:{} name:{}>".format(self.ep_num, self.ep_name)

  def __copy__(self):
    return AdvancedEpisodeInfo(self.show_name, self.season_num, self.ep_num, self.ep_name)

# -----------------------------------------------------------------------------------
class EpisodeRenameItem(base_types.BaseRenameItem):
  """ An item that may be selected for move/copy action. """
  MISSING_NEW    = "No Matching Episode"
  MISSING_OLD    = "No Matching File"

  def __init__(self, filename, info, is_enabled=True):
    super(EpisodeRenameItem, self).__init__(filename, info, is_enabled)
    
  def getStatus(self):
    ret = EpisodeRenameItem.MISSING_OLD
    if self._info.ep_num == UNRESOLVED_KEY:
      ret = EpisodeRenameItem.MISSING_NEW
    elif self.filename:
      ret = EpisodeRenameItem.READY
    return ret
  
  def __copy__(self):
    return EpisodeRenameItem(self.filename, copy.copy(self._info), self.is_enabled)

  def __eq__(self, other):
    return self.filename == other.filename and self._info == other.getInfo()

  def __str__(self):
    return "[{}] {}: {} -> {}".format(self.filename, self.info.ep_num, self.info.ep_name, self.getStatus())

# -----------------------------------------------------------------------------------
class SourceFile(object):
  def __init__(self, ep_num, filename):
    super(SourceFile, self).__init__()
    self.ep_num = ep_num
    self.filename = filename

  def __eq__(self, other):
    return other and self.ep_num == other.ep_num and self.filename == other.filename

# -----------------------------------------------------------------------------------
class SourceFiles(list):
  """ episode to filename map """
  def removeFile(self, filename):
    source = self.getItemByFilename(filename)
    assert(source)
    self.remove(source)

  def getItemByEpisodeNum(self, ep_num):
    for source in self:
      if source.ep_num == ep_num:
        return source

  def getItemByFilename(self, filename):
    for source in self:
      if source.filename == filename:
        return source

  def setEpisodeForFilename(self, key, filename):
    new_ep = self.getItemByFilename(filename)
    old_ep = self.getItemByEpisodeNum(key)
    if not new_ep or old_ep == new_ep:
      return
    if old_ep:
      old_ep.ep_num = UNRESOLVED_KEY
    new_ep.ep_num = key

  def append(self, item):
    if not isinstance(item, SourceFile):
      raise TypeError("item is not of type {}".format(SourceFile))
    if self.getItemByEpisodeNum(item.ep_num):
      item.ep_num = UNRESOLVED_KEY
    super(SourceFiles, self).append(item)

# -----------------------------------------------------------------------------------
class SeasonInfo(base_types.BaseInfo):
  """ contains list of """
  def __init__(self, show_name="", season_num=""):
    super(SeasonInfo, self).__init__(base_types.TV_MODE)
    self.show_name = show_name
    self.season_num = season_num
    self.episodes = []

  def getEpisodeByEpisodeNum(self, ep_num):
    for episode in self.episodes:
      if episode.ep_num == ep_num:
        return episode
    return EpisodeInfo.createUnresolvedEpisode()

  def __copy__(self):
    ret = SeasonInfo(self.show_name, self.season_num)
    ret.episodes = list(self.episodes)
    return ret

  def __str__(self):
    return "{} season {} - # episodes: {}".format(self.show_name, self.season_num, len(self.episodes))

  def getSearchParams(self):
    return TvSearchParams(self.show_name, self.season_num)
  
# --------------------------------------------------------------------------------------------------------------------
class Season(object):
  """ Creates a list of episode_move_items given a source and destination input map. """
  UNBALANCED_FILES  = "Partially resolved"
  SEASON_NOT_FOUND  = "Season not found"

  def __init__(self, input_folder, info, sources):
    super(Season, self).__init__()
    self.sources = sources
    self._info = info
    self.input_folder = input_folder
    if len(self.input_folder) > 1:
      self.input_folder.rstrip(os.path.sep)
    self.episode_move_items = []
    self._resolveEpisodeMoveItems()
    
  def removeSourceFile(self, filename):
    #utils.verifyType(f, basestring)
    self.sources.removeFile(filename)
    self.updateSource(self.sources)
    
  def getInfo(self):
    #HACK: remove this. make use the renamer base class
    return self._info

  def setInfo(self, info):
    #utils.verifyType(info, SeasonInfo)
    self._info = info
    self._resolveEpisodeMoveItems()

  def updateSource(self, sources):
    #utils.verifyType(sources, SourceFiles)
    self.sources = sources
    self._resolveEpisodeMoveItems()

  def _resolveEpisodeMoveItems(self):
    self.episode_move_items = []
    temp_season_info = copy.copy(self.getInfo())
    taken_keys = [] #dodgy...
    info = self.getInfo()
    for source in self.sources:
      dest_ep = EpisodeInfo.createUnresolvedEpisode()
      if source.ep_num != UNRESOLVED_KEY and not source.ep_num in taken_keys:
        dest_ep = temp_season_info.getEpisodeByEpisodeNum(source.ep_num)
        if dest_ep.ep_num != UNRESOLVED_KEY:
          temp_season_info.episodes.remove(dest_ep)
        taken_keys.append(source.ep_num)
      dest_ep = AdvancedEpisodeInfo(info.show_name, info.season_num, dest_ep.ep_num, dest_ep.ep_name)
      self.episode_move_items.append(EpisodeRenameItem(source.filename, dest_ep))

    for episode in temp_season_info.episodes:
      self.episode_move_items.append(EpisodeRenameItem("", 
          AdvancedEpisodeInfo(info.show_name, info.season_num, episode.ep_num, episode.ep_name)))

    self.episode_move_items = sorted(self.episode_move_items, key=lambda item: item.getInfo().ep_num)

  def getStatus(self):
    status = Season.UNBALANCED_FILES
    if not self._info.isValid():
      status = Season.SEASON_NOT_FOUND
    elif all([item.getInfo().ep_num != UNRESOLVED_KEY and item.filename for item in self.episode_move_items]):
      status = "Ready" #TODO: Season.READY
    return status
  
  def setEpisodeForFilename(self, key, filename):
    self.sources.setEpisodeForFilename(key, filename)
    self.updateSource(self.sources)

  def __str__(self):
    info = self.getInfo()
    show_name = info.show_name or "???"
    season_num = info.season_num if info.season_num != UNRESOLVED_KEY else "???"
    return "Season: {} #: {}".format(show_name, season_num)
