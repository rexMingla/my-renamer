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
class MovieInfoStore(infoClient.BaseInfoStore):
    
  def getInfo(self, title, year="", default=None):
    return next(self.getInfos(title, year), (default, ""))[0]
  
  def getInfos(self, title, year=""):
    """ returns an iterator """
    for store in self.stores:
      if store.isActive():
        for info in store.getInfos(title, year):
          yield (info, store.sourceName)
          
_STORE = None
# --------------------------------------------------------------------------------------------------------------------
def getStore():
  global _STORE
  if not _STORE:
    _STORE = MovieInfoStore()
    _STORE.addStore(ImdbClient())  
    #_STORE.addStore(ImdbPyClient())  # does not seem to work at the moment.
    _STORE.addStore(TheMovieDbClient()) 
    _STORE.addStore(RottenTomatoesClient()) 
  return _STORE

# --------------------------------------------------------------------------------------------------------------------
class MovieInfo(object):
  def __init__(self, title="", year=None, genres=None):
    super(MovieInfo, self).__init__()
    self.title = title
    self.year = year
    self.genres = genres or []
    
  def __copy__(self):
    return MovieInfo(self.title, self.year, list(self.genres))
  
  def __str__(self):
    return self.title if not self.year else "{} ({})".format(self.title, self.year)
  
# --------------------------------------------------------------------------------------------------------------------
class BaseMovieInfoClient(infoClient.BaseInfoClient):
  def getInfo(self, title, year=""):
    return self._getInfo(title, year) if self.hasLib else None

  def getInfos(self, title, year=""):
    return self._getInfos(title, year) if self.hasLib else None    

  def _getInfo(self, title, year=""):
    infos = self._getInfos(title, year)
    return infos[0] if infos else None
  
  def _getInfos(self, title, year=""):
    raise NotImplementedError("BaseMovieInfoClient.getInfos not implemented")
  
# --------------------------------------------------------------------------------------------------------------------
class ImdbClient(BaseMovieInfoClient):
  def __init__(self):
    super(ImdbClient, self).__init__("pymdb", "imdb.com", "https://github.com/caruccio/pymdb", 
                                     hasLib=_hasPymdb,
                                     requiresKey=False)
    
  def _getInfos(self, title, year=""):
    ret  = []
    info = None
    try:
      m = pymdb.Movie("{} {}".format(title, year))
      title = utils.sanitizeString(m.title or title)
      info = MovieInfo(title, year)
      ret.append(info)
      info.year = utils.sanitizeString(m.year or year)
      info.genres = [utils.sanitizeString(g) for g in m.genre] or info.genres
    except (AttributeError, pymdb.MovieError) as e:
      utils.logWarning("Title: {} Error {}: {}".format(title, type(e), e), title="TVDB lookup")
    return ret
  
# --------------------------------------------------------------------------------------------------------------------
class ImdbPyClient(BaseMovieInfoClient):
  def __init__(self):
    super(ImdbPyClient, self).__init__("imdbPy", "imdb.com", "http://imdbpy.sourceforge.net/", 
                                       hasLib=_hasImdbPy,
                                       requiresKey=False)
    
  def _getInfos(self, title, year=""):
    ret = []
    try:
      db = IMDb("http")
      m = db.search_movie("{} {}".format(title, year))
      info = MovieInfo(utils.sanitizeString(m.title or title), year)
      ret.append(info)
      info.year = utils.sanitizeString(m.year or year)
      info.genres = [utils.sanitizeString(g) for g in m.genre] or info.genres
    except (AttributeError, pymdb.MovieError) as e:
      utils.logWarning("Title: {} Error {}: {}".format(title, type(e), e), title="TVDB lookup")
    return ret
  
# --------------------------------------------------------------------------------------------------------------------
class TheMovieDbClient(BaseMovieInfoClient):
  def __init__(self):
    super(TheMovieDbClient, self).__init__("tmdb", "themoviedb.org", "https://github.com/dbr/themoviedb", 
                                           hasLib=_hasTmdb, 
                                           requiresKey=False)
    
  def _getInfos(self, title, year=""):
    ret = []
    try:
      prettyTitle = title if not year else "{} ({})".format(title, year)
      db = tmdb.MovieDb()
      results = db.search(prettyTitle)
      for r in results:
        title = utils.sanitizeString(r.get("name", title))
        year = str(r.get("released", year))[:4]
        info = MovieInfo(title, year)
        #don't worry about genre for now
        #i = r.info()
        #info.genres = map(utils.sanitizeString, i["categories"]["genre"].keys())
        ret.append(info)
    except tmdb.TmdBaseError as e:
      utils.logWarning("Title: {} Error {}: {}".format(title, type(e), e), title="TheMovieDB lookup")
    return ret

# --------------------------------------------------------------------------------------------------------------------
class RottenTomatoesClient(BaseMovieInfoClient):
  def __init__(self):
    super(RottenTomatoesClient, self).__init__("rottentomatoes", "RottenTomatoes.com",
                                               "https://github.com/zachwill/rottentomatoes", 
                                               _hasRottenTomatoes, True)
    
  def _getInfos(self, title, year=""):
    ret = []
    try:
      prettyTitle = title if not year else "{} ({})".format(title, year)
      rt = RT(self.key)
      results = rt.search(prettyTitle)
      for r in results:
        title = utils.sanitizeString(r.get("title", title))
        year = str(r.get("year", year))
        info = MovieInfo(title, year)
        #no genre without more effort
        ret.append(info)
    except Exception as e: #bad need to find a better exception
      utils.logWarning("Title: {} Error {}: {}".format(title, type(e), e), title="TheMovieDB lookup")
    return ret