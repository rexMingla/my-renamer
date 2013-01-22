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
    
  @staticmethod
  def getFolders(rootFolder, isRecursive):
    folders = []
    for root, dirs, files in os.walk(file_helper.FileHelper.replaceSeparators(rootFolder, os.sep)):
      folders.append(root)      
      if not isRecursive:
        break
    return folders 

  def setCache(self, data):
    #utils.verifyType(data, dict)
    self._cache = data

  def cache(self):
    return self._cache
  
  def getItem(self, searchParams, useCache=True):
    """ retrieves season from cache or holder's InfoClients if not present """
    item = None
    
    cacheKey = searchParams.getKey()
    if useCache and cacheKey in self._cache:
      item = self._cache[cacheKey]
    else:
      item = self._holder.getInfo(searchParams, default=searchParams.toInfo())
      if item and item.hasData():
        newKey = item.toSearchParams().getKey()
        cachedItem = copy.copy(item)
        self._cache[newKey] = cachedItem
        self._cache[cacheKey] = cachedItem
    return item    
  
  def setItem(self, item): 
    self._cache[item.toSearchParams().getKey()] = item
