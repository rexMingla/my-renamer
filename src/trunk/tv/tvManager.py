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
from common import interfaces
from common import manager
from common import utils

import tvImpl
import tvInfoClient

_RE_FOLDER_MATCH_1 = re.compile(r"^.*{0}(?P<name>.*){0}(?:season|series)\s+(?P<num>\d+)[^{0}]*$".format(re.escape(os.sep)), 
                                flags=re.IGNORECASE) #/show/season
_RE_FOLDER_MATCH_2 = re.compile(r"^.*{0}(?P<name>.*)\s+\-\s+(?:season|series)\s+(?P<num>\d+)[^{0}]*$".format(re.escape(os.sep)), 
                                flags=re.IGNORECASE) #/show - season
_RE_EPISODE_MATCH = re.compile(r"^.*?(?P<epNum>\d\d?)\D*\.[^\.]*$")

# --------------------------------------------------------------------------------------------------------------------
class TvHelper:
  @staticmethod
  def seasonFromFolderName(folder):
    utils.verifyType(folder, str)
    folder = fileHelper.FileHelper.replaceSeparators(folder, os.sep)
    show = tvImpl.UNRESOLVED_NAME
    seriesNum = tvImpl.UNRESOLVED_KEY
    for regex in (_RE_FOLDER_MATCH_1, _RE_FOLDER_MATCH_2):
      m = regex.match(folder)
      if m:
        show = m.group("name")
        seriesNum = int(m.group("num"))
        break
    return tvInfoClient.TvSearchParams(show, seriesNum)
  
  @staticmethod
  def getSourcesFromFilenames(filenames):
    def getCandidateEpisodeNumsFromFilename(filename):
      """ returns a list of numbers for the filename """
      return [int(m[-2:]) for m in re.findall("\d+", fileHelper.FileHelper.basename(filename))] or [tvImpl.UNRESOLVED_KEY]

    if not filenames:
      return tvImpl.SourceFiles()
    
    eps = [(f, getCandidateEpisodeNumsFromFilename(f)) for f in filenames]
    maxIndexes = max(len(ep[1]) for ep in eps)
    ret = []
    for i in range(maxIndexes):
      sources = tvImpl.SourceFiles()
      for f, indexes in eps:
        sources.append(tvImpl.SourceFile(indexes[i] if i < len(indexes) else tvImpl.UNRESOLVED_KEY, f))
      ret.append(sources)
    for i in range(maxIndexes):
      sources = tvImpl.SourceFiles()
      for f, indexes in eps:
        sources.append(tvImpl.SourceFile(indexes[- i - 1] if i < len(indexes) else tvImpl.UNRESOLVED_KEY, f))
      ret.append(sources)
    return max(ret, key=lambda sources: len([source for source in sources if source.epNum != tvImpl.UNRESOLVED_KEY]))

# --------------------------------------------------------------------------------------------------------------------
class TvManager(manager.BaseManager):
  """ Collection of tv series functions. """
  helper = TvHelper
  
  def __init__(self):
    super(TvManager, self).__init__(tvInfoClient.getStoreHolder())

  def getSeasonsForFolders(self, rootFolder, isRecursive, extensionFilter):
    utils.verifyType(rootFolder, str)
    utils.verifyType(isRecursive, bool)
    utils.verifyType(extensionFilter, extension.FileExtensions)
    seasons = []
    dirs = TvHelper.getFolders(rootFolder, isRecursive)
    for d in enumerate(dirs):
      s= self.getSeasonForFolder(d.rstrip(os.sep) or os.sep, extensionFilter)
      seasons.append(s)
    return seasons

  def getSeasonForFolder(self, folder, extensionFilter, minFileSizeBytes):
    utils.verifyType(minFileSizeBytes, int)    
    searchParams = TvHelper.seasonFromFolderName(folder)
    tempFiles = [fileHelper.FileHelper.joinPath(folder, f) for f in extensionFilter.filterFiles(os.listdir(folder))]
    files = [f for f in tempFiles if fileHelper.FileHelper.isFile(f) and fileHelper.FileHelper.getFileSize(f) > minFileSizeBytes]
    s = None
    if not searchParams.showName == tvImpl.UNRESOLVED_NAME or len(files):
      sources = TvHelper.getSourcesFromFilenames(files)
      info = tvImpl.SeasonInfo(searchParams.showName, searchParams.seasonNum)
      if searchParams.showName != tvImpl.UNRESOLVED_NAME:
        info = self.getItem(searchParams)
      s = tvImpl.Season(folder, info, sources)
    return s 

_MANAGER = None  

def getManager():
  global _MANAGER
  if not _MANAGER:
    _MANAGER = TvManager()
  return _MANAGER