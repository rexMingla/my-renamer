#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------
from common import infoClient
from common import utils

_hasPymdb = False
try:
  from pymdb import pymdb
  _hasPymdb = True
except ImportError:
  pass

_hasTmdb = False
try:
  import tmdb
  _hasTmdb = True
except ImportError:
  pass

_hasImdbPy = False
try:
  from imdb import IMDb
  _hasImdbPy = True
except ImportError:
  pass

_hasRottenTomatoes = False
try:
  from rottentomatoes import RT
  _hasRottenTomatoes = True
except ImportError:
  pass

# --------------------------------------------------------------------------------------------------------------------
class MovieInfo(infoClient.BaseInfo):
  """ info retrieved from movie clients """ 
  def __init__(self, title="", year=None, genres=None, series=""):
    super(MovieInfo, self).__init__()
    self.title = title
    self.year = year
    self.genres = genres or []
    self.series = series
    
  def __copy__(self):
    return MovieInfo(self.title, self.year, list(self.genres), self.series)
  
  def __str__(self):
    return self.title if not self.year else "{} ({})".format(self.title, self.year)
  
  def toSearchParams(self):
    return MovieSearchParams(self.title, self.year)

# --------------------------------------------------------------------------------------------------------------------
class MovieSearchParams(infoClient.BaseInfoClientSearchParams):
  """ class used to query info clients """
  def __init__(self, title, year=""):
    self.title = title
    self.year = year
    
  def getKey(self):
    return self.title if not self.year else utils.sanitizeString("{} ({})".format(self.title, self.year))
  
  def toInfo(self):
    return MovieInfo(self.title, self.year)

# --------------------------------------------------------------------------------------------------------------------
class MovieInfoStoreHolder(infoClient.BaseInfoStoreHolder):
  pass

_STORE = None

# --------------------------------------------------------------------------------------------------------------------
def getStoreHolder():
  global _STORE
  if not _STORE:
    _STORE = MovieInfoStoreHolder()
    _STORE.addStore(ImdbClient())  
    #_STORE.addStore(ImdbPyClient())  # does not seem to work at the moment.
    _STORE.addStore(TheMovieDbClient()) 
    _STORE.addStore(RottenTomatoesClient()) 
  return _STORE
  
# --------------------------------------------------------------------------------------------------------------------
class BaseMovieInfoClient(infoClient.BaseInfoClient):
  pass
  
# --------------------------------------------------------------------------------------------------------------------
class ImdbClient(BaseMovieInfoClient):
  def __init__(self):
    super(ImdbClient, self).__init__("pymdb", "imdb.com", "https://github.com/caruccio/pymdb", 
                                     hasLib=_hasPymdb,
                                     requiresKey=False)
    
  def _getInfos(self, searchParams):
    ret  = []
    info = None
    try:
      m = pymdb.Movie("{} {}".format(searchParams.title, searchParams.year))
      title = utils.sanitizeString(m.title or searchParams.title)
      info = MovieInfo(title, searchParams.year)
      ret.append(info)
      info.year = utils.sanitizeString(m.year or searchParams.year)
      info.genres = [utils.sanitizeString(g) for g in m.genre] or info.genres
      
    except AttributeError as e:
      pass
    except pymdb.MovieError as e:
      utils.logWarning("Lib: {} Title: {} Error {}: {}".format(self.displayName, searchParams.title, type(e), e), 
                       title="{} lookup".format(self.displayName))
    return ret
  
# --------------------------------------------------------------------------------------------------------------------
class ImdbPyClient(BaseMovieInfoClient):
  def __init__(self):
    super(ImdbPyClient, self).__init__("imdbPy", "imdb.com", "http://imdbpy.sourceforge.net/", 
                                       hasLib=_hasImdbPy,
                                       requiresKey=False)
    
  def _getInfos(self, searchParams):
    ret = []
    try:
      db = IMDb("http")
      m = db.search_movie("{} {}".format(searchParams.title, searchParams.year))
      info = MovieInfo(utils.sanitizeString(m.title or searchParams.title), searchParams.year)
      ret.append(info)
      info.year = utils.sanitizeString(m.year or searchParams.year)
      info.genres = [utils.sanitizeString(g) for g in m.genre] or info.genres
    except (AttributeError, pymdb.MovieError) as e:
      utils.logWarning("Lib: {} Title: {} Error {}: {}".format(self.displayName, searchParams.title, type(e), e), 
                       title="{} lookup".format(self.displayName))
    return ret
  
# --------------------------------------------------------------------------------------------------------------------
class TheMovieDbClient(BaseMovieInfoClient):
  def __init__(self):
    super(TheMovieDbClient, self).__init__("tmdb", "themoviedb.org", "https://github.com/dbr/themoviedb", 
                                           hasLib=_hasTmdb, 
                                           requiresKey=False)
    
  def _getInfos(self, searchParams):
    ret = []
    try:
      prettyTitle = searchParams.title if not searchParams.year else "{} ({})".format(searchParams.title, searchParams.year)
      db = tmdb.MovieDb()
      results = db.search(prettyTitle)
      for r in results:
        title = utils.sanitizeString(r.get("name", searchParams.title))
        year = str(r.get("released", searchParams.year))[:4]
        info = MovieInfo(title, year)
        ret.append(info)
        i = r.info()
        genres = i["categories"]["genre"].keys() if ("categories" in i and "genre" in i["categories"]) else []
        info.genres = map(utils.sanitizeString, genres)
    except tmdb.TmdBaseError as e:
      utils.logWarning("Lib: {} Title: {} Error {}: {}".format(self.displayName, searchParams.title, type(e), e), 
                       title="{} lookup".format(self.displayName))
    return ret

# --------------------------------------------------------------------------------------------------------------------
class RottenTomatoesClient(BaseMovieInfoClient):
  def __init__(self):
    super(RottenTomatoesClient, self).__init__("rottentomatoes", "rottentomatoes.com",
                                               "https://github.com/zachwill/rottentomatoes", 
                                               _hasRottenTomatoes, True)
    
  def _getInfos(self, searchParams):
    ret = []
    try:
      prettyTitle = title if not year else "{} ({})".format(searchParams.title, searchParams.year)
      rt = RT(self.key)
      results = rt.search(prettyTitle)
      for r in results:
        title = utils.sanitizeString(r.get("title", searchParams.title))
        year = str(r.get("year", searchParams.year))
        info = MovieInfo(title, year)
        #no genre without more effort
        ret.append(info)
    except Exception as e: #bad need to find a better exception
      utils.logWarning("Lib: {} Title: {} Error {}: {}".format(self.displayName, searchParams.title, type(e), e), 
                       title="{} lookup".format(self.displayName))
    return ret