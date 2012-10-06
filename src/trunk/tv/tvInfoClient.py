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

hasTvRage = False
try:
  import tvrage.api
  import tvrage.exceptions
  hasTvRage = True
except ImportError:
  pass

# --------------------------------------------------------------------------------------------------------------------
class TvInfoStore(infoClient.BaseInfoStore):
  
  def getInfo(self, showName, seasonNum, default=None):
    return next(self.getInfos(showName, seasonNum), (default, ""))[0]
  
  def getInfos(self, showName, seasonNum):
    """ returns an iterator """
    for store in self.stores:
      if store.isActive():
        for info in store.getInfos(showName, seasonNum):
          yield (info, store.sourceName)  
    
_STORE = None
# --------------------------------------------------------------------------------------------------------------------
def getStore():
  global _STORE
  if not _STORE:
    _STORE = TvInfoStore()
    _STORE.addStore(TvdbClient())  
    _STORE.addStore(TvRageClient())  
  return _STORE

# --------------------------------------------------------------------------------------------------------------------
class BaseTvInfoClient(infoClient.BaseInfoClient):
  
  def getInfo(self, showName, seasonNum):
    return self._getInfo(showName, seasonNum) if self.isActive() else None
  
  def getInfos(self, showName, seasonNum=""):
    return self._getInfos(showName, seasonNum) if self.hasLib else None    

  def _getInfo(self, showName, seasonNum=""):
    infos = self._getInfos(showName, seasonNum)
    return infos[0] if infos else None
  
  def _getInfos(self, showName, seasonNum=""):
    raise NotImplementedError("BaseTvInfoClient.getInfos not implemented")
  
# --------------------------------------------------------------------------------------------------------------------
class TvdbClient(BaseTvInfoClient):
  def __init__(self):
    super(TvdbClient, self).__init__("tvdb_api", "thetvdb.com", "https://github.com/dbr/tvdb_api/", 
                                     hasLib=hasTvdb, 
                                     requiresKey=False)
    
  def _getInfos(self, showName, seasonNum):
    utils.verifyType(showName, str)
    utils.verifyType(seasonNum, int)
    ret = []
    try:
      tv = tvdb_api.Tvdb()
      season = tv[showName][seasonNum]
      eps = episode.DestinationEpisodeMap(utils.sanitizeString(tv[showName]["seriesname"], "") or showName, seasonNum)
      ret.append(eps)
      for i in season:
        ep = season[i]
        show = episode.DestinationEpisode(int(ep["episodenumber"]), utils.sanitizeString(ep["episodename"] or ""))
        eps.addItem(show)
    except tvdb_exceptions.tvdb_exception as e:
      utils.logWarning("Could not find season. Show: {} seasonNum: {} Error: {}".format(showName, seasonNum, e))
    return ret

# --------------------------------------------------------------------------------------------------------------------
class TvRageClient(BaseTvInfoClient):
  def __init__(self):
    super(TvRageClient, self).__init__("python-tvrage", "tvrage.com", "http://pypi.python.org/pypi/python-tvrage/0.1.4", 
                                       hasLib=hasTvRage, 
                                       requiresKey=False)
    
  def _getInfos(self, showName, seasonNum):
    utils.verifyType(showName, str)
    utils.verifyType(seasonNum, int)
    ret = []
    try:
      tv = tvrage.api.Show(showName)
      season = tv.season(seasonNum)
      eps = episode.DestinationEpisodeMap(utils.sanitizeString(tv.name) or showName, seasonNum)
      ret.append(eps)
      for ep in season.values():
        show = episode.DestinationEpisode(int(ep.number), utils.sanitizeString(ep.title))
        eps.addItem(show)
    except tvrage.exceptions.BaseError as e:
      utils.logWarning("Could not find season. Show: {} seasonNum: {} Error: {}".format(showName, seasonNum, e))
    return ret
  