#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Helper functions associated with tv series 
# --------------------------------------------------------------------------------------------------------------------
import copy
import collections
import itertools
import os
import re

from common import extension
from common import fileHelper
from common import utils

# --------------------------------------------------------------------------------------------------------------------
class BaseManager(object):
  def __init__(self, store):
    super(BaseManager, self).__init__()
    self._cache = {}
    self._store = store
    
  @staticmethod
  def getFolders(rootFolder, isRecursive):
    utils.verifyType(rootFolder, str)
    utils.verifyType(isRecursive, bool)
    folders = []
    for root, dirs, files in os.walk(fileHelper.FileHelper.replaceSeparators(rootFolder, os.sep)):
      folders.append(root)      
      if not isRecursive:
        break
    return folders 

  def setCache(self, data):
    utils.verifyType(data, dict)
    self._cache = data

  def cache(self):
    return self._cache
  
  def getItem(self, searchParams, useCache=True):
    """ retrieves season from cache or tvdb if not present """
    item = None
    
    cacheKey = searchParams.getKey()
    if useCache and cacheKey in self._cache:
      item = self._cache[cacheKey]
    else:
      item = self._store.getInfo(searchParams, default=searchParams.toInfo())
      if item and item.hasData():
        newKey = item.toSearchParams().getKey()
        cachedItem = copy.copy(item)
        self._cache[newKey] = cachedItem
        self._cache[cacheKey] = cachedItem
    return item    
  
  def setItem(self, item): 
    self._cache[item.toSearchParams().getKey()] = item  