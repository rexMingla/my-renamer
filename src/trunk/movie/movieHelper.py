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

from pymdb import pymdb

from common import extension
from common import fileHelper
from common import utils

#_SUBTITLE_EXTENSIONS = (".sub", ".srt", ".rar", ".sfv")
_PART_MATCH = re.compile(r".*(?:disc|cd)[\s0]*([1-9a-e]).*$", re.IGNORECASE)
_MOVIE_YEAR_MATCH = re.compile(r"(?P<title>.+?)(?P<year>\d{4}).*$")
_MOVIE_NO_YEAR_MATCH = re.compile(r"(?P<title>.+?)$")
_MIN_VIDEO_SIZE_BYTES = 20 * 1024 * 1024 # 20 MB

_CACHE = {}

# --------------------------------------------------------------------------------------------------------------------
class Result:
  SAMPLE_VIDEO = 1
  FILE_NOT_FOUND = 2
  FOUND = 3
  
  @staticmethod 
  def as_string(result):
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
  def __init__(self, filename, title, part="", year="", fileSize=0, subsFiles=None):
    super(Movie, self).__init__()
    self.filename = filename #utils.toString(filename)
    self.fileSize = fileSize
    self.ext = os.path.splitext(self.filename)[1].lower()
    self.title = utils.toString(title)
    #self.subsFiles = subsFiles # not used atm
    #dynamic properties
    self.year = utils.toString(year)
    self.genres = []
    self.collision_number = None #marked if multiple entries have the same name
    self.part = part #disc number
    self.result = None #Filthy, just temporary   
    
  def genre(self, valueIfNull=""):
    return self.genres[0] if self.genres else valueIfNull
   
  def __copy__(self):
    ret = Movie(self.filename, self.title, self.part, self.year)
    ret.collision_number = self.collision_number
    ret.result = self.result
    ret.genres = list(self.genres)
    return ret
    
  def itemToInfo(self):
    return MovieInfo(self.title, self.year, list(self.genres))
    
# --------------------------------------------------------------------------------------------------------------------
class MovieInfo(object):
  def __init__(self, title="", year=None, genres=None):
    super(MovieInfo, self).__init__()
    self.title = title
    self.year = year
    self.genres = genres or []
    
  def __copy__(self):
    return MovieInfo(self.title, self.year, list(self.genres))
    
# --------------------------------------------------------------------------------------------------------------------
class MovieHelper:
  @staticmethod
  def getFiles(folder, extensionFilter, isRecursive):
    files = []
    for dirName, _, filenames in os.walk(folder):
      for baseName in extensionFilter.filterFiles(sorted(filenames)):
        files.append(utils.sanitizeString(fileHelper.FileHelper.joinPath(dirName, baseName)))
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
    size = fileHelper.FileHelper.getFileSize(filename) 
    title, part, year, result = "", "", "", None
    if not os.path.exists(filename):
      result = Result.FILE_NOT_FOUND #somehow this happens
    elif size < _MIN_VIDEO_SIZE_BYTES:
      result = Result.SAMPLE_VIDEO
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
    movie = Movie(filename, title, part, year, size)
    movie.result = result
    return movie
    
  @staticmethod
  def getInfoFromTvdb(title, year=""):
    info = MovieInfo(title, year)
    try:
      m = pymdb.Movie(title)
      info.title = utils.sanitizeString(m.title or title)
      info.year = utils.sanitizeString(m.year or year)
      info.genres = [utils.sanitizeString(g) for g in m.genre] or info.genres
    except (AttributeError, pymdb.MovieError) as e:
      utils.logWarning("Title: {} Error {}: {}".format(title, type(e), e), title="TVDB lookup")
    return info
  
  @staticmethod
  def setCache(data):
    utils.verifyType(data, dict)
    global _CACHE
    _CACHE = data

  @staticmethod
  def cache():
    global _CACHE
    return _CACHE

  @staticmethod
  def getItem(title, year, useCache=True):
    """ retrieves season from cache or tvdb if not present """
    cacheKey = utils.sanitizeString("{} ({})".format(title, year))
    global _CACHE
    ret = None
    if useCache and cacheKey in _CACHE:
      ret = _CACHE[cacheKey]
    else:
      ret = MovieHelper.getInfoFromTvdb(title, year)
      utils.logDebug("{} ({}".format(title, year))
      import jsonpickle
      f = open("test.txt", "w")
      f.write(jsonpickle.encode({"test" : ret}))
      f.close()      
      if ret:
        _CACHE[cacheKey] = copy.copy(ret)
        newKey = utils.sanitizeString("{} ({})".format(title, year))        
        if cacheKey != newKey:
          _CACHE[cacheKey] = copy.copy(ret)
    return ret 
    
