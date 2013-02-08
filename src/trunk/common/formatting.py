#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Generates an output filename based on TvInputValues attributes
# --------------------------------------------------------------------------------------------------------------------
import re

from common import utils
from common import file_helper

CONDITIONAL_START = "%("
CONDITIONAL_END = ")%"
_RE_CONDITIONAL = re.compile("({}.*?{})".format(re.escape(CONDITIONAL_START), re.escape(CONDITIONAL_END)))

def _left_pad(val, places=2):
  ret = utils.to_string(val).zfill(places)
  return ret

def _wrap_replace_str(val):
  return "<{}>".format(val)

# --------------------------------------------------------------------------------------------------------------------
class BaseNameFormatter(object):
  DEFAULT_FORMAT_STR = ""
  
  def __init__(self):
    super(BaseNameFormatter, self).__init__()
    
  def get_name(self, fmt, item, folder=None):
    if folder is None:
      folder = item.output_folder
    return self.get_name_from_info(fmt, item.get_info(), item.ext, folder)
    
  def get_name_from_info(self, fmt, info, ext="", folder=""):
    ret = file_helper.FileHelper.join_path(folder, fmt)
    key_values = self.get_values(info).items()    
    for match in _RE_CONDITIONAL.finditer(ret):
      text = match.group(1)
      new_text = ""
      if any(key in text and value for key, value in key_values):
        new_text = self.get_name_from_info(text[len(CONDITIONAL_START):-len(CONDITIONAL_END)], info) #strip delimiters
      ret = ret.replace(text, new_text)
    for key, value in key_values: #TODO: fix this. i'm sure there is a built in function for this.
      ret = ret.replace(key, str(value))
    return "".join([ret, ext])
  
  def get_values(self, info):
    raise NotImplementedError("BaseNameFormatter.get_values not implemented")
    
# --------------------------------------------------------------------------------------------------------------------
class TvNameFormatter(BaseNameFormatter):
  """ Configurable attributes for output. """
  KEY_SHOW_NAME  = _wrap_replace_str("show")
  KEY_SERIES_NUM = _wrap_replace_str("s_num")
  KEY_EP_NUM     = _wrap_replace_str("ep_num") 
  KEY_EP_NAME    = _wrap_replace_str("ep_name")  
  DEFAULT_FORMAT_STR = "<show> - S<s_num>E<ep_num> - <ep_name>"

  def __init__(self):
    super(TvNameFormatter, self).__init__()    
    
  def get_values(self, info):
    ret = {}
    if info:
      ret = {TvNameFormatter.KEY_SHOW_NAME:  info.show_name,
             TvNameFormatter.KEY_SERIES_NUM: _left_pad(info.season_num),
             TvNameFormatter.KEY_EP_NUM:     _left_pad(info.ep_num),
             TvNameFormatter.KEY_EP_NAME:    info.ep_name}  
    return ret
    
# --------------------------------------------------------------------------------------------------------------------
class MovieNameFormatter(BaseNameFormatter):
  """ Configurable attributes for output. """
  KEY_TITLE  = _wrap_replace_str("t")
  KEY_YEAR   = _wrap_replace_str("y")
  KEY_GENRE  = _wrap_replace_str("g")  
  KEY_DISC   = _wrap_replace_str("p")  
  KEY_SERIES = _wrap_replace_str("s")
  DEFAULT_FORMAT_STR = "<g>/%(<s> - )%<t> (<y>)%( - Disc <p>)%"

  def __init__(self):
    super(MovieNameFormatter, self).__init__()
    
  def get_values(self, info):
    ret = {}
    if info:
      ret = {MovieNameFormatter.KEY_TITLE: info.title,
             MovieNameFormatter.KEY_YEAR:  str(info.year),
             MovieNameFormatter.KEY_GENRE: info.get_genre(""),
             MovieNameFormatter.KEY_DISC: str(info.part or ""),
             MovieNameFormatter.KEY_SERIES: info.series}
    return ret
