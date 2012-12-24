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
class TvSearchParams(infoClient.BaseInfoClientSearchParams):
  def __init__(self, showName, seasonNum):
    super(TvSearchParams, self).__init__()
    self.showName = showName
    self.seasonNum = seasonNum    
    
  def getKey(self):
    return utils.sanitizeString("{} ({})".format(self.showName, self.seasonNum))

  def toInfo(self):
    return episode.DestinationEpisodeMap(self.showName, self.seasonNum)

# --------------------------------------------------------------------------------------------------------------------
class TvInfo(infoClient.BaseInfo):
  def __init__(self, showName, seasonNum):
    self.showName = showName
    self.seasonNum = seasonNum
    self.episodes = {}
    
  def toDestEpisodeMap(self):
    #hack: this should be the same class
    ret = episode.DestinationEpisodeMap(self.showName, self.seasonNum)
    for epNum, name in self.episodes.items():
      ret.matches[key] = copy.copy(value)
    return ret
  
# --------------------------------------------------------------------------------------------------------------------
class TvInfoStore(infoClient.BaseInfoStore):
  pass

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
      eps = episode.DestinationEpisodeMap(utils.sanitizeString(tv[searchParams.showName]["seriesname"], "") or 
                                          searchParams.showName, searchParams.seasonNum)
      ret.append(eps)
      for i in season:
        ep = season[i]
        show = episode.DestinationEpisode(int(ep["episodenumber"]), utils.sanitizeString(ep["episodename"] or ""))
        eps.addItem(show)
    except tvdb_exceptions.tvdb_exception as e:
      utils.logWarning("Could not find season. Show: {} seasonNum: {} Error: {}".format(searchParams.showName, 
                                                                                        searchParams.seasonNum, e))
    return ret

# --------------------------------------------------------------------------------------------------------------------
class TvRageClient(BaseTvInfoClient):
  def __init__(self):
    super(TvRageClient, self).__init__("python-tvrage", "tvrage.com", "http://pypi.python.org/pypi/python-tvrage/0.1.4", 
                                       hasLib=hasTvRage, 
                                       requiresKey=False)
    
  def _getInfos(self, searchParams):
    ret = []
    try:
      tv = tvrage.api.Show(searchParams.showName)
      season = tv.season(searchParams.seasonNum)
      eps = episode.DestinationEpisodeMap(utils.sanitizeString(tv.name) or searchParams.showName, searchParams.seasonNum)
      ret.append(eps)
      for ep in season.values():
        show = episode.DestinationEpisode(int(ep.number), utils.sanitizeString(ep.title))
        eps.addItem(show)
    except tvrage.exceptions.BaseError as e:
      utils.logWarning("Could not find season. Show: {} seasonNum: {} Error: {}".format(searchParams.showName, 
                                                                                        searchParams.seasonNum, e))
    return ret
  