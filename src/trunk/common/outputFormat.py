#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Generates an output filename based on TvInputMap attributes
# --------------------------------------------------------------------------------------------------------------------
from common import utils
from fileHelper import FileHelper

import re

_CONDITIONAL_START = "%("
_CONDITIONAL_END = ")%"
_RE_CONDITIONAL = re.compile("({}.*?{})".format(re.escape(_CONDITIONAL_START), re.escape(_CONDITIONAL_END)))

def _leftPad(val, places=2):
  ret = utils.toString(val).zfill(places)
  return ret

def _wrapReplaceStr(val):
  return "<{}>".format(val)

# --------------------------------------------------------------------------------------------------------------------
class InputMap(object):
  def __init__(self):
    super(InputMap, self).__init__()
    self.data = {}
    
  @staticmethod
  def helpInputMap():
    raise NotImplementedError("InputMap.helpInputMap not implemented")

  @staticmethod
  def exampleInputMap():
    raise NotImplementedError("InputMap.exampleInputMap not implemented")
  
  @staticmethod
  def defaultFormatStr():
    raise NotImplementedError("InputMap.defaultFormatStr not implemented")
    
# --------------------------------------------------------------------------------------------------------------------
class TvInputMap(InputMap):
  """ Configurable attributes for output. """
  KEY_SHOW_NAME  = _wrapReplaceStr("show_name")
  KEY_SERIES_NUM = _wrapReplaceStr("season_num")
  KEY_EP_NUM     = _wrapReplaceStr("ep_num") 
  KEY_EP_NAME    = _wrapReplaceStr("ep_name")  

  def __init__(self, showName, seriesNum, epNum, epName):
    super(TvInputMap, self).__init__()
    utils.verifyType(showName, str)
    utils.verify(isinstance(seriesNum, str) or isinstance(seriesNum, int), "str or int")
    utils.verify(isinstance(epNum, str) or isinstance(epNum, int), "str or int")
    utils.verifyType(epName, basestring)
    self.data = {TvInputMap.KEY_SHOW_NAME:  showName,
                 TvInputMap.KEY_SERIES_NUM: _leftPad(seriesNum),
                 TvInputMap.KEY_EP_NUM:     _leftPad(epNum),
                 TvInputMap.KEY_EP_NAME:    epName}

  @staticmethod
  def helpInputMap():
    return TvInputMap("Show Name", "Series Number", "Episode Number", "Episode Name")

  @staticmethod
  def exampleInputMap():
    return TvInputMap("Entourage", 1, 7, "The Scene")
  
  @staticmethod
  def defaultFormatStr():
    return "<show_name> - S<season_num>E<ep_num> - <ep_name>"
  
# --------------------------------------------------------------------------------------------------------------------
class MovieInputMap(InputMap):
  """ Configurable attributes for output. """
  KEY_TITLE  = _wrapReplaceStr("title")
  KEY_YEAR   = _wrapReplaceStr("year")
  KEY_GENRE  = _wrapReplaceStr("genre")  
  KEY_DISC   = _wrapReplaceStr("part")  
  KEY_SERIES = _wrapReplaceStr("series")  

  def __init__(self, title, year, genre, disc, series):
    super(MovieInputMap, self).__init__()
    utils.verifyType(title, str)
    utils.verifyType(genre, str)
    self.data = {MovieInputMap.KEY_TITLE: title,
                 MovieInputMap.KEY_YEAR:  str(year),
                 MovieInputMap.KEY_GENRE: genre,
                 MovieInputMap.KEY_DISC: str(disc or ""),
                 MovieInputMap.KEY_SERIES: series}

  @staticmethod
  def helpInputMap():
    return MovieInputMap("Title", "Year", "Genre", "Part", "Series")

  @staticmethod
  def exampleInputMap():
    return MovieInputMap("The Twin Towers", 2002, "action", 1, "LOTR")
  
  @staticmethod
  def defaultFormatStr():
    return "<genre>/%(<series> - )%<title> (<year>)%( - Disc <part>)%"
      
# --------------------------------------------------------------------------------------------------------------------
class OutputFormat:
  """ 
  Resolution of input map to create output filename. 
  Eg. 
  input_map.data_ = {"<show_name>":  "Entourage", 
                     "<season_num>": 1, 
                     "<ep_num>":     7, 
                     "<ep_name>":    "The Scene"}
  output_format = OutputFormat("<show_name> S<season_num>E<ep_num> <ep_name>)
  output_format.outputToString(input_map, ".mpg")
  Resolves to "Entourage S01E07 The Scene.mpg"
  """
  def __init__(self, formatStr):
    utils.verifyType(formatStr, str)
    self.formatStr = formatStr
    
  def outputToString(self, inputs, ext="", path=""):
    utils.verifyType(inputs, InputMap)
    utils.verifyType(ext, str)
    ret = self.formatStr
    for match in _RE_CONDITIONAL.finditer(ret):
      text = match.group(1)
      newText = ""
      if any(key in text and value for key, value in inputs.data.items()):
        childFormat = OutputFormat(text[len(_CONDITIONAL_START):-len(_CONDITIONAL_END)]) #strip delimiters
        newText = childFormat.outputToString(inputs)
      ret = ret.replace(text, newText, 1)
    if path:
      ret = FileHelper.joinPath(path, ret)
    for key, value in inputs.data.items(): #todo: fix this. i'm sure there is a built in function for this.
      ret = ret.replace(key, value)
    return ret + ext

  