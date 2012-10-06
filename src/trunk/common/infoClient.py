#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that connects to movie info sources
# --------------------------------------------------------------------------------------------------------------------
from common import utils

hasPymdb = False
try:
  from pymdb import pymdb
  hasPymdb = True
except ImportError:
  pass

hasTmdb = False
try:
  import tmdb
  hasTmdb = True
except ImportError:
  pass

hasImdbPy = False
try:
  from imdb import IMDb
  hasImdbPy = True
except ImportError:
  pass

class BaseInfoStore(object):
  def __init__(self):
    self.stores = []
  
  def addStore(self, store):
    index = self.getStoreIndex(store)
    if index == -1:
      self.stores.append(store)
    else:
      self.stores[index] = store
    
  def getStoreIndex(self, name):
    return next( (i for i, s in enumerate(self.stores) if name == s.prettyName() ), -1)
  
  def getStore(self, name):
    return next( (s for s in self.stores if name == s.prettyName() ), -1)
  
  def setAllActive(self, stores):
    for key in stores:
      s = self.getStore(key)
      if s and s.isAvailable():
        s.isEnabled = True
    
  def getAllActiveNames(self):
    return [store.prettyName() for store in self.stores if store.isActive()]
  
# --------------------------------------------------------------------------------------------------------------------
class BaseInfoClient(object):
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
  