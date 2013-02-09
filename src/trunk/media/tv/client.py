#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to tv show sources
# --------------------------------------------------------------------------------------------------------------------
from media.base import client as base_client
from common import utils
from media.tv import types as tv_types

_HAS_TVDB = False
try:
  import tvdb_api
  import tvdb_exceptions
  _HAS_TVDB = True
except ImportError:
  pass

_HAS_TVRAGE = False
try:
  import tvrage.api
  import tvrage.exceptions
  _HAS_TVRAGE = True
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
                                     has_lib=_HAS_TVDB,
                                     requires_key=False)

  def _getAllInfo(self, search_params):
    ret = []
    try:
      source = tvdb_api.Tvdb()
      season = source[search_params.show_name][search_params.season_num]
      eps = tv_types.SeasonInfo(utils.sanitizeString(source[search_params.show_name]["seriesname"], "") or
                                          search_params.show_name, search_params.season_num)
      ret.append(eps)
      for i in season:
        episode = season[i]
        show = tv_types.EpisodeInfo(int(episode["episodenumber"]),
                                    utils.sanitizeString(episode["episodename"] or ""))
        eps.episodes.append(show)
    except tvdb_exceptions.tvdb_exception as ex:
      utils.logWarning("Lib: {} Show: {} season_num: {} Error {}: {}".format(self.display_name, search_params.show_name,
                                                                            search_params.season_num, type(ex), ex),
                       title="{} lookup".format(self.display_name))
    return ret

# --------------------------------------------------------------------------------------------------------------------
class TvRageClient(BaseTvInfoClient):
  def __init__(self):
    super(TvRageClient, self).__init__("python-tvrage", "tvrage.com",
                                       "http://pypi.python.org/pypi/python-tvrage/0.1.4",
                                       has_lib=_HAS_TVRAGE,
                                       requires_key=False)

  def _getAllInfo(self, search_params):
    ret = []
    try:
      source = tvrage.api.Show(search_params.show_name)
      season = source.season(search_params.season_num)
      eps = tv_types.SeasonInfo(utils.sanitizeString(source.name) or search_params.show_name, search_params.season_num)
      ret.append(eps)
      for i in season.values():
        show = tv_types.EpisodeInfo(int(i.number), utils.sanitizeString(i.title))
        eps.episodes.append(show)
    except tvrage.exceptions.BaseError as ex:
      utils.logWarning("Lib: {} Show: {} season_num: {} Error {}: {}".format(self.display_name, search_params.show_name,
                                                                            search_params.season_num, type(ex), ex),
                       title="{} lookup".format(self.display_name))
    return ret


