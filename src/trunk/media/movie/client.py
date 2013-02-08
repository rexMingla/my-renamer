#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------
from media.base import client as base_client
from common import utils
from media.movie import types as movie_types

_HAS_PYMDB = False
try:
  from pymdb import pymdb
  _HAS_PYMDB = True
except ImportError:
  pass

_HAS_TMDB = False
try:
  import tmdb
  _HAS_TMDB = True
except ImportError:
  pass

_HAS_IMDB_PY = False
try:
  from imdb import IMDb
  _HAS_IMDB_PY = True
except ImportError:
  pass

_HAS_ROTTEN_TOMATOES = False
try:
  from rottentomatoes import RT
  _HAS_ROTTEN_TOMATOES = True
except ImportError:
  pass

# --------------------------------------------------------------------------------------------------------------------
class MovieInfoStoreHolder(base_client.BaseInfoStoreHolder):
  pass

_STORE = None

# --------------------------------------------------------------------------------------------------------------------
def get_store_holder():
  global _STORE
  if not _STORE:
    _STORE = MovieInfoStoreHolder()
    _STORE.add_store(ImdbClient())  
    #_STORE.add_store(ImdbPyClient())  # does not seem to work at the moment.
    _STORE.add_store(TheMovieDbClient()) 
    _STORE.add_store(RottenTomatoesClient()) 
  return _STORE
  
# --------------------------------------------------------------------------------------------------------------------
class BaseMovieInfoClient(base_client.BaseInfoClient):
  pass
  
# --------------------------------------------------------------------------------------------------------------------
class ImdbClient(BaseMovieInfoClient):
  def __init__(self):
    super(ImdbClient, self).__init__("pymdb", "imdb.com", "https://github.com/caruccio/pymdb", 
                                     has_lib=_HAS_PYMDB,
                                     requires_key=False)
    
  def _get_all_info(self, search_params):
    ret  = []
    info = None
    try:
      movie = pymdb.Movie(str(search_params))
      title = utils.sanitize_string(movie.title or search_params.title)
      info = movie_types.MovieInfo(title, search_params.year)
      ret.append(info)
      info.year = utils.sanitize_string(movie.year or search_params.year)
      info.genres = [utils.sanitize_string(g) for g in movie.genre] or info.genres
    except (ValueError, AttributeError) as ex:
      pass
    except pymdb.MovieError as ex:
      utils.log_warning("Lib: {} Title: {} Error {}: {}".format(self.display_name, search_params.title, type(ex), ex), 
                       title="{} lookup".format(self.display_name))
    return ret
  
# --------------------------------------------------------------------------------------------------------------------
class ImdbPyClient(BaseMovieInfoClient):
  def __init__(self):
    super(ImdbPyClient, self).__init__("imdbPy", "imdb.com", "http://imdbpy.sourceforge.net/", 
                                       has_lib=_HAS_IMDB_PY,
                                       requires_key=False)
    
  def _get_all_info(self, search_params):
    ret = []
    try:
      source = IMDb("http")
      movie = source.search_movie(str(search_params))
      info = movie_types.MovieInfo(utils.sanitize_string(movie.title or search_params.title), search_params.year)
      ret.append(info)
      info.year = utils.sanitize_string(movie.year or search_params.year)
      info.genres = [utils.sanitize_string(g) for g in movie.genre] or info.genres
    except (AttributeError, pymdb.MovieError) as ex:
      utils.log_warning("Lib: {} Title: {} Error {}: {}".format(self.display_name, search_params.title, type(ex), ex), 
                       title="{} lookup".format(self.display_name))
    return ret
  
# --------------------------------------------------------------------------------------------------------------------
class TheMovieDbClient(BaseMovieInfoClient):
  def __init__(self):
    super(TheMovieDbClient, self).__init__("tmdb", "themoviedb.org", "https://github.com/dbr/themoviedb", 
                                           has_lib=_HAS_TMDB, 
                                           requires_key=False)
    
  def _get_all_info(self, search_params):
    ret = []
    try:
      pretty_title = str(search_params)
      source = tmdb.MovieDb()
      results = source.search(pretty_title)
      for result in results:
        title = utils.sanitize_string(result.get("name", search_params.title))
        year = str(result.get("released", search_params.year))[:4]
        info = movie_types.MovieInfo(title, year)
        ret.append(info)
        sub_info = result.info()
        genres = []
        if "categories" in sub_info and "genre" in sub_info["categories"]:
          genres = sub_info["categories"]["genre"].keys()
        info.genres = [utils.sanitize_string(g) for g in genres]
    except tmdb.TmdBaseError as ex:
      utils.log_warning("Lib: {} Title: {} Error {}: {}".format(self.display_name, search_params.title, type(ex), ex), 
                       title="{} lookup".format(self.display_name))
    return ret

# --------------------------------------------------------------------------------------------------------------------
class RottenTomatoesClient(BaseMovieInfoClient):
  def __init__(self):
    super(RottenTomatoesClient, self).__init__("rottentomatoes", "rottentomatoes.com",
                                               "https://github.com/zachwill/rottentomatoes", 
                                               _HAS_ROTTEN_TOMATOES, True)
    
  def _get_all_info(self, search_params):
    ret = []
    try:
      pretty_title = str(search_params)
      source = RT(self.key)
      results = source.search(pretty_title)
      for i in results:
        title = utils.sanitize_string(i.get("title", search_params.title))
        year = str(i.get("year", search_params.year))
        info = movie_types.MovieInfo(title, year)
        #no genre without more effort
        ret.append(info)
    except Exception as ex: #bad need to find a better exception
      utils.log_warning("Lib: {} Title: {} Error {}: {}".format(self.display_name, search_params.title, type(ex), ex), 
                       title="{} lookup".format(self.display_name))
    return ret