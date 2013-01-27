#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Classes to represent movies
# --------------------------------------------------------------------------------------------------------------------
import copy

from media.base import types as base_types
from common import utils

# --------------------------------------------------------------------------------------------------------------------
class MovieRenameItem(base_types.BaseRenameItem):
  def __init__(self, filename, info):
    super(MovieRenameItem, self).__init__(filename)
    self.info = info
    
  def __copy__(self):
    ret = MovieRenameItem(self.filename, copy.copy(self.info))
    return ret
  
  def file_exists(self):
    return self.file_size > 0
  
  def __str__(self):
    return str(self.info)
  
  def get_info(self):
    return self.info

# --------------------------------------------------------------------------------------------------------------------
class MovieInfo(base_types.BaseInfo):
  """ info retrieved from media.movie clients """ 
  def __init__(self, title="", year=None, genres=None, series="", part=None):
    super(MovieInfo, self).__init__()
    self.title = title
    self.year = year
    self.genres = genres or []
    self.series = series
    self.part = part
    
  def __copy__(self):
    return MovieInfo(self.title, self.year, list(self.genres), self.series)
  
  def __str__(self):
    return self.title if not self.year else "{} ({})".format(self.title, self.year)
  
  def __eq__(self, other):
    return (self.title == other.title and self.year == other.year and 
            self.part == other.part and self.get_genre() == other.get_genre())
  
  def get_genre(self, default=""):
    return self.genres[0] if self.genres else default
  
  def to_search_params(self):
    return MovieSearchParams(self.title, self.year)

# --------------------------------------------------------------------------------------------------------------------
class MovieSearchParams(base_types.BaseInfoClientSearchParams):
  """ class used to query info clients """
  def __init__(self, title, year=""):
    self.title = title
    self.year = year
    
  def get_key(self):
    return self.title if not self.year else utils.sanitize_string("{} ({})".format(self.title, self.year))
  
  def to_info(self):
    return MovieInfo(self.title, self.year)

  