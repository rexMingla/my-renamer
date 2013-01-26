#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to tv show sources
# --------------------------------------------------------------------------------------------------------------------
from base import client as base_client
from common import utils
from tv import types as tv_types

hasTvdb = False
try:
  import tvdb_api
  import tvdb_exceptions  
  hasTvdb = True
except ImportError:
  pass

hasTvRage = False
try:
  import tvrage.api
  import tvrage.exceptions
  hasTvRage = True
except ImportError:
  pass
  
# --------------------------------------------------------------------------------------------------------------------
class TvInfoStoreHolder(base_client.BaseInfoStoreHolder):
  pass

_STORE = None

# --------------------------------------------------------------------------------------------------------------------
def getStoreHolder():
  global _STORE
  if not _STORE:
    _STORE = TvInfoStoreHolder()
    _STORE.addStore(TvdbClient())  
    _STORE.addStore(TvRageClient())  
  return _STORE

# --------------------------------------------------------------------------------------------------------------------
class BaseTvInfoClient(base_client.BaseInfoClient):
  pass
  
# --------------------------------------------------------------------------------------------------------------------
class TvdbClient(BaseTvInfoClient):
  def __init__(self):
    super(TvdbClient, self).__init__("tvdb_api", "thetvdb.com", "https://github.com/dbr/tvdb_api/", 
                                     hasLib=hasTvdb, 
                                     requiresKey=False)
    
  def _getInfos(self, searchParams):
    ret = []
    try:
      tv = tvdb_api.Tvdb()
      season = tv[searchParams.showName][searchParams.seasonNum]
      eps = tv_types.SeasonInfo(utils.sanitizeString(tv[searchParams.showName]["seriesname"], "") or 
                                          searchParams.showName, searchParams.seasonNum)
      ret.append(eps)
      for i in season:
        ep = season[i]
        show = tv_types.EpisodeInfo(int(ep["episodenumber"]), utils.sanitizeString(ep["episodename"] or ""))
        eps.episodes.append(show)
    except tvdb_exceptions.tvdb_exception as e:
      utils.logWarning("Lib: {} Show: {} seasonNum: {} Error {}: {}".format(self.displayName, searchParams.showName, 
                                                                            searchParams.seasonNum, type(e), e), 
                       title="{} lookup".format(self.displayName))
    return ret

# --------------------------------------------------------------------------------------------------------------------
class TvRageClient(BaseTvInfoClient):
  def __init__(self):
    super(TvRageClient, self).__init__("python-tvrage", "tvrage.com", 
                                       "http://pypi.python.org/pypi/python-tvrage/0.1.4", 
                                       hasLib=hasTvRage, 
                                       requiresKey=False)
    
  def _getInfos(self, searchParams):
    ret = []
    try:
      tv = tvrage.api.Show(searchParams.showName)
      season = tv.season(searchParams.seasonNum)
      eps = tv_types.SeasonInfo(utils.sanitizeString(tv.name) or searchParams.showName, searchParams.seasonNum)
      ret.append(eps)
      for ep in season.values():
        show = tv_types.EpisodeInfo(int(ep.number), utils.sanitizeString(ep.title))
        eps.episodes.append(show)
    except tvrage.exceptions.BaseError as e:
      utils.logWarning("Lib: {} Show: {} seasonNum: {} Error {}: {}".format(self.displayName, searchParams.showName, 
                                                                            searchParams.seasonNum, type(e), e), 
                       title="{} lookup".format(self.displayName))
    return ret
  