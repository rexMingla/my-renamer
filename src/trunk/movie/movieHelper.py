#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module responsible for the renaming of movies
# --------------------------------------------------------------------------------------------------------------------
import copy
import glob
import os
import re

from common import extension
from common import fileHelper
from common import utils

import movieInfoClient

#_SUBTITLE_EXTENSIONS = (".sub", ".srt", ".rar", ".sfv")
_PART_MATCH = re.compile(r".*(?:disc|cd)[\s0]*([1-9a-e]).*$", re.IGNORECASE)
_MOVIE_YEAR_MATCH = re.compile(r"(?P<title>.+?)(?P<year>\d{4}).*$")
_MOVIE_NO_YEAR_MATCH = re.compile(r"(?P<title>.+?)$")

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

# --------------------------------------------------------------------------------------------------------------------
class Movie(object):
  def __init__(self, filename, title, part="", year="", subsFiles=None, series=""):
    super(Movie, self).__init__()
    self.filename = filename #utils.toString(filename)
    self.fileSize = fileHelper.FileHelper.getFileSize(filename)
    self.ext = os.path.splitext(self.filename)[1].lower()
    self.title = utils.toString(title)
    #self.subsFiles = subsFiles # not used atm
    #dynamic properties
    self.year = utils.toString(year)
    self.genres = []
    self.part = part #disc number
    self.series = series
    self.result = None #Filthy, just temporary   
    
  def genre(self, valueIfNull=""):
    return self.genres[0] if self.genres else valueIfNull
   
  def __copy__(self):
    ret = Movie(self.filename, self.title, self.part, self.year, series=self.series)
    ret.result = self.result
    ret.genres = list(self.genres)
    return ret
  
  def __str__(self):
    return self.title if not self.year else "{} ({})".format(self.title, self.year)
    
  def itemToInfo(self):
    return movieInfoClient.MovieInfo(self.title, self.year, list(self.genres), self.series)
    
# --------------------------------------------------------------------------------------------------------------------
class MovieHelper:
  _cache = {}
  _store = movieInfoClient.getStore()
  
  @staticmethod
  def getFiles(folder, extensionFilter, isRecursive, minFileSizeBytes):
    files = []
    for dirName, _, filenames in os.walk(folder):
      for baseName in extensionFilter.filterFiles(sorted(filenames)):
        name = fileHelper.FileHelper.joinPath(dirName, baseName)
        if fileHelper.FileHelper.getFileSize(name) > minFileSizeBytes:
          files.append(name)
      if not isRecursive:
        break
    return files
  
  @staticmethod
  def processFile(filename):
    movie = MovieHelper.extractMovieFromFile(filename)
    if movie.result == Result.FOUND:
      info = MovieHelper.getItem(movie.title, movie.year)
      movie.year = info.year or movie.year
      movie.genres = info.genres or movie.genres
      movie.title = info.title or movie.title      
    return movie
  
  @staticmethod
  def extractMovieFromFile(filename):
    basename = fileHelper.FileHelper.basename(filename)
    name, ext = os.path.splitext(basename)
    ext = ext.lower()
    title, part, year, result = "", "", "", None
    if not os.path.exists(filename):
      result = Result.FILE_NOT_FOUND #somehow this happens
    else:
      result = Result.FOUND
      m = _MOVIE_YEAR_MATCH.match(name) or _MOVIE_NO_YEAR_MATCH.match(name)
      assert(m)
      title = m.groupdict().get("title")
      year = m.groupdict().get("year", "")
      part = ""
      partStr = basename
      moviesInFolder = len(glob.glob("{}/*{}".format(fileHelper.FileHelper.dirname(filename), ext)))
      if moviesInFolder < 3: #use the folder name if there aren't many files in the folder
        partStr = filename
      pm = _PART_MATCH.match(partStr)
      if pm:
        part = pm.group(1)
        if part.isalpha():
          part = utils.toString(" abcdef".index(part))
        else:
          part = int(part)  
      if title.find(" ") == -1:
        title = title.replace(".", " ")
      title = re.sub(r"[\(\[\{\s]+$", "", title) #clean end
      title = re.sub(r"^\w+\-", "", title) #strip anywords at the start before a - character
      #todo: fix subs...
      #subsFiles = [change_ext(filename, e) for e in _SUBTITLE_EXTENSIONS
      #              if os.path.exists(change_ext(filename, e)) ]
    movie = Movie(filename, title, part, year)
    movie.result = result
    return movie
  
  @classmethod
  def setCache(cls, data):
    utils.verifyType(data, dict)
    cls._cache = data

  @classmethod
  def cache(cls):
    return cls._cache

  @staticmethod
  def _getKey(title, year):
    return title if not year else utils.sanitizeString("{} ({})".format(title, year))

  @classmethod
  def getItem(cls, title, year="", useCache=True):
    """ retrieves season from cache or tvdb if not present """
    cacheKey = cls._getKey(title, year)
    ret = None
    if useCache and cacheKey in cls._cache:
      ret = cls._cache[cacheKey]
    else:
      ret = cls._store.getInfo(title, year, default=movieInfoClient.MovieInfo(title, year))
      if ret:
        cls._cache[cacheKey] = copy.copy(ret)
        newKey = cls._getKey(title, year)        
        if cacheKey != newKey:
          cls._cache[cacheKey] = copy.copy(ret)
    return ret 
  
  @classmethod
  def getItems(cls, title, year=""):
    pass
  
  @classmethod  
  def setItem(cls, item): 
    #utils.verifyType(item, MovieInfo)
    cls._cache[cls._getKey(item.title, item.year)] = item
