#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Helper functions associated with tv series 
# --------------------------------------------------------------------------------------------------------------------
import os
import re

try:
  from tvdb_api import tvdb_api
except ImportError:
  assert(False)

from common import extension, utils
import episode
import fileHelper
import season

class SeasonHelper:
  """ Collection of tv series functions. """
  @staticmethod
  def seasonFromFolderName(folder):
    utils.verifyType(folder, str)
    folder = folder.replace("\\","/")
    if folder.endswith("/"):
      folder = folder[:-1]
    splitFolderRegex = "^.*/(.*)/(?:season|series)\\s+(\\d+)$"     #/show/season
    sameFolderRegex  = "^.*/(.*)\\s+\\-\\s+(?:season|series)\\s+(\\d+)$"  #/show - season
    show = episode.UNRESOLVED_NAME
    seriesNum = -1
    m = re.match(splitFolderRegex, folder, flags=re.IGNORECASE)
    if not m:
      m = re.match(sameFolderRegex, folder, flags=re.IGNORECASE)
    if m:
      show = m.group(1)
      seriesNum = utils.toInt(m.group(2))
    return show, seriesNum

  @staticmethod
  def episodeNumFromLastNumInFilename(ep):
    utils.verifyType(ep, str)
    episodeRegex = "^.*?(\\d\\d?)\\D*\\.[^\\.]*$"
    m = re.match(episodeRegex, fileHelper.FileHelper.basename(ep), flags=re.IGNORECASE)
    epNum = episode.UNRESOLVED_KEY
    if m:
      epNum = int(m.group(1))
      utils.out("episode: %s #:%d" % (ep, epNum), 1)
    else:
      utils.out("** unresolved: %s" % ep, 1)
    return epNum

  @staticmethod
  def episodeMapFromIndex(index, files):
    utils.verifyType(files, list)
    epMap = episode.EpisodeMap()
    epRegex = "^.{%d}(\\d\\d?).*\\.[^\\.]*$" % index
    for f in files:
      epNum = episode.UNRESOLVED_KEY
      if index >= 0:
        m = re.match(epRegex, fileHelper.FileHelper.basename(f))
        if m:
          epNum = utils.toInt(m.group(1))
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
    for i in range(len(files)):
      fileA = fileHelper.FileHelper.basename(files[i])
      for j in range(i+1,len(files)):
        fileB = fileHelper.FileHelper.basename(files[j])
        minLen = len(fileA)
        if len(fileB) < minLen:
          minLen = len(fileB)
        matchIndex = 0
        for k in range(minLen):
          if not fileA[k] == fileB[k]:
            matchIndex = k
            break
        if matchIndex > bestMatchIndex:
          left = fileA
          right = fileB
          bestMatchIndex = matchIndex
    return left, right
    
  @staticmethod
  def getMatchIndex(files, startIndex=0):
    utils.verifyType(files, list)
    utils.verifyType(startIndex, int)
    index = -1
    if len(files) > 1:
      fileA, fileB = SeasonHelper._getMatchTestFiles(files)
      if not fileA:
        fileA = files[0]
        fileB = files[1]
      minLen = len(fileA)
      if len(fileB) < minLen:
        minLen = len(fileB)
      for i in range(startIndex, minLen-1):
        if fileA[i] == fileB[i]:
          a = fileA[i:i+2]
          b = fileB[i:i+2]
          if re.match("\\d{2}", a) and re.match("\\d{2}", b) and not a == b:
            index = i
            break
        else:
          break
    return index
  
  @staticmethod
  def getDestinationEpisodeMapFromTVDB(show, seasonNum):
    utils.verifyType(show, str)
    utils.verifyType(seasonNum, int)
    eps = episode.EpisodeMap()
    try:
      tv = tvdb_api.Tvdb()
      season = tv[show][seasonNum]
      for i in season:
        ep = season[i]
        show = episode.DestinationEpisode(int(ep["episodenumber"]), str(ep["episodename"]))
        eps.addItem(show)
    except:
      utils.out("Could not find season. Show: %s seasonNum: %d" % (show, seasonNum), 1)
    return eps
    
  @staticmethod
  def getSourceEpisodeMapFromFilenames(files):
    utils.verifyType(files, list)    
    
    tmpMaps = []
    eps = None     
    index = SeasonHelper.getMatchIndex(files)
    if index != -1:
      match = SeasonHelper.episodeMapFromIndex(index, files)
      tmpMaps.append(match)
    tmpMaps.append(SeasonHelper.episodeMapFromFilenames(files))
    for m in tmpMaps:
      if not eps or len(m.matches_) > len(eps.matches_):
        eps = m    
    return eps 
  
  @staticmethod
  def getFolders(rootFolder, isRecursive):
    utils.verifyType(rootFolder, str)
    utils.verifyType(isRecursive, bool)
    folders = []
    rootFolder = rootFolder.replace("\\", "/")
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
    for d in dirs:
      seasonName, seriesNum = SeasonHelper.seasonFromFolderName(d)
      tempFiles = extensionFilter.filterFiles(os.listdir(d))
      files = []
      for f in tempFiles:
        filename = fileHelper.FileHelper.joinPath(d, f) 
        if fileHelper.FileHelper.isFile(filename):
          files.append(filename)
      if not seasonName == episode.UNRESOLVED_NAME or len(files):
        sourceMap = SeasonHelper.getSourceEpisodeMapFromFilenames(files)
        destMap = SeasonHelper.getDestinationEpisodeMapFromTVDB(seasonName, seriesNum)
        s = season.Season(seasonName, seriesNum, sourceMap, destMap, d)
        s.inputFolder_ = d
        seasons.append(s)
    return seasons

