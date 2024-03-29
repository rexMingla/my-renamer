#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Classes to represent movies
# --------------------------------------------------------------------------------------------------------------------
import copy

from media.base import types as base_types
from common import file_helper
from common import utils

# --------------------------------------------------------------------------------------------------------------------
class MovieRenameItem(base_types.BaseRenameItem):
  FILE_NOT_FOUND = "File not found"
  
  def __init__(self, filename, info, is_enabled=True):
    super(MovieRenameItem, self).__init__(filename, info)

  def __copy__(self):
    ret = MovieRenameItem(self.filename, copy.copy(self.getInfo()), self.is_enabled)
    return ret

  def getStatus(self):
    return self.READY if file_helper.FileHelper.fileExists(self.filename) else self.FILE_NOT_FOUND

  def __str__(self):
    return str(self._info)

# --------------------------------------------------------------------------------------------------------------------
class MovieInfo(base_types.BaseInfo):
  """ info retrieved from media.movie clients """
  def __init__(self, title="", year=None, genres=None, series="", part=None):
    super(MovieInfo, self).__init__(base_types.MOVIE_MODE)
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
            self.part == other.part and self.getGenre() == other.getGenre())

  def getGenre(self, default=""):
    return self.genres[0] if self.genres else default

  def getSearchParams(self):
    return MovieSearchParams(self.title, self.year)

# --------------------------------------------------------------------------------------------------------------------
class MovieSearchParams(base_types.BaseSearchParams):
  """ class used to query info clients """
  def __init__(self, title, year=""):
    self.title = title
    self.year = year

  def getKey(self):
    return self.title if not self.year else utils.sanitizeString("{} ({})".format(self.title, self.year))

  def getInfo(self):
    return MovieInfo(self.title, self.year)


