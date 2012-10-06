#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------
from common import infoClient
from common import utils

hasPymdb = False
try:
  from pymdb import pymdb
  hasPymdb = True
except ImportError:
  pass

hasTmdb = False
try:
  import tmdb
  hasTmdb = True
except ImportError:
  pass

hasImdbPy = False
try:
  from imdb import IMDb
  hasImdbPy = True
except ImportError:
  pass

# --------------------------------------------------------------------------------------------------------------------
class MovieInfoStore(infoClient.BaseInfoStore):
    
  def getInfo(self, title, year="", default=None):
    ret = None
    for store in self.stores:
      if store.isActive():
        ret = store.getInfo(title, year)
        if ret:
          break
    return ret or default
  
  def getInfos(self, title, year=""):
    """ returns an iterator """
    for store in self.stores:
      if store.isActive():
        for info in store.getInfos(title, year):
          yield (info, store.prettyName())
          
_STORE = None
# --------------------------------------------------------------------------------------------------------------------
def getStore():
  global _STORE
  if not _STORE:
    _STORE = MovieInfoStore()
    _STORE.addStore(ImdbClient())  
    _STORE.addStore(TheMovieDbClient())  
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
                                     hasLib=hasPymdb,
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
                                       hasLib=hasImdbPy,
                                       requiresKey=False)
    
  def _getInfos(self, title, year=""):
    return []
    info = MovieInfo(title, year)
    try:
      db = IMDb()
      m = db.search_movie("{} {}".format(title, year))
      info.title = utils.sanitizeString(m.title or title)
      info.year = utils.sanitizeString(m.year or year)
      info.genres = [utils.sanitizeString(g) for g in m.genre] or info.genres
    except (AttributeError, pymdb.MovieError) as e:
      utils.logWarning("Title: {} Error {}: {}".format(title, type(e), e), title="TVDB lookup")
    return info
  
class TheMovieDbClient(BaseMovieInfoClient):
  def __init__(self):
    super(TheMovieDbClient, self).__init__("tmdb", "themoviedb.org", "https://github.com/dbr/themoviedb", hasTmdb, True)
    
  def _getInfos(self, title, year=""):
    return [] #info = MovieInfo(title, year)
    #results = tmdb.search("Fight Club")    
    
#MovieInfoStore.addStore(ImdbClient())
#MovieInfoStore.addStore(TheMovieDbClient())
#MovieInfoStore.addStore(ImdbPyClient())
  
  