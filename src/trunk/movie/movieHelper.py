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
  def __init__(self, filename, title, part=None, year="", subsFiles=None):
    super(Movie, self).__init__()
    self.filename = str(filename)
    self.inPath = os.path.dirname(self.filename)
    self.ext = os.path.splitext(self.filename)[1].lower()
    self.title = str(title)
    #self.subsFiles = subsFiles # not used atm
    #dynamic properties
    self.year = year
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
        files.append(fileHelper.FileHelper.joinPath(dirName, baseName))
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
    title, part, year, result = None, None, None, None
    if not os.path.exists(filename):
      result = Result.FILE_NOT_FOUND #somehow this happens
    elif os.path.getsize(filename) < _MIN_VIDEO_SIZE_BYTES:
      result = Result.SAMPLE_VIDEO
    else:
      result = Result.FOUND
      m = _MOVIE_YEAR_MATCH.match(name) or _MOVIE_NO_YEAR_MATCH.match(name)
      assert(m)
      title = m.groupdict().get("title")
      year = m.groupdict().get("year")
      part = None
      partStr = basename
      moviesInFolder = len(glob.glob("{}/*{}".format(fileHelper.FileHelper.dirname(filename), ext)))
      if moviesInFolder < 3: #use the folder name if there aren't many files in the folder
        partStr = filename
      pm = _PART_MATCH.match(filename)
      if pm:
        part = pm.group(1)
        if part.isalpha():
          part = str(" abcdef".index(part))
      if part:
        print "**", part, basename
      if title.find(" ") == -1:
        title = title.replace(".", " ")
      title = re.sub(r"[\(\[\{\s]+$", "", title)
      title = re.sub(r"^\w+\-", "", title)
      #todo: fix subs...
      #subsFiles = [change_ext(filename, e) for e in _SUBTITLE_EXTENSIONS
      #              if os.path.exists(change_ext(filename, e)) ]
    movie = Movie(filename, title, part, year)
    movie.result = result
    return movie
    
  @staticmethod
  def getInfoFromTvdb(title, year=""):
    info = MovieInfo(title, year)
    try:
      m = pymdb.Movie(title)
      info.title = str(m.title or title)
      info.year = str(m.year or year)
      info.genres = m.genre or []
    except (AttributeError, ValueError, pymdb.MovieError) as e:
      print("**error: %s on %s" % (e, title))
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
  def getItem(title, year):
    """ retrieves season from cache or tvdb if not present """
    cacheKey = "%s (%s)" % (title, year)
    global _CACHE
    ret = None
    if cacheKey in _CACHE:
      ret = _CACHE[cacheKey]
    else:
      ret = MovieHelper.getInfoFromTvdb(title, year)
      if ret:
        _CACHE[cacheKey] = copy.copy(ret)
    return ret 
    
x = """# ------------------------------------------------------------------    
def trawl_folder(folder):
  results = dict( (v, []) for v in VALID_RESULTS)
  movies = []
  for dir_name, dir_names, filenames in os.walk(folder):
    for base_name in sorted(filenames): #sort so disc ordering is resolved
      name, ext = os.path.splitext(base_name)
      ext = ext.lower()
      ret = None
      full_name = clean_string(os.path.join(dir_name, base_name))
      if not os.path.exists(full_name):
        ret = Result.IGNORED_FILE_NOT_FOUND
      elif not ext in _VIDEO_EXTENSIONS:
        ret = Result.IGNORED_NOT_VIDEO
      elif os.path.getsize(full_name) < _MIN_VIDEO_SIZE_BYTES:
        ret = Result.IGNORED_SAMPLE_VIDEO
      else:
        m = _MOVIE_YEAR_MATCH.match(name) or _MOVIE_NO_YEAR_MATCH.match(name)
        assert(m)
        title = m.groupdict().get("title")
        year = m.groupdict().get("year")
        part = None
        if year:
          ret = Result.FOUND_YEAR
        else:
          ret = Result.FOUND_NO_YEAR
        part_str = base_name
        if len(filenames) < 3: #use the folder name if there aren't many files in the folder
          part_str = full_name
        pm = _PART_MATCH.match(full_name)
        if pm:
          part = pm.group(1)
          if part.isalpha():
            part = str(" abcdef".index(part))
        if part:
          print "**", part, base_name
        if title.find(" ") == -1:
          title = title.replace(".", " ")
        title = re.sub(r"[\(\[\{\s]+$", "", title)
        title = re.sub(r"^\w+\-", "", title)
        #todo: fix subs...
        subsFiles = [change_ext(full_name, e) for e in _SUBTITLE_EXTENSIONS
                      if os.path.exists(change_ext(full_name, e)) ]
        movie = Movie(full_name, title, part, year, subsFiles)
        movies.append(movie)
      results[ret].append(full_name)
  return results, movies
  
# ------------------------------------------------------------------    
def change_ext(filename, ext):
  return clean_string("%s.%s" % (os.path.splitext(filename)[0], ext))

def write_log_summary(filename, result_hist, movies):
  f = open(filename, "w")
  data = {"hist": result_hist, "movies": movies, "cache": CACHE}
  f.write(jsonpickle.encode(data))
  f.close()
  
def read_log_summary(filename):
  if os.path.exists(filename):
    f = open(filename, "r")
    obj = jsonpickle.decode(f.read())
    f.close()
    if "cache" in obj:
      CACHE = obj["cache"]
    print len(CACHE)
  
def really_clean_string(text):
  _VALID_BASENAME_CHARACTERS = "%s%s%s" % (string.ascii_letters,
                                           string.digits,
                                           " !#$%&'()*+,-./;=@[\]^_`{}~")
  invalidFilenameCharsRegex = "[^%s]" % re.escape(_VALID_BASENAME_CHARACTERS)
  text = re.sub(invalidFilenameCharsRegex, "-", text)  
  return text
  
def clean_string(text):
  return str(text).decode("utf-8", "ignore")

def make_dirs(folder):
  if not os.path.exists(folder):
    os.makedirs(folder)
  assert(folder)
  
def seek_info(movie):
  info = None
  key = "%s (%s)" % (movie.title, movie.year)
  if key in CACHE:
    info = CACHE[key]
  else:
    info = MovieInfo(movie.title)
    try:
      m = pymdb.Movie(movie.title)
      info.title = str(m.title or info.title)
      info.year = str(m.year or info.year)
      info.genres = m.genre or info.genres
      if info:
        CACHE["%s (%s)" % (info.title, info.year)] = info
    except (AttributeError, ValueError, pymdb.MovieError) as e:
      print("**error: %s on %s" % (e, movie.title))
  return info
  #TODO: rstrip
# ------------------------------------------------------------------    
def main():
  root_dir = r"S:\media\unsorted\movies"
  out_dir = r"S:\media\sorted\movies"
  log_file = os.path.join(root_dir, "log.txt")
  total = 0
  match = 0
  read_log_summary(log_file)  
  results, movies = trawl_folder(root_dir)

  ignored_extensions = set(os.path.splitext(n)[1] for n in results[Result.IGNORED_NOT_VIDEO])
  print("%s%s" % ("Extensions: ", " ".join(ignored_extensions)))
      
  for result, filenames in results.items():
    print("%s => %d" % (Result.as_string(result), len(filenames)))
  
  if not os.path.isabs(out_dir):
    out_dir = os.path.normpath(os.path.join(root_dir, out_dir))
  make_dirs(out_dir)
  print("Output dir: %s" % out_dir)
  
  #search for info
  count = 0
  if MODE in (LookupMode.ALL, LookupMode.SEMI):
    for m in movies:
      #if not m.year or MODE == LookupMode.ALL:
      info = seek_info(m)
      m.year = info.year or m.year
      m.genres = info.genres or m.genres
      m.title = info.title or m.title
      count += 1
      if count % 10 == 0:
        print("%d%%" % int(100 * count / len(movies)))
      break
  
  #validate. check for collisions
  for i, m1 in enumerate(movies):
    collision_count = 0
    for m2 in movies[i + 1:]:
      if m1.title == m2.title and m1.title == m2.title and m1.year == m2.year and \
         m1.ext == m2.ext and m1.part == m2.part:
        collision_count += 1
        m2.collision_number = collision_count
        m1.collision_number = 0 #make it the first collision
    
  limbo_dir = os.path.join(out_dir, ".limbo")
  make_dirs(limbo_dir)
  
  collision_dir = os.path.join(out_dir, ".clash")
  make_dirs(collision_dir)

  for m in movies:
    m.out_location = m.getMovieName(out_dir, collision_dir, limbo_dir)
    m.move()
    
  if not os.listdir(limbo_dir):
    os.rmdir(limbo_dir)
  if not os.listdir(collision_dir):
    os.rmdir(collision_dir)
    
  result_hist = dict( (r, {"name" : Result.as_string(r), "count" : len(filenames)})
                     for r, filenames in results.items())
  write_log_summary(log_file, result_hist, movies)
  
# ------------------------------------------------------------------    
if __name__ == "__main__":
  main()
"""
