#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from app import utils

def leftPad(val):
  ret = utils.toString(val).zfill(2)
  return ret

# --------------------------------------------------------------------------------------------------------------------
class InputMap:    
  KEY_SHOW_NAME  = "[show_name]"
  KEY_SERIES_NUM = "[season_num]"
  KEY_EP_NUM     = "[ep_num]"   
  KEY_EP_NAME    = "[ep_name]"  

  def __init__(self, showName, seriesNum, epNum, epName):
    utils.verifyType(showName, str)
    utils.verify(isinstance(seriesNum, str) or isinstance(seriesNum, int), "str or int")
    utils.verify(isinstance(epNum, str) or isinstance(epNum, int), "str or int")
    utils.verifyType(epName, str)
    self.data_ = {InputMap.KEY_SHOW_NAME:  showName,
                  InputMap.KEY_SERIES_NUM: leftPad(seriesNum),
                  InputMap.KEY_EP_NUM:     leftPad(epNum),
                  InputMap.KEY_EP_NAME:    epName}

HELP_INPUT_MAP    = InputMap("Show Name", "Series Number", "Episode Number", "Episode Name")
EXAMPLE_INPUT_MAP = InputMap("Entourage", 1, 7, "The Scene")
      
# --------------------------------------------------------------------------------------------------------------------
class OutputFormat:
  def __init__(self, formatStr):
    utils.verifyType(formatStr, str)
    self.formatStr_ = formatStr
    
  def outputToString(self, inputs, ext=""):
    utils.verifyType(inputs, InputMap)
    utils.verifyType(ext, str)
    ret = self.formatStr_
    for key in inputs.data_.keys():
      ret = ret.replace(key, inputs.data_[key])
    return ret + ext

DEFAULT_FORMAT = OutputFormat("[ep_num] - [ep_name]")
  