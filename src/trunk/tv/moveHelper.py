#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from app import utils, outputWidget

# -----------------------------------------------------------------------------------
class MoveHelper:
  FAILED            = -2
  INVALID_FILE      = -1
  MOVED             = 1
  NO_OVERWRITE      = 2
  
  def __init__(self, settings):
    utils.verifyType(settings, outputWidget.OutputSettings)
    self_.settings_ = settings

  def moveFile(self, source, dest):
    utils.verifyType(source, str)
    utils.verifyType(dest, str)
    
    if source == dest and settings_:
      return False