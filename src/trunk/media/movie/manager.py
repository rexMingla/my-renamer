#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module responsible for the renaming of movies
# --------------------------------------------------------------------------------------------------------------------
import glob
import os
import re

from media.base import manager as base_manager
from common import file_helper
from common import utils

from media.movie import types as movie_types
from media.movie import client as movie_client

_PART_MATCH = re.compile(r".*(?:disc|cd)[\s0]*([1-9a-e]).*$", re.IGNORECASE)
_MOVIE_YEAR_MATCH = re.compile(r"(?P<title>.+?)(?P<year>\d{4}).*$")
_MOVIE_NO_YEAR_MATCH = re.compile(r"(?P<title>.+?)$")

# --------------------------------------------------------------------------------------------------------------------
class MovieHelper:
  @staticmethod
  def getFiles(folder, ext_filter, is_recursive, min_file_size_bytes):
    files = []
    for dir_name, _, filenames in os.walk(folder):
      for basename in ext_filter.filterFiles(sorted(filenames)):
        name = file_helper.FileHelper.joinPath(dir_name, basename)
        if file_helper.FileHelper.getFileSize(name) > min_file_size_bytes:
          files.append(name)
      if not is_recursive:
        break
    return files

  @staticmethod
  def extractMovieFromFile(filename):
    basename = file_helper.FileHelper.basename(filename)
    name, ext = os.path.splitext(basename)
    ext = ext.lower()
    title, part, year = "", "", ""
    if os.path.exists(filename):
      match = _MOVIE_YEAR_MATCH.match(name) or _MOVIE_NO_YEAR_MATCH.match(name)
      assert(match)
      title = match.groupdict().get("title")
      year = match.groupdict().get("year", "")
      part = ""
      part_str = basename
      num_movies_in_folder = len(glob.glob("{}/*{}".format(file_helper.FileHelper.dirname(filename), ext)))
      if num_movies_in_folder < 3: #use the folder name if there aren't many files in the folder
        part_str = filename
      part_match = _PART_MATCH.match(part_str)
      if part_match:
        part = part_match.group(1)
        if part.isalpha():
          part = utils.toString(" abcdef".index(part))
        else:
          part = int(part)
      if title.find(" ") == -1:
        title = title.replace(".", " ")
      title = re.sub(r"[\(\[\{\s]+$", "", title) #clean end
      title = re.sub(r"^\w+\-", "", title) #strip anywords at the start before a - character
    movie = movie_types.MovieRenameItem(filename, movie_types.MovieInfo(title, year, genres=[], series="", part=part))
    return movie

# --------------------------------------------------------------------------------------------------------------------
class MovieManager(base_manager.BaseManager):
  helper = MovieHelper

  def __init__(self):
    super(MovieManager, self).__init__(movie_client.getInfoClientHolder())

  def processFile(self, filename):
    movie = MovieHelper.extractMovieFromFile(filename)
    if movie.isReady():
      movie.info = self.getInfo(movie.getInfo().getSearchParams())
    return movie

_MANAGER = None

def getManager():
  global _MANAGER
  if not _MANAGER:
    _MANAGER = MovieManager()
  return _MANAGER
