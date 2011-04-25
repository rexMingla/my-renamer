#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import copy
import os
import re

from tvdb_api import tvdb_api
from app import utils

import episode
import extension
import outputFormat
import season

class SeasonHelper:
  @staticmethod
  def _escapedFileExtensions():
    return extension.FileExtensions.escapedFileTypeString()

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
    episodeRegex = "^.*?(\\d\\d?)\\D*%s$" % SeasonHelper._escapedFileExtensions()
    m = re.match(episodeRegex, ep, flags=re.IGNORECASE)
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
    epRegex = "^.{%d}(\\d\\d?).*%s$" % (index, SeasonHelper._escapedFileExtensions())
    for f in files:
      epNum = episode.UNRESOLVED_KEY
      if index >= 0:
        m = re.match(epRegex, f)
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
  def getMatchIndex(files):
    """search for two concecutive numbers where the second ones are the same"""
    """a little dodgy. should check for best matching files"""
    utils.verifyType(files, list)
    index = -1
    if len(files) > 1:
      fileA = files[0]
      fileB = files[1]
      minLen = len(fileA)
      if len(fileB) < minLen:
        minLen = len(fileB)
      for i in range(minLen-1):
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
    eps = episode.EpisodeMap()
    utils.verifyType(files, list)    
    
    tmpMaps = []
    tmpMaps.append(SeasonHelper.episodeMapFromFilenames(files))
    index = SeasonHelper.getMatchIndex(files)
    if index != -1:
      tmpMaps.append(SeasonHelper.episodeMapFromIndex(index, files))
      for m in tmpMaps:
        if len(m.matches_) > len(eps.matches_):
          eps = m    
    return eps 
  
  @staticmethod
  def getFolders(rootFolder, isRecursive):
    utils.verifyType(rootFolder, str)
    utils.verifyType(isRecursive, bool)
    folders = []
    rootFolder = rootFolder.replace("\\", "/")
    if not isRecursive:
      if os.path.exists(rootFolder):
        folders.append(rootFolder)
    else:
      for root, dirs, files in os.walk(rootFolder):
        folders.append(root)      
    return folders 

  @staticmethod
  def getSeasonsForFolders(rootFolder, isRecursive):
    utils.verifyType(rootFolder, str)
    utils.verifyType(isRecursive, bool)
    seasons = []
    dirs = SeasonHelper.getFolders(rootFolder, isRecursive)
    for d in dirs:
      seasonName, seriesNum = SeasonHelper.seasonFromFolderName(d)
      files = extension.FileExtensions.filterFiles(os.listdir(d))
      if not seasonName == episode.UNRESOLVED_NAME or len(files):
        sourceMap = SeasonHelper.getSourceEpisodeMapFromFilenames(files)
        destMap = SeasonHelper.getDestinationEpisodeMapFromTVDB(seasonName, seriesNum)
        s = season.Season(seasonName, seriesNum, sourceMap, destMap)
        seasons.append(s)
    return seasons

