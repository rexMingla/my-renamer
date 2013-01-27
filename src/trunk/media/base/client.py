#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------
import abc

class BaseInfoStoreHolder(object):
  """ container for all of the InfoClients """
  
  def __init__(self):
    super(BaseInfoStoreHolder, self).__init__()
    self.stores = []
  
  def add_store(self, store):
    index = self.get_store_index(store)
    if index == -1:
      self.stores.append(store)
    else:
      self.stores[index] = store
    
  def get_store_index(self, name):
    return next( (i for i, store in enumerate(self.stores) if name == store.pretty_name() ), -1)
  
  def get_store_helper(self, name):
    return next( (store for store in self.stores if name == store.pretty_name() ), None)
  
  def get_all_active_names(self):
    return [store.pretty_name() for store in self.stores if store.is_active()]  
  
  def get_config(self):
    ret = []
    for i, store in enumerate(self.stores):
      ret.append({"name": store.pretty_name(), "requires_key": store.requires_key, "key": store.key, "index": i})
    return ret
  
  def set_config(self, data):
    for i, values in enumerate(data):
      index = self.get_store_index(values["name"])
      if index != -1 and index != i:
        store = self.stores.pop(index)
        self.stores.insert(values["index"], store)
        store.requires_key = values["requires_key"]
        store.key = values["key"]
        
  def get_info(self, search_params, default=None):
    """ get info api  """
    return next(self.get_all_info(search_params), ResultHolder(default, "")).info
  
  def get_all_info(self, search_params):
    """ returns an iterator to ResultHolder objects """
    for store in self.stores:
      if store.is_active():
        for info in store.get_all_info(search_params):
          yield ResultHolder(info, store.source_name)  
  
# --------------------------------------------------------------------------------------------------------------------
class ResultHolder(object):
  def __init__(self, info, source_name):
    super(ResultHolder, self).__init__()
    self.info = info
    self.source_name = source_name
    
# --------------------------------------------------------------------------------------------------------------------
class BaseInfoClient(object):
  """ class to retrieve information from an online (or other) resource """
  __metaclass__ = abc.ABCMeta
  
  def __init__(self, display_name, source_name, url, has_lib, requires_key):
    super(BaseInfoClient, self).__init__()
    self.display_name = display_name #lib used
    self.source_name = source_name #website (or other) its connected to
    self.url = url #website
    self.has_lib = has_lib #is the library available
    self.requires_key = requires_key
    self.key = ""
    self.is_enabled = True #enabled by user
    
  def pretty_name(self):
    return "{} ({})".format(self.source_name, self.display_name)
  
  def is_available(self):
    return self.has_lib and (not self.requires_key or bool(self.key))
    
  def is_active(self):
    return self.is_available() and self.is_enabled
  
  #api stuff
  def get_info(self, search_params):
    return self._get_info(search_params) if self.has_lib else None

  def get_all_info(self, search_params):
    return self._get_all_info(search_params) if self.has_lib else None    

  def _get_info(self, search_params):
    infos = self._get_all_info(search_params)
    return infos[0] if infos else None
  
  @abc.abstractmethod
  def _get_all_info(self, search_params):
    pass