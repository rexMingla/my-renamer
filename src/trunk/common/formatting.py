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
from file_helper import FileHelper

CONDITIONAL_START = "%("
CONDITIONAL_END = ")%"
_RE_CONDITIONAL = re.compile("({}.*?{})".format(re.escape(CONDITIONAL_START), re.escape(CONDITIONAL_END)))

def _leftPad(val, places=2):
  ret = utils.toString(val).zfill(places)
  return ret

def _wrapReplaceStr(val):
  return "<{}>".format(val)

# --------------------------------------------------------------------------------------------------------------------
class BaseNameFormatter(object):
  __metaclass__ = abc.ABCMeta
  
  DEFAULT_FORMAT_STR = ""
  
  def __init__(self):
    super(BaseNameFormatter, self).__init__()
    
  def getName(self, fmt, item, folder=None):
    if folder is None:
      folder = item.outputFolder
    return self.getNameFromInfo(fmt, item.getInfo(), item.ext, folder)
    
  def getNameFromInfo(self, fmt, info, ext="", folder=""):
    ret = FileHelper.joinPath(folder, fmt)
    keyValues = self.getValues(info).items()    
    for match in _RE_CONDITIONAL.finditer(ret):
      text = match.group(1)
      newText = ""
      if any(key in text and value for key, value in keyValues):
        newText = self.getNameFromInfo(text[len(CONDITIONAL_START):-len(CONDITIONAL_END)], info) #strip delimiters
      ret = ret.replace(text, newText)
    for key, value in keyValues: #TODO: fix this. i'm sure there is a built in function for this.
      ret = ret.replace(key, str(value))
    return "".join([ret, ext])
  
  @abc.abstractmethod
  def getValues(self, info):
    pass
    
# --------------------------------------------------------------------------------------------------------------------
class TvNameFormatter(BaseNameFormatter):
  """ Configurable attributes for output. """
  KEY_SHOW_NAME  = _wrapReplaceStr("show")
  KEY_SERIES_NUM = _wrapReplaceStr("s_num")
  KEY_EP_NUM     = _wrapReplaceStr("ep_num") 
  KEY_EP_NAME    = _wrapReplaceStr("ep_name")  
  DEFAULT_FORMAT_STR = "<show> - S<s_num>E<ep_num> - <ep_name>"

  def __init__(self):
    super(TvNameFormatter, self).__init__()    
    
  def getValues(self, info):
    ret = {}
    info = info or self.info
    if info:
      ret = {TvNameFormatter.KEY_SHOW_NAME:  info.showName,
             TvNameFormatter.KEY_SERIES_NUM: _leftPad(info.seasonNum),
             TvNameFormatter.KEY_EP_NUM:     _leftPad(info.epNum),
             TvNameFormatter.KEY_EP_NAME:    info.epName}  
    return ret
    
# --------------------------------------------------------------------------------------------------------------------
class MovieNameFormatter(BaseNameFormatter):
  """ Configurable attributes for output. """
  KEY_TITLE  = _wrapReplaceStr("t")
  KEY_YEAR   = _wrapReplaceStr("y")
  KEY_GENRE  = _wrapReplaceStr("g")  
  KEY_DISC   = _wrapReplaceStr("p")  
  KEY_SERIES = _wrapReplaceStr("s")
  DEFAULT_FORMAT_STR = "<g>/%(<s> - )%<t> (<y>)%( - Disc <p>)%"

  def __init__(self):
    super(MovieNameFormatter, self).__init__()
    
  def getValues(self, info):
    ret = {}
    info = info or self.info
    if info:
      ret = {MovieNameFormatter.KEY_TITLE: info.title,
             MovieNameFormatter.KEY_YEAR:  str(info.year),
             MovieNameFormatter.KEY_GENRE: info.getGenre(""),
             MovieNameFormatter.KEY_DISC: str(info.part or ""),
             MovieNameFormatter.KEY_SERIES: info.series}
    return ret
