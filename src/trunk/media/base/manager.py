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
    
  def get_holder(self):
    return self._holder
    
  @staticmethod
  def get_folders(root_folder, is_recursive):
    folders = []
    for root, _dirs, _files in os.walk(file_helper.FileHelper.replace_separators(root_folder, os.sep)):
      folders.append(root)      
      if not is_recursive:
        break
    return folders 

  def set_cache(self, data):
    #utils.verify_type(data, dict)
    self._cache = data

  def cache(self):
    return self._cache
  
  def get_item(self, search_params, use_cache=True):
    #TODO: make get_info
    """ retrieves season from cache or holder's InfoClients if not present """
    item = None
    
    cache_key = search_params.get_key()
    if use_cache and cache_key in self._cache:
      item = self._cache[cache_key]
    else:
      item = self._holder.get_info(search_params, default=search_params.to_info())
      if item and item.has_data():
        new_key = item.to_search_params().get_key()
        cached_item = copy.copy(item)
        self._cache[new_key] = cached_item
        self._cache[cache_key] = cached_item
    return item    
  
  def set_item(self, item): 
    self._cache[item.to_search_params().get_key()] = item
