#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Helper functions associated with tv series
# --------------------------------------------------------------------------------------------------------------------
import os
import re

from media.base import manager as base_manager
from common import file_helper
from media.tv import types as tv_types
from media.tv import client as tv_client

_RE_FOLDER_MATCH_1 = re.compile(r"^.*{0}(?P<name>.*){0}"
                                r"(?:season|series)\s+(?P<num>\d+)[^{0}]*$".format(re.escape(os.sep)),
                                flags=re.IGNORECASE) #/show/season
_RE_FOLDER_MATCH_2 = re.compile(r"^.*{0}(?P<name>.*)\s+\-\s+(?:season|series)"
                                r"\s+(?P<num>\d+)[^{0}]*$".format(re.escape(os.sep)),
                                flags=re.IGNORECASE) #/show - season
_RE_EPISODE_MATCH = re.compile(r"^.*?(?P<ep_num>\d\d?)\D*\.[^\.]*$")

# --------------------------------------------------------------------------------------------------------------------
class TvHelper:
  @staticmethod
  def seasonFromFolderName(folder):
    #utils.verifyType(folder, str)
    folder = file_helper.FileHelper.replaceSeparators(folder, os.sep)
    show = tv_types.UNRESOLVED_NAME
    series_num = tv_types.UNRESOLVED_KEY
    for regex in (_RE_FOLDER_MATCH_1, _RE_FOLDER_MATCH_2):
      match = regex.match(folder)
      if match:
        show = match.group("name")
        series_num = int(match.group("num"))
        break
    return tv_types.TvSearchParams(show, series_num)

  @staticmethod
  def getSourcesFromFilenames(filenames):
    def getEpisodeNumsFromFilename(filename):
      """ returns a list of numbers for the filename """
      return [int(match[-2:]) for match in re.findall(r"\d+", file_helper.FileHelper.basename(filename))] or \
             [tv_types.UNRESOLVED_KEY]

    if not filenames:
      return tv_types.SourceFiles()

    eps = [(filename, getEpisodeNumsFromFilename(filename)) for filename in filenames]
    max_indexes = max(len(episode[1]) for episode in eps)
    ret = []
    for i in range(max_indexes):
      sources = tv_types.SourceFiles()
      for filename, indexes in eps:
        sources.append(tv_types.SourceFile(indexes[i] if i < len(indexes) else tv_types.UNRESOLVED_KEY, filename))
      ret.append(sources)
    for i in range(max_indexes):
      sources = tv_types.SourceFiles()
      for filename, indexes in eps:
        sources.append(tv_types.SourceFile(indexes[- i - 1] if i < len(indexes) else tv_types.UNRESOLVED_KEY, filename))
      ret.append(sources)
    return max(ret, key=lambda sources: len([source for source in sources if source.ep_num != tv_types.UNRESOLVED_KEY]))

# --------------------------------------------------------------------------------------------------------------------
class TvManager(base_manager.BaseManager):
  """ Collection of tv series functions. """
  helper = TvHelper

  def __init__(self):
    super(TvManager, self).__init__(tv_client.getInfoClientHolder())

  def getSeasonForFolder(self, folder, extension_filter, min_file_size_bytes):
    #utils.verifyType(min_file_size_bytes, int)
    search_params = TvHelper.seasonFromFolderName(folder)
    temp_files = [file_helper.FileHelper.joinPath(folder, i)
                  for i in extension_filter.filterFiles(os.listdir(folder))]
    files = [i for i in temp_files
             if file_helper.FileHelper.isFile(i) and file_helper.FileHelper.getFileSize(i) > min_file_size_bytes]
    season = None
    if not search_params.show_name == tv_types.UNRESOLVED_NAME or len(files):
      sources = TvHelper.getSourcesFromFilenames(files)
      info = tv_types.SeasonInfo(search_params.show_name, search_params.season_num)
      if search_params.show_name != tv_types.UNRESOLVED_NAME:
        info = self.getInfo(search_params)
      season = tv_types.Season(folder, info, sources)
    return season

_MANAGER = None

def getManager():
  global _MANAGER
  if not _MANAGER:
    _MANAGER = TvManager()
  return _MANAGER
