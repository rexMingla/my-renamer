#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Model and other classes pertaining to the set of tv seasons to be modified in the workbench
# --------------------------------------------------------------------------------------------------------------------
import copy

from common import commonTypes
from common import utils

# --------------------------------------------------------------------------------------------------------------------
class Result:
  SAMPLE_VIDEO = 1
  FILE_NOT_FOUND = 2
  FOUND = 3
  
  @staticmethod 
  def resultStr(result):
    if result == Result.SAMPLE_VIDEO:     return "Too small"
    elif result == Result.FILE_NOT_FOUND: return "File not found"
    elif result == Result.FOUND:          return "OK"
    else: 
      assert(result == Result.FOUND_NO_YEAR)
      return "Found: Without year"
  
VALID_RESULTS = (Result.SAMPLE_VIDEO, 
                 Result.FILE_NOT_FOUND, 
                 Result.FOUND)  
#TODO: Kill result!

# --------------------------------------------------------------------------------------------------------------------
class MovieRenameItem(commonTypes.BaseRenameItem):
  def __init__(self, filename, info):
    super(MovieRenameItem, self).__init__(filename)
    self.info = info
    self.result = None #Filthy, just temporary   
    
  def __copy__(self):
    ret = MovieRenameItem(self.filename, copy.copy(self.info))
    ret.result = self.result
    return ret
  
  def __str__(self):
    return str(self.info)
    
  def getInfo(self):
    return self.info

# --------------------------------------------------------------------------------------------------------------------
class MovieInfo(commonTypes.BaseInfo):
  """ info retrieved from movie clients """ 
  def __init__(self, title="", year=None, genres=None, series="", disc=None):
    super(MovieInfo, self).__init__()
    self.title = title
    self.year = year
    self.genres = genres or []
    self.series = series
    self.disc = disc
    
  def __copy__(self):
    return MovieInfo(self.title, self.year, list(self.genres), self.series)
  
  def __str__(self):
    return self.title if not self.year else "{} ({})".format(self.title, self.year)
  
  def __eq__(self, other):
    return (self.title == other.title and self.year == other.year and 
            self.part == other.part and self.movie.getGenre() == other.getGenre())
  
  def getGenre(self, default=""):
    return self.genres[0] if self.genres else default
  
  def toSearchParams(self):
    return MovieSearchParams(self.title, self.year)

# --------------------------------------------------------------------------------------------------------------------
class MovieSearchParams(commonTypes.BaseInfoClientSearchParams):
  """ class used to query info clients """
  def __init__(self, title, year=""):
    self.title = title
    self.year = year
    
  def getKey(self):
    return self.title if not self.year else utils.sanitizeString("{} ({})".format(self.title, self.year))
  
  def toInfo(self):
    return MovieInfo(self.title, self.year)

  