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
from common import manager
from common import renamer
from common import utils

import movieInfoClient

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
class MovieRenameItem(renamer.BaseRenameItem):
  def __init__(self, filename, title, part="", year="", subsFiles=None, series=""):
    super(MovieRenameItem, self).__init__()
    self.filename = filename #utils.toString(filename)
    self.fileSize = fileHelper.FileHelper.getFileSize(filename)
    self.ext = fileHelper.FileHelper.extension(filename)
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
    ret = MovieRenameItem(self.filename, self.title, self.part, self.year, series=self.series)
    ret.result = self.result
    ret.genres = list(self.genres)
    return ret
  
  def __str__(self):
    return self.title if not self.year else "{} ({})".format(self.title, self.year)
    
  def itemToInfo(self):
    return movieInfoClient.MovieInfo(self.title, self.year, list(self.genres), self.series)
    
# --------------------------------------------------------------------------------------------------------------------
class MovieHelper:
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
    movie = MovieRenameItem(filename, title, part, year)
    movie.result = result
    return movie  
    
# --------------------------------------------------------------------------------------------------------------------
class MovieManager(manager.BaseManager):
  helper = MovieHelper
  
  def __init__(self):
    super(MovieManager, self).__init__(movieInfoClient.getStoreHolder())
  
  def processFile(self, filename):
    movie = MovieHelper.extractMovieFromFile(filename)
    if movie.result == Result.FOUND:
      info = self.getItem(movieInfoClient.MovieSearchParams(movie.title, movie.year))
      movie.year = info.year or movie.year
      movie.genres = info.genres or movie.genres
      movie.title = info.title or movie.title      
    return movie

_MANAGER = None  

def getManager():
  global _MANAGER
  if not _MANAGER:
    _MANAGER = MovieManager()
  return _MANAGER
