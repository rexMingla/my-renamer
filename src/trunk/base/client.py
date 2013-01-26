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
  
  def addStore(self, store):
    index = self.getStoreIndex(store)
    if index == -1:
      self.stores.append(store)
    else:
      self.stores[index] = store
    
  def getStoreIndex(self, name):
    return next( (i for i, s in enumerate(self.stores) if name == s.prettyName() ), -1)
  
  def getStoreHolder(self, name):
    return next( (s for s in self.stores if name == s.prettyName() ), None)
  
  def setAllActive(self, stores):
    for key in stores:
      s = self.getStoreHolder(key)
      if s and s.isAvailable():
        s.isEnabled = True
    
  def getAllActiveNames(self):
    return [store.prettyName() for store in self.stores if store.isActive()]  
  
  def get_config(self):
    ret = []
    for i, s in enumerate(self.stores):
      ret.append({"name": s.prettyName(), "isEnabled": s.isEnabled, "key": s.key, "index": i})
    return ret
  
  def set_config(self, data):
    for i, values in enumerate(data):
      index = self.getStoreIndex(values["name"])
      if index != -1 and index != i:
        store = self.stores.pop(index)
        self.stores.insert(values["index"], store)
        store.isEnabled = values["isEnabled"]
        store.key = values["key"]
        
  def getInfo(self, searchParams, default=None):
    """ get info api  """
    return next(self.getInfos(searchParams), ResultHolder(default, "")).info
  
  def getInfos(self, searchParams):
    """ returns an iterator to ResultHolder objects """
    for store in self.stores:
      if store.isActive():
        for info in store.getInfos(searchParams):
          yield ResultHolder(info, store.sourceName)  
  
# --------------------------------------------------------------------------------------------------------------------
class ResultHolder(object):
  def __init__(self, info, sourceName):
    super(ResultHolder, self).__init__()
    self.info = info
    self.sourceName = sourceName
    
# --------------------------------------------------------------------------------------------------------------------
class BaseInfoClient(object):
  """ class to retrieve information from an online (or other) resource """
  __metaclass__ = abc.ABCMeta
  
  def __init__(self, displayName, sourceName, url, hasLib, requiresKey):
    super(BaseInfoClient, self).__init__()
    self.displayName = displayName #lib used
    self.sourceName = sourceName #website (or other) its connected to
    self.url = url #website
    self.hasLib = hasLib #is the library available
    self.requiresKey = requiresKey
    self.key = ""
    self.isEnabled = True #enabled by user
    
  def prettyName(self):
    return "{} ({})".format(self.sourceName, self.displayName)
  
  def isAvailable(self):
    return self.hasLib and (not self.requiresKey or bool(self.key))
    
  def isActive(self):
    return self.isAvailable() and self.isEnabled
  
  #api stuff
  def getInfo(self, searchParams):
    return self._getInfo(searchParams) if self.hasLib else None

  def getInfos(self, searchParams):
    return self._getInfos(searchParams) if self.hasLib else None    

  def _getInfo(self, searchParams):
    infos = self._getInfos(searchParams)
    return infos[0] if infos else None
  
  @abc.abstractmethod
  def _getInfos(self, searchParams):
    pass