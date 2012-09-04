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

import tvdb_api
import tvdb_exceptions

from common import extension
from common import fileHelper
from common import utils

import episode
import season

_CACHE = {}

_RE_FOLDER_MATCH_1 = re.compile(r"^.*{0}(?P<name>.*){0}(?:season|series)\s+(?P<num>\d+)[^{0}]*$".format(re.escape(os.sep)), 
                                flags=re.IGNORECASE) #/show/season
_RE_FOLDER_MATCH_2 = re.compile(r"^.*{0}(?P<name>.*)\s+\-\s+(?:season|series)\s+(?P<num>\d+)[^{0}]*$".format(re.escape(os.sep)), 
                                flags=re.IGNORECASE) #/show - season
_RE_EPISODE_MATCH = re.compile(r"^.*?(?P<epNum>\d\d?)\D*\.[^\.]*$")

class SeasonHelper:
  """ Collection of tv series functions. """
  @staticmethod
  def seasonFromFolderName(folder):
    utils.verifyType(folder, str)
    folder = fileHelper.FileHelper.replaceSeparators(folder, os.sep)
    show = episode.UNRESOLVED_NAME
    seriesNum = episode.UNRESOLVED_KEY
    for regex in (_RE_FOLDER_MATCH_1, _RE_FOLDER_MATCH_2):
      m = regex.match(folder)
      if m:
        show = m.group("name")
        seriesNum = int(m.group("num"))
        break
    return show, seriesNum
  
  @staticmethod
  def getSourceEpisodeMapFromFilenames(filenames):
    def getCandidateEpisodeNumsFromFilename(filename):
      """ returns a list of numbers for the filename """
      return [int(m[-2:]) for m in re.findall("\d+", fileHelper.FileHelper.basename(filename))] or [episode.UNRESOLVED_KEY]

    if not filenames:
      return episode.EpisodeMap()
    
    eps = [(f, getCandidateEpisodeNumsFromFilename(f)) for f in filenames]
    maxIndexes = max(len(ep[1]) for ep in eps)
    epMaps = []
    for i in range(maxIndexes):
      epMap = episode.EpisodeMap()
      for f, indexes in eps:
        epMap.addItem(episode.SourceEpisode(indexes[i] if i < len(indexes) else episode.UNRESOLVED_KEY, f))
      epMaps.append(epMap)
    for i in range(maxIndexes):
      epMap = episode.EpisodeMap()
      for f, indexes in eps:
        epMap.addItem(episode.SourceEpisode(indexes[- i - 1] if i < len(indexes) else episode.UNRESOLVED_KEY, f))
      epMaps.append(epMap)
    return max(epMaps, key=lambda epMap: len(epMap.matches))
  
  @staticmethod
  def getSeasonInfoFromTVDB(showName, seasonNum):
    utils.verifyType(showName, str)
    utils.verifyType(seasonNum, int)
    sanitizedShowName = showName
    eps = episode.EpisodeMap()
    try:
      tv = tvdb_api.Tvdb()
      season = tv[showName][seasonNum]
      sanitizedShowName = utils.sanitizeString(tv[showName]["seriesname"], "") or showName
      for i in season:
        ep = season[i]
        show = episode.DestinationEpisode(int(ep["episodenumber"]), utils.sanitizeString(ep["episodename"] or ""))
        eps.addItem(show)
    except tvdb_exceptions.tvdb_exception as e:
      utils.logWarning("Could not find season. Show: {} seasonNum: {} Error: {}".format(showName, seasonNum, e))
    return sanitizedShowName, eps  
  
  @staticmethod
  def getDestinationEpisodeMapFromTVDB(showName, seasonNum):
    utils.verifyType(showName, str)
    utils.verifyType(seasonNum, int)
    return SeasonHelper.getSeasonInfoFromTVDB(showName, seasonNum)[1]
  
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

  @staticmethod
  def getSeasonsForFolders(rootFolder, isRecursive, extensionFilter):
    utils.verifyType(rootFolder, str)
    utils.verifyType(isRecursive, bool)
    utils.verifyType(extensionFilter, extension.FileExtensions)
    seasons = []
    dirs = SeasonHelper.getFolders(rootFolder, isRecursive)
    for d in enumerate(dirs):
      s= SeasonHelper.getSeasonForFolder(d.rstrip(os.sep) or os.sep, extensionFilter)
      seasons.append(s)
    return seasons

  @staticmethod
  def getSeasonForFolder(folder, extensionFilter, minFileSizeBytes):
    utils.verifyType(minFileSizeBytes, int)    
    seasonName, seriesNum = SeasonHelper.seasonFromFolderName(folder)
    tempFiles = [fileHelper.FileHelper.joinPath(folder, f) for f in extensionFilter.filterFiles(os.listdir(folder))]
    files = [f for f in tempFiles if fileHelper.FileHelper.isFile(f) and fileHelper.FileHelper.getFileSize(f) > minFileSizeBytes]
    s = None
    if not seasonName == episode.UNRESOLVED_NAME or len(files):
      sourceMap = SeasonHelper.getSourceEpisodeMapFromFilenames(files)
      destMap = episode.EpisodeMap()
      if seasonName != episode.UNRESOLVED_NAME:
        seasonName, destMap = SeasonHelper.getSeasonInfo(seasonName, seriesNum)
      s = season.Season(seasonName, seriesNum, sourceMap, destMap, folder)
      s.inputFolder = folder
    return s
    
  @staticmethod
  def setCache(data):
    utils.verifyType(data, dict)
    global _CACHE
    _CACHE = data

  @staticmethod
  def cache():
    global _CACHE
    return _CACHE
  
  @staticmethod
  def getSeasonInfo(seasonName, seriesNum, useCache=True):
    """ retrieves season from cache or tvdb if not present """
    global _CACHE
    epMap = None
    
    cacheKey = utils.sanitizeString("{} ({})".format(seasonName, seriesNum))
    if useCache and cacheKey in _CACHE:
      epMap = _CACHE[cacheKey]
    else:
      seasonName, epMap = SeasonHelper.getSeasonInfoFromTVDB(seasonName, seriesNum)
      if epMap != episode.EpisodeMap():
        newKey = utils.sanitizeString("{} ({})".format(seasonName, seriesNum))
        cachedEpMap = copy.copy(epMap)
        _CACHE[newKey] = cachedEpMap
        _CACHE[cacheKey] = cachedEpMap
    return seasonName, epMap    
  
  @staticmethod
  def setSeasonInfo(seasonName, seriesNum, item): 
    utils.verifyType(item, episode.EpisodeMap)
    global _CACHE
    _CACHE[utils.sanitizeString("{} ({})".format(seasonName, seriesNum))] = item  