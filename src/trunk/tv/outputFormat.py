#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Generates an output filename based on TvInputMap attributes
# --------------------------------------------------------------------------------------------------------------------
from common import utils

def leftPad(val):
  ret = utils.toString(val).zfill(2)
  return ret

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
  KEY_SHOW_NAME  = "[show_name]"
  KEY_SERIES_NUM = "[season_num]"
  KEY_EP_NUM     = "[ep_num]"   
  KEY_EP_NAME    = "[ep_name]"  

  def __init__(self, showName, seriesNum, epNum, epName):
    super(TvInputMap, self).__init__()
    utils.verifyType(showName, str)
    utils.verify(isinstance(seriesNum, str) or isinstance(seriesNum, int), "str or int")
    utils.verify(isinstance(epNum, str) or isinstance(epNum, int), "str or int")
    utils.verifyType(epName, basestring)
    self.data = {TvInputMap.KEY_SHOW_NAME:  showName,
                 TvInputMap.KEY_SERIES_NUM: leftPad(seriesNum),
                 TvInputMap.KEY_EP_NUM:     leftPad(epNum),
                 TvInputMap.KEY_EP_NAME:    epName}

  @staticmethod
  def helpInputMap():
    return TvInputMap("Show Name", "Series Number", "Episode Number", "Episode Name")

  @staticmethod
  def exampleInputMap():
    return TvInputMap("Entourage", 1, 7, "The Scene")
  
  @staticmethod
  def defaultFormatStr():
    return "[show_name] - S[season_num]E[ep_num] - [ep_name]"
      
# --------------------------------------------------------------------------------------------------------------------
class OutputFormat:
  """ 
  Resolution of input map to create output filename. 
  Eg. 
  input_map.data_ = {"[show_name]":  "Entourage", 
                     "[season_num]": 1, 
                     "[ep_num]":     7, 
                     "[ep_name]":    "The Scene"}
  output_format = OutputFormat("[show_name] S[season_num]E[ep_num] [ep_name])
  output_format.outputToString(input_map, ".mpg")
  Resolves to "Entourage S01E07 The Scene.mpg"
  """
  def __init__(self, formatStr):
    utils.verifyType(formatStr, str)
    self.formatStr = formatStr
    
  def outputToString(self, inputs, ext=""):
    utils.verifyType(inputs, InputMap)
    utils.verifyType(ext, str)
    ret = self.formatStr
    for key, value in inputs.data.items(): #todo: fix this.
      ret = ret.replace(key, value)
    return ret + ext

  