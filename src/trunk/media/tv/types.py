#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Main class for working the tv seasons
# --------------------------------------------------------------------------------------------------------------------
import copy

from media.base import types as base_types
from common import utils

UNRESOLVED_KEY = -1
UNRESOLVED_NAME = "" 
  
# --------------------------------------------------------------------------------------------------------------------
class TvSearchParams(base_types.BaseInfoClientSearchParams):
  def __init__(self, show_name, season_num):
    super(TvSearchParams, self).__init__()
    self.show_name = show_name
    self.season_num = season_num    
    
  def get_key(self):
    return utils.sanitize_string("{} ({})".format(self.show_name, self.season_num))

  def to_info(self):
    return SeasonInfo(self.show_name, self.season_num)  
  
# --------------------------------------------------------------------------------------------------------------------
class EpisodeInfo(object):
  """ Information about an output file """
  def __init__(self, ep_num, ep_name):
    super(EpisodeInfo, self).__init__()
    #utils.verify_type(ep_num, int)
    #utils.verify_type(ep_name, basestring)
    self.ep_num = ep_num
    self.ep_name = ep_name
    
  @staticmethod
  def create_unresolved_episode():
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
  READY          = 1
  MISSING_NEW    = 2
  MISSING_OLD    = 3
  UNKNOWN        = 4
  
  @staticmethod
  def type_str(text):
    if text == EpisodeRenameItem.READY:            
      return "Ready"
    elif text == EpisodeRenameItem.MISSING_NEW:    
      return "No Matching Episode"
    elif text == EpisodeRenameItem.MISSING_OLD:    
      return "No Matching File"
    else: 
      assert(False)  
      return "Unknown"      
  
  def __init__(self, filename, info):
    super(EpisodeRenameItem, self).__init__(filename)
    #utils.verify_type(filename, basestring)
    #utils.verify_type(info, EpisodeInfo)
    self.info = info
    match_text = self.match_type()
    self.can_move = match_text == EpisodeRenameItem.READY #can execute
    self.can_edit = match_text in (EpisodeRenameItem.READY, EpisodeRenameItem.MISSING_NEW) #can edit
    self.perform_move = self.can_move                             #will move
  
  def match_type(self):
    ret = EpisodeRenameItem.MISSING_OLD
    if self.info.ep_num == UNRESOLVED_KEY:
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
                                       self.info.ep_num, 
                                       self.info.ep_name,
                                       EpisodeRenameItem.type_str(self.match_type()) )
  
  def get_info(self):
    return self.info

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
  def remove_file(self, filename):
    source = self.get_item_by_filename(filename)
    assert(source)
    self.remove(source) 
        
  def get_item_by_episode_num(self, ep_num):
    for source in self:
      if source.ep_num == ep_num:
        return source
  
  def get_item_by_filename(self, filename):
    for source in self:
      if source.filename == filename:
        return source
      
  def set_episode_for_filename(self, key, filename):
    new_ep = self.get_item_by_filename(filename)
    old_ep = self.get_item_by_episode_num(key)
    if not new_ep or old_ep == new_ep:
      return
    if old_ep:
      old_ep.ep_num = UNRESOLVED_KEY
    new_ep.ep_num = key
      
  def append(self, item):
    if not isinstance(item, SourceFile):
      raise TypeError("item is not of type {}".format(SourceFile))
    if self.get_item_by_episode_num(item.ep_num):
      item.ep_num = UNRESOLVED_KEY
    super(SourceFiles, self).append(item)
    
# -----------------------------------------------------------------------------------
class SeasonInfo(base_types.BaseInfo):
  """ contains list of """
  def __init__(self, show_name="", season_num=""):
    super(SeasonInfo, self).__init__()
    self.show_name = show_name
    self.season_num = season_num
    self.episodes = []
    
  def get_episode_by_episode_num(self, ep_num):
    for episode in self.episodes:
      if episode.ep_num == ep_num:
        return episode
    return EpisodeInfo.create_unresolved_episode()
    
  #def get_episode_by_filename(self, filename):
  #  for episode in self.episodes:
  #    if episode.filename == filename:
  #      return episode    
    
  def __copy__(self):
    ret = SeasonInfo(self.show_name, self.season_num)
    ret.episodes = list(self.episodes)
    return ret
    
  def __str__(self):
    return "{} season {} - # episodes: {}".format(self.show_name, self.season_num, len(self.episodes))

  def to_search_params(self):
    return TvSearchParams(self.show_name, self.season_num)
  
  def has_data(self):
    return bool(self.episodes)
  
# --------------------------------------------------------------------------------------------------------------------
class Season:
  """ Creates a list of episode_move_items given a source and destination input map. """
  OK                = 1
  UNBALANCED_FILES  = -1
  SEASON_UNRESOLVED = -2
  SEASON_NOT_FOUND  = -3
  UNKNOWN           = -4
  
  @staticmethod
  def result_str(result):
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
      return "Season: {} #: ???".format(self.info.show_name)
    else:
      return "Season: {} #: {}".format(self.info.show_name, self.info.season_num)
  
  def __init__(self, input_folder, info, sources):
    #utils.verify_type(input_folder, str)
    #utils.verify_type(sources, SourceFiles)
    #utils.verify_type(info, SeasonInfo)
    
    self.sources = sources
    self.info = info
    self.perform_move = True #wtf? #HACK:
    self.input_folder = input_folder
    self.status = None
    self.episode_move_items = []
    self._resolve_episode_move_items()
    self._resolve_status() 
    
  def remove_source_file(self, filename):
    #utils.verify_type(f, basestring)
    self.sources.remove_file(filename)
    self.update_source(self.sources)
    
  def update_season_info(self, info):
    #utils.verify_type(info, SeasonInfo)
    self.info = info
    self._resolve_episode_move_items()
    self._resolve_status()    
    
  def update_source(self, sources):
    #utils.verify_type(sources, SourceFiles)
    self.sources = sources
    self._resolve_episode_move_items()
    self._resolve_status()    
          
  def _resolve_episode_move_items(self):
    self.episode_move_items = []
    temp_season_info = copy.copy(self.info)
    taken_keys = [] #dodgy...
    for source in self.sources:
      dest_ep = EpisodeInfo.create_unresolved_episode()
      if source.ep_num != UNRESOLVED_KEY and not source.ep_num in taken_keys:
        dest_ep = temp_season_info.get_episode_by_episode_num(source.ep_num)
        if dest_ep.ep_num != UNRESOLVED_KEY:
          temp_season_info.episodes.remove(dest_ep)
        taken_keys.append(source.ep_num)
      dest_ep = AdvancedEpisodeInfo(self.info.show_name, self.info.season_num, dest_ep.ep_num, dest_ep.ep_name)
      self.episode_move_items.append(EpisodeRenameItem(source.filename, dest_ep))
      
    for episode in temp_season_info.episodes:
      self.episode_move_items.append(EpisodeRenameItem("", 
          AdvancedEpisodeInfo(self.info.show_name, self.info.season_num, episode.ep_num, episode.ep_name)))
        
    self.episode_move_items = sorted(self.episode_move_items, key=lambda item: item.info.ep_num)
          
  def _resolve_status(self):
    if not self.info:
      self.status = Season.SEASON_NOT_FOUND
    if all([item.info.ep_num != UNRESOLVED_KEY and item.filename for item in self.episode_move_items]):
      self.status = Season.OK      
    else:
      self.status = Season.UNBALANCED_FILES  
  
  def set_episode_for_filename(self, key, filename):
    self.sources.set_episode_for_filename(key, filename)
    self.update_source(self.sources)
      
  def get_info(self):
    return self.info

  def isValid(self):
    return self.info.has_data()
 