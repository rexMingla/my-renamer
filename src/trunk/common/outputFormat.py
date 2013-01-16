#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Generates an output filename based on TvInputValues attributes
# --------------------------------------------------------------------------------------------------------------------
import abc
import re

from common import utils
from fileHelper import FileHelper

CONDITIONAL_START = "%("
CONDITIONAL_END = ")%"
_RE_CONDITIONAL = re.compile("({}.*?{})".format(re.escape(CONDITIONAL_START), re.escape(CONDITIONAL_END)))

def _leftPad(val, places=2):
  ret = utils.toString(val).zfill(places)
  return ret

def _wrapReplaceStr(val):
  return "<{}>".format(val)

# --------------------------------------------------------------------------------------------------------------------
class InputValues(object):
  __metaclass__ = abc.ABCMeta
  
  DEFAULT_FORMAT_STR = ""
  
  def __init__(self, info=None):
    super(InputValues, self).__init__()
    self.info = info
    
  @abc.abstractmethod
  def getValues(self, info=None):
    pass
    
# --------------------------------------------------------------------------------------------------------------------
class TvInputValues(InputValues):
  """ Configurable attributes for output. """
  KEY_SHOW_NAME  = _wrapReplaceStr("show")
  KEY_SERIES_NUM = _wrapReplaceStr("s_num")
  KEY_EP_NUM     = _wrapReplaceStr("ep_num") 
  KEY_EP_NAME    = _wrapReplaceStr("ep_name")  
  DEFAULT_FORMAT_STR = "<show> - S<s_num>E<ep_num> - <ep_name>"

  def __init__(self, info=None):
    super(TvInputValues, self).__init__(info)    
    
  def getValues(self, info=None):
    ret = {}
    info = info or self.info
    if info:
      ret = {TvInputValues.KEY_SHOW_NAME:  info.showName,
             TvInputValues.KEY_SERIES_NUM: _leftPad(info.seasonNum),
             TvInputValues.KEY_EP_NUM:     _leftPad(info.epNum),
             TvInputValues.KEY_EP_NAME:    info.epName}  
    return ret
    
# --------------------------------------------------------------------------------------------------------------------
class MovieInputValues(InputValues):
  """ Configurable attributes for output. """
  KEY_TITLE  = _wrapReplaceStr("t")
  KEY_YEAR   = _wrapReplaceStr("y")
  KEY_GENRE  = _wrapReplaceStr("g")  
  KEY_DISC   = _wrapReplaceStr("p")  
  KEY_SERIES = _wrapReplaceStr("s")
  DEFAULT_FORMAT_STR = "<g>/%(<s> - )%<t> (<y>)%( - Disc <p>)%"

  def __init__(self, info=None):
    super(MovieInputValues, self).__init__(info)
    
  def getValues(self, info=None):
    ret = {}
    info = info or self.info
    if info:
      ret = {MovieInputValues.KEY_TITLE: info.title,
             MovieInputValues.KEY_YEAR:  str(info.year),
             MovieInputValues.KEY_GENRE: info.getGenre(""),
             MovieInputValues.KEY_DISC: str(info.disc or ""),
             MovieInputValues.KEY_SERIES: info.series}
    return ret

# --------------------------------------------------------------------------------------------------------------------
class OutputFormat(object):
  """ 
  Resolution of input map to create output filename. 
  Eg. 
  >>> inputValues = tvImpl.AdvancedEpisodeInfo("Entourage", 1, 7, "The Scene")
  >>> outputFormat = OutputFormat("<show_name> S<season_num>E<ep_num> <ep_name>)
  >>> outputFormat.outputToString(inputValues, ".mpg")
  Entourage S01E07 The Scene.mpg
  
  """
  
  def __init__(self, formatStr):
    super(OutputFormat, self).__init__()
    utils.verifyType(formatStr, str)
    self.formatStr = formatStr
    
  def outputToString(self, inputs, ext="", path=""):
    utils.verifyType(inputs, InputValues)
    utils.verifyType(ext, str)
    ret = self.formatStr
    keyValues = inputs.getValues().items()
    for match in _RE_CONDITIONAL.finditer(ret):
      text = match.group(1)
      newText = ""
      if any(key in text and value for key, value in keyValues):
        childFormat = OutputFormat(text[len(CONDITIONAL_START):-len(CONDITIONAL_END)]) #strip delimiters
        newText = childFormat.outputToString(inputs)
      ret = ret.replace(text, newText, 1)
    if path:
      ret = FileHelper.joinPath(path, ret)
    for key, value in keyValues: #TODO: fix this. i'm sure there is a built in function for this.
      ret = ret.replace(key, str(value))
    return "".join([ret, ext])

  