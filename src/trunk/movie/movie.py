#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: interface to the imdb api
# --------------------------------------------------------------------------------------------------------------------
import os
import re
import string

import jsonpickle
jsonpickle.set_encoder_options("simplejson", indent=2)
from pymdb import pymdb
  
VIDEO_EXTENSIONS = (".avi", ".divx", ".mkv", ".mpg", ".mp4", ".wmv")
SUBTITLE_EXTENSIONS = (".sub", ".srt", ".rar", ".sfv")
PART_MATCH = re.compile(r".*(?:disc|cd)[\s0]*([1-9a-e]).*$", re.IGNORECASE)
MOVIE_YEAR_MATCH = re.compile(r"(?P<title>.+?)(?P<year>\d{4}).*$")
MOVIE_NO_YEAR_MATCH = re.compile(r"(?P<title>.+?)$")
MIN_VIDEO_SIZE_BYTES = 20 * 1024 * 1024 # 20 MB
IS_TEST_ONLY = True # create dummy files
MODE = None 

CACHE = {}

# ------------------------------------------------------------------    
class LookupMode:
  LAZY = "lazy" #move all regardless of matching year
  SEMI = "semi" #move year'ed, lookup non year'ed
  ALL = "all"
  
VALID_MODES = (LookupMode.LAZY, LookupMode.SEMI, LookupMode.ALL)
MODE = LookupMode.SEMI

# ------------------------------------------------------------------    
class Result:
  IGNORED_NOT_VIDEO = 1
  IGNORED_SAMPLE_VIDEO = 2
  IGNORED_FILE_NOT_FOUND = 3
  FOUND_YEAR = 4
  FOUND_NO_YEAR = 5
  
  @staticmethod 
  def as_string(result):
    if result == Result.IGNORED_NOT_VIDEO:        return "Ignored: Not video"
    elif result == Result.IGNORED_SAMPLE_VIDEO:   return "Ignored: Video too small"
    elif result == Result.IGNORED_FILE_NOT_FOUND: return "Ignored: File not found"
    elif result == Result.FOUND_YEAR:             return "Found: With year"
    else: 
      assert(result == Result.FOUND_NO_YEAR)
      return "Found: Without year"
  
VALID_RESULTS = (Result.IGNORED_NOT_VIDEO, 
                 Result.IGNORED_SAMPLE_VIDEO, 
                 Result.IGNORED_FILE_NOT_FOUND,
                 Result.FOUND_YEAR, 
                 Result.FOUND_NO_YEAR)

# ------------------------------------------------------------------    
class Movie(object):
  def __init__(self, filename, title, part, year=None, subs_files=None):
    super(Movie, self).__init__()
    self.filename = clean_string(filename)
    self.in_path = os.path.dirname(self.filename)
    self.ext = os.path.splitext(self.filename)[1].lower()
    self.title = clean_string(title)
    self.subs_files = subs_files # not used atm
    #dynamic properties
    self.year = year
    self.genres = ["unknown"]
    self.is_moved = False
    self.out_location = None
    self.collision_number = None #marked if multiple entries have the same name
    self.part = part #disc number
    
  def get_movie_name(self, normal_dir, collision_dir, limbo_dir):
    def get_name():
      out = [self.title]
      if self.year:
        out.append(" (%s)" % self.year)
      if self.part:
        out.append(" CD %s" % self.part)
      if not self.collision_number is None:
        out.append("[%d]" %  self.collision_number)
      out.append(self.ext)
      return "".join(out)
    
    name = get_name()
    folder = limbo_dir
    if not self.collision_number is None:
      folder = collision_dir
    if self.year:
      #sub_folder = ""
      sub_folder = really_clean_string(self.genres[0])
      """elif not sub_folder:
        sub_folder = name[0].upper()
        if sub_folder.isdigit():
          sub_folder = "0-9"
        elif not sub_folder.isalpha():
          sub_folder = "Misc" """
      folder = os.path.join(normal_dir, sub_folder)
      
    return os.path.join(folder, name)
    
  def move(self):
    assert(self.out_location and not self.is_moved)
    if os.path.exists(self.out_location):
      print("wtf: file exists in output location: %s" % self.out_location)
      return
    make_dirs(os.path.dirname(self.out_location))
    #todo: assert some stuff
    try:
      if IS_TEST_ONLY:
        #create a dummy file in the directory
        open(self.out_location, "w").close()
        #todo: subtitles...
      else:
        open(self.out_location, "w").close()#os.rename(self.filename, self.out_location)    
    except (IOError, WindowsError) as e:
      print("**error: %s on file: %s" % (e, self.out_location))
    self.is_moved = os.path.exists(self.out_location) and not (self.filename)
    
# ------------------------------------------------------------------    
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
      elif not ext in VIDEO_EXTENSIONS:
        ret = Result.IGNORED_NOT_VIDEO
      elif os.path.getsize(full_name) < MIN_VIDEO_SIZE_BYTES:
        ret = Result.IGNORED_SAMPLE_VIDEO
      else:
        m = MOVIE_YEAR_MATCH.match(name) or MOVIE_NO_YEAR_MATCH.match(name)
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
        pm = PART_MATCH.match(full_name)
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
        subs_files = [change_ext(full_name, e) for e in SUBTITLE_EXTENSIONS
                      if os.path.exists(change_ext(full_name, e)) ]
        movie = Movie(full_name, title, part, year, subs_files)
        movies.append(movie)
      results[ret].append(full_name)
  return results, movies

# ------------------------------------------------------------------    
class MovieInfo(object):
  def __init__(self, title="", year=None, genres=None):
    super(MovieInfo, self).__init__()
    self.title = title
    self.year = year
    self.genres = genres or []
  
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
    m.out_location = m.get_movie_name(out_dir, collision_dir, limbo_dir)
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
