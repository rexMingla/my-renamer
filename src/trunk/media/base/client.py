#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------
from common import utils

class BaseInfoStoreHolder(object):
  """ container for all of the InfoClients """

  def __init__(self):
    super(BaseInfoStoreHolder, self).__init__()
    self.stores = []

  def addStore(self, store):
    index = self.getStoreIndex(store)
    if index == -1:
      self.stores.append(store)
    else:
      self.stores[index] = store

  def getStoreIndex(self, name):
    return next( (i for i, store in enumerate(self.stores) if name == store.prettyName() ), -1)

  def getStoreHolder(self, name):
    return next( (store for store in self.stores if name == store.prettyName() ), None)

  def getAllActiveNames(self):
    return [store.prettyName() for store in self.stores if store.isActive()]

  def getConfig(self):
    ret = []
    for i, store in enumerate(self.stores):
      ret.append({"name": store.prettyName(), "requires_key": store.requires_key, "key": store.key, "index": i})
    return ret

  def setConfig(self, data):
    for i, values in enumerate(data):
      index = self.getStoreIndex(values["name"])
      if index != -1 and index != i:
        store = self.stores.pop(index)
        self.stores.insert(values["index"], store)
        store.requires_key = values["requires_key"]
        store.key = values["key"]

  def getInfo(self, search_params, default=None):
    """ get info api  """
    return next(self.getAllInfo(search_params), ResultHolder(default, "")).info

  def getAllInfo(self, search_params):
    """ returns an iterator to ResultHolder objects """
    for store in self.stores:
      if store.isActive():
        for info in store.getAllInfo(search_params):
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
  def __init__(self, display_name, source_name, url, has_lib, requires_key):
    super(BaseInfoClient, self).__init__()
    self.display_name = display_name #lib used
    self.source_name = source_name #website (or other) its connected to
    self.url = url #website
    self.has_lib = has_lib #is the library available
    self.requires_key = requires_key
    self.key = ""
    self.is_enabled = True #enabled by user

  def prettyName(self):
    return "{} ({})".format(self.source_name, self.display_name)

  def isAvailable(self):
    return self.has_lib and (not self.requires_key or bool(self.key))

  def isActive(self):
    return self.isAvailable() and self.is_enabled

  #api stuff
  def getInfo(self, search_params):
    return self._getInfo(search_params) if self.has_lib else None

  def getAllInfo(self, search_params):
    ret = []
    try:
      ret = self._getAllInfo(search_params) if self.has_lib else None
    except Exception as ex:
      utils.logWarning("uncaught exception in lib. lib={} params={} ex={}".format(self.display_name,
          search_params.getKey(), ex))
    return ret

  def _getInfo(self, search_params):
    infos = self._getAllInfo(search_params)
    return infos[0] if infos else None

  def _getAllInfo(self, search_params):
    raise NotImplementedError("BaseInfoClient._getAllInfo not implemented")

