#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Helper functions associated with tv series 
# --------------------------------------------------------------------------------------------------------------------
import copy
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

_RE_FOLDER_MATCH_1 = re.compile(r"^.*{0}(?P<name>.*){0}(?:season|series)\s+(?P<num>\d+).*$".format(re.escape(os.sep)), 
                                flags=re.IGNORECASE) #/show/season
_RE_FOLDER_MATCH_2 = re.compile(r"^.*{}(?P<name>.*)\s+\-\s+(?:season|series)\s+(?P<num>\d+).*$".format(re.escape(os.sep)), 
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
  def episodeNumFromLastNumInFilename(ep):
    utils.verifyType(ep, str)
    epNum = episode.UNRESOLVED_KEY
    m = _RE_EPISODE_MATCH.match(fileHelper.FileHelper.basename(ep))
    if m:
      epNum = int(m.group(1))
      utils.logNotSet("episode: {} #:{}".format(ep, epNum), 1)
    else:
      utils.logNotSet("unresolved: {}".format(ep), 1)
    return epNum

  @staticmethod
  def episodeMapFromIndex(index, files):
    utils.verifyType(files, list)
    epMap = episode.EpisodeMap()
    epRegex = "^.{{{}}}(\\d\\d?).*\\.[^\\.]*$".format(index)
    for f in files:
      epNum = episode.UNRESOLVED_KEY
      if index >= 0:
        m = re.match(epRegex, fileHelper.FileHelper.basename(f))
        if m:
          epNum = int(m.group(1))
      epMap.addItem(episode.SourceEpisode(epNum, f))
    return epMap

  @staticmethod
  def episodeMapFromFilenames(files):
    utils.verifyType(files, list)
    epMap = episode.EpisodeMap()
    for f in files:
      epNum = SeasonHelper.episodeNumFromLastNumInFilename(f)
      epMap.addItem(episode.SourceEpisode(epNum, f))
    return epMap
  
  @staticmethod
  def _getMatchTestFiles(files):
    left = None
    right = None
    bestMatchIndex = -1
    basenames = [fileHelper.FileHelper.basename(f) for f in files]
    for i, fa in enumerate(basenames):
      for fb in basenames[i+1:]:
        matchIndex = 0
        for i, vals in enumerate(itertools.izip(fa, fb)):
          if vals[0] != vals[1]:
            matchIndex = i
            break
        if matchIndex > bestMatchIndex:
          left = fa
          right = fb
          bestMatchIndex = matchIndex
    return left, right
    
  @staticmethod
  def getMatchIndex(files, startIndex=0):
    utils.verifyType(files, list)
    utils.verifyType(startIndex, int)
    index = -1
    fileA, fileB = SeasonHelper._getMatchTestFiles(files)
    if fileA and fileB:
      partsA = [fileA[i:i+2] for i in range(len(fileA) - 1)]
      partsB = [fileB[i:i+2] for i in range(len(fileB) - 1)]
      for i, parts in enumerate(itertools.izip(partsA, partsB)):
        a, b = parts
        if a[0] == b[0]:
          if re.match("\\d{2}", a) and re.match("\\d{2}", b) and not a == b:
            index = i
            break
        else:
          break
    return index
  
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
        show = episode.DestinationEpisode(int(ep["episodenumber"]), utils.sanitizeString(ep["episodename"]))
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
  def getSourceEpisodeMapFromFilenames(files):
    utils.verifyType(files, list)    
    
    tmpMaps = []
    eps = None     
    index = SeasonHelper.getMatchIndex(files)
    if index != episode.UNRESOLVED_KEY:
      match = SeasonHelper.episodeMapFromIndex(index, files)
      tmpMaps.append(match)
    tmpMaps.append(SeasonHelper.episodeMapFromFilenames(files))
    for m in tmpMaps:
      if not eps or len(m.matches) > len(eps.matches):
        eps = m    
    return eps 
  
  @staticmethod
  def getFolders(rootFolder, isRecursive):
    utils.verifyType(rootFolder, str)
    utils.verifyType(isRecursive, bool)
    folders = []
    rootFolder = fileHelper.FileHelper.replaceSeparators(rootFolder, os.sep)
    if not isRecursive:
      if fileHelper.FileHelper.dirExists(rootFolder):
        folders.append(rootFolder)
    else:
      for root, dirs, files in os.walk(rootFolder):
        folders.append(root)      
    return folders 

  @staticmethod
  def getSeasonsForFolders(rootFolder, isRecursive, extensionFilter):
    utils.verifyType(rootFolder, str)
    utils.verifyType(isRecursive, bool)
    utils.verifyType(extensionFilter, extension.FileExtensions)
    seasons = []
    dirs = SeasonHelper.getFolders(rootFolder, isRecursive)
    for d in enumerate(dirs):
      s= SeasonHelper.getSeasonForFolder(d, extensionFilter)
      seasons.append(s)
    return seasons

  @staticmethod
  def getSeasonForFolder(folder, extensionFilter):
    seasonName, seriesNum = SeasonHelper.seasonFromFolderName(folder)
    tempFiles = [fileHelper.FileHelper.joinPath(folder, f) for f in extensionFilter.filterFiles(os.listdir(folder))]
    files = [f for f in tempFiles if fileHelper.FileHelper.isFile(f)]
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
    cacheKey = utils.sanitizeString("{} ({})".format(seasonName, seriesNum))
    global _CACHE
    epMap = None
    if useCache and cacheKey in _CACHE:
      epMap = _CACHE[cacheKey]
    else:
      seasonName, epMap = SeasonHelper.getSeasonInfoFromTVDB(seasonName, seriesNum)
      if epMap != episode.EpisodeMap():
        _CACHE[cacheKey] = copy.copy(epMap)
        newKey = utils.sanitizeString("{} ({})".format(seasonName, seriesNum))
        if newKey != cacheKey:
          _CACHE[newKey] = copy.copy(epMap)
    return seasonName, epMap    