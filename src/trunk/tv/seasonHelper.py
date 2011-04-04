#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import sys 
import os
sys.path.insert(0, os.path.abspath(__file__+"/../../"))
import re

import tvdb_api

import app
import episode
import extension

class SeasonHelper:
  NO_MATCH_NAME = ""

  @staticmethod
  def _escapedFileExtensions():
    return extension.FileExtensions.escapedFileTypeString()

  @staticmethod
  def seasonFromFolderName(folder):
    app.utils.verifyType(folder, str)
    splitFolderRegex = "^.*/(.*)/(?:season|series)\\s+(\\d+)$"     #/show/season
    sameFolderRegex  = "^.*/(.*)\\s+(?:season|series)\\s+(\\d+)$"  #/show - season
    show = SeasonHelper.NO_MATCH_NAME
    seriesNum = -1
    m = re.match(splitFolderRegex, folder, flags=re.IGNORECASE)
    if not m:
      m = re.match(sameFolderRegex, folder, flags=re.IGNORECASE)
    if m:
      show = m.group(1)
      seriesNum = app.utils.toInt(m.group(2))
    return show, seriesNum

  @staticmethod
  def episodeNumFromFilenames(episode):
    app.utils.verifyType(episode, str)
    episodeRegex = "^.*?(\\d\\d?)\\D*%s$" % SeasonHelper._escapedFileExtensions()
    m = re.match(episodeRegex, episode, flags=re.IGNORECASE)
    epNum = episode.UNRESOLVED_KEY
    if m:
      epNum = int(m.group(1))
      out("episode: %s #:%d" % (episode, epNum), 1)
    else:
      out("** unresolved: %s" % episode, 1)
    return epNum

  @staticmethod
  def episodeMapFromIndex(index, files):
    epMap = episode.EpisodeMap()
    if index != -1:
      epRegex = "^.{%d}(\\d\\d?).*%s$" % (index, SeasonHelper._escapedFileExtensions())
      for f in files:
        m = re.match(epRegex, f)
        epNum = episode.UNRESOLVED_KEY
        if m:
          epNum = app.utils.toInt(m.group(1))
        epMap.addItem(episode.SourceEpisode(epNum, f))
    return epMap

  @staticmethod
  def episodeMapFromSeason(files):
    epMap = episode.EpisodeMap()
    for f in files:
      epNum = episodeNumFromShow(f)
      epMap.addItem(episode.SourceEpisode(epNum, f))
    return epMap

  @staticmethod
  def getMatchIndex(files):
    """search for two concecutive numbers where the second ones are the same"""
    """a little dodgy. should check for best matching files"""
    app.utils.verifyType(files, list)
    index = -1
    if len(files) > 1:
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
    app.utils.verifyType(show, str)
    app.utils.verifyType(seasonNum, int)
    eps = episode.EpisodeMap()
    try:
      tv = tvdb_api.Tvdb()
      season = tv[show][seasonNum]
      for i in season:
        ep = season[i]
        show = DestinationEpisode(int(show["episodenumber"]), show["episodename"])
        eps.addItem(show)
    except:
      out("Could not find season. Show: %s seasonNum: %d" % (show, seasonNum), 1)
    return eps
    
  @staticmethod
  def getSourceEpisodeMapFromFilenames(files):
    eps = episode.EpisodeMap()
    app.utils.verifyType(files, list)    
    
    tmpMaps = []
    tmpMaps.append(SeasonHelper.episodeNumFromFilenames(files))
    index = getMatchIndex(files)
    if index != -1:
      tmpMaps.append(SeasonHelper.episodeMapFromIndex(index, files))
      for m in tmpMaps:
        if len(m.matches_) > len(eps.matches_):
          eps = m    
    return eps  
