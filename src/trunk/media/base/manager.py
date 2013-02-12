  #!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: cache of info client results 
# --------------------------------------------------------------------------------------------------------------------
import copy

from common import file_helper

# --------------------------------------------------------------------------------------------------------------------
class BaseManager(object):
  """ maintains a cache of previous info client results. if the item can not be found in the cache the info client
  hold is called to retrieve info directly from the 3rd party. 
  
  Attributes:
    _cache: internal dictionary mapping searchParams key to base.types.BaseInfo objects
    _holder: base.client.InfoClientHolder object that will perform the info search 
    
  The cache key is bound to the result of the base.types.BaseSearchParams.toKey() function.
  """
  def __init__(self, holder):
    super(BaseManager, self).__init__()
    self._cache = {}
    self._holder = holder

  def getInfo(self, search_params, use_cache=True):
    """ retrieves season from cache or holder's InfoClient if not present. If the item is not retrived from cache the 
      result written to cache before returning from the function. 
    Args:
      search_params: base.types.BaseSearchParams
      use_cache: boolean determines whether to look up value from cache or holder is accessed directly. 
        If False, the cached isn't cleared so subsequent calls will be able to pick up the last saved value.
    Returns: 
      base.types.BaseInfo
    """
    info = None
    cache_key = search_params.getKey()
    if use_cache and cache_key in self._cache:
      info = self._cache[cache_key]
    else:
      info = self._holder.getInfo(search_params, default=search_params.getInfo())
      if info and info.isValid():
        new_key = info.getSearchParams().getKey()
        cached_item = copy.copy(info)
        self._cache[new_key] = cached_item
        self._cache[cache_key] = cached_item
    return info

  def setInfo(self, info):
    """ stores the base.types.BaseInfo object in cache (unfortunately the key is bound to the search params object). """
    self._cache[info.getSearchParams().getKey()] = info

  def getHolder(self):
    return self._holder

  def setCache(self, data):
    self._cache = data

  def cache(self):
    return self._cache

