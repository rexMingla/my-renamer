  #!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Helper functions associated with tv series
# --------------------------------------------------------------------------------------------------------------------
import copy
import os

from common import file_helper

# --------------------------------------------------------------------------------------------------------------------
class BaseManager(object):
  """ uses cache and BaseHolder to retrieve BaseInfo data """
  def __init__(self, holder):
    super(BaseManager, self).__init__()
    self._cache = {}
    self._holder = holder

  def getHolder(self):
    return self._holder

  @staticmethod
  def getFolders(root_folder, is_recursive):
    folders = []
    for root, _dirs, _files in os.walk(file_helper.FileHelper.replaceSeparators(root_folder, os.sep)):
      folders.append(root)
      if not is_recursive:
        break
    return folders

  def setCache(self, data):
    #utils.verifyType(data, dict)
    self._cache = data

  def cache(self):
    return self._cache

  def getItem(self, search_params, use_cache=True):
    #TODO: make getInfo
    """ retrieves season from cache or holder's InfoClients if not present """
    item = None

    cache_key = search_params.getKey()
    if use_cache and cache_key in self._cache:
      item = self._cache[cache_key]
    else:
      item = self._holder.getInfo(search_params, default=search_params.toInfo())
      if item and item.hasData():
        new_key = item.toSearchParams().getKey()
        cached_item = copy.copy(item)
        self._cache[new_key] = cached_item
        self._cache[cache_key] = cached_item
    return item

  def setItem(self, item):
    self._cache[item.toSearchParams().getKey()] = item
