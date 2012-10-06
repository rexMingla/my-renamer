#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to tv show sources
# --------------------------------------------------------------------------------------------------------------------
from common import infoClient
from common import utils

import episode

hasTvdb = False
try:
  import tvdb_api
  import tvdb_exceptions  
  hasTvdb = True
except ImportError:
  pass

# --------------------------------------------------------------------------------------------------------------------
class TvInfoStore(infoClient.BaseInfoStore):
  
  def getInfo(self, showName, seasonNum, default=None):
    ret = None
    for store in self.stores:
      if store.isActive():
        ret = store.getInfo(showName, seasonNum)
        if ret:
          break
    return ret or default 
    
_STORE = None
# --------------------------------------------------------------------------------------------------------------------
def getStore():
  global _STORE
  if not _STORE:
    _STORE = TvInfoStore()
    _STORE.addStore(TvdbClient())  
  return _STORE

# --------------------------------------------------------------------------------------------------------------------
class BaseTvInfoClient(infoClient.BaseInfoClient):
  
  def getInfo(self, showName, seasonNum):
    return self._getInfo(showName, seasonNum) if self.isActive() else None

  def _getInfo(self, showName, seasonNum):
    raise NotImplementedError("BaseTvInfoClient.getInfo not implemented")
  
# --------------------------------------------------------------------------------------------------------------------
class TvdbClient(BaseTvInfoClient):
  def __init__(self):
    super(TvdbClient, self).__init__("tvdb_api", "thetvdb.com", "https://github.com/dbr/tvdb_api/", hasTvdb, False)
    
  def _getInfo(self, showName, seasonNum):
    utils.verifyType(showName, str)
    utils.verifyType(seasonNum, int)
    eps = None
    try:
      tv = tvdb_api.Tvdb()
      season = tv[showName][seasonNum]
      eps = episode.DestinationEpisodeMap(showName, seasonNum)
      eps = episode.DestinationEpisodeMap(utils.sanitizeString(tv[showName]["seriesname"], "") or showName, seasonNum)
      for i in season:
        ep = season[i]
        show = episode.DestinationEpisode(int(ep["episodenumber"]), utils.sanitizeString(ep["episodename"] or ""))
        eps.addItem(show)
    except tvdb_exceptions.tvdb_exception as e:
      utils.logWarning("Could not find season. Show: {} seasonNum: {} Error: {}".format(showName, seasonNum, e))
    return eps  

  
  