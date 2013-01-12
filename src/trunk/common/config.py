#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Website:             http://code.google.com/p/dps-x509/
# Purpose of document: Config data
# --------------------------------------------------------------------------------------------------------------------
import extension
import interfaces
import utils

CONFIG_VERSION = "1.0"
    
# --------------------------------------------------------------------------------------------------------------------
class BaseConfig(object):
  pass

# --------------------------------------------------------------------------------------------------------------------
class InputConfig(BaseConfig):
  def __init__(self):
    super(InputConfig, self).__init__()
    self.folder = ""
    self.recursive = True
    self.allExtensions = False
    self.extensions = extension.DEFAULT_VIDEO_EXTENSIONS.extensionString()
    self.allFileSizes = False
    self.minFileSizeBytes = utils.MIN_VIDEO_SIZE_BYTES
    self.sources = []
  
  def getExtensions(self):
    return extension.ALL_FILE_EXTENSIONS if self.allExtensions else extension.FileExtensions(self.extensions.split())

  def getMinFileSizeBytes(self):
    return 0 if self.allFileSizes else self.minFileSizeBytes

# --------------------------------------------------------------------------------------------------------------------
class WorkbenchConfig(BaseConfig):
  def _init__(self):
    super(WorkbenchConfig, self).__init__()
    
# --------------------------------------------------------------------------------------------------------------------
class OutputConfig(BaseConfig):
  def __init__(self):
    self.format = None
    self.folder = ""
    self.useSource = True
    self.isMove = True
    self.dontOverwrite = True
    self.showHelp = True
    self.actionSubtitles = True
    self.subtitleExtensions = extension.DEFAULT_SUBTITLE_EXTENSIONS.extensionString()
    
  def getOutputFolder(self):
    return self.folder if self.useSource else ""

  def getSubtitles(self):
    return [] if not self.actionSubtitles else extension.FileExtensions(self.subtitleExtensions).extensionString().split()
    
# --------------------------------------------------------------------------------------------------------------------
class MainWindowConfig(BaseConfig):
  def __init__(self):
    super(MainWindowConfig, self).__init__()
    self.geo = "AdnQywABAAAAAABbAAAACQAABEsAAALmAAAAYwAAACcAAARDAAAC3gAAAAAAAA=="
    self.state = "AAAA/wAAAAD9AAAAAgAAAAIAAAPhAAAAsvwBAAAAAfsAAAAcAEkAbgBwAHUAdAAgAFMAZQB0AHQAaQBuAGcAcwEAAAAAAAAD4QAAAKMA////AAAAAwAAA+EAAADU/AEAAAAC+wAAAB4ATwB1AHQAcAB1AHQAIABTAGUAdAB0AGkAbgBnAHMBAAAAAAAAAnIAAAGIAP////sAAAAWAE0AZQBzAHMAYQBnAGUAIABMAG8AZwEAAAJ2AAABawAAAHsA////AAAD4QAAAPMAAAAEAAAABAAAAAgAAAAI/AAAAAEAAAACAAAAAQAAABoAYQBjAHQAaQBvAG4AVABvAG8AbABCAGEAcgEAAAAA/////wAAAAAAAAAA"
    self.dontShows = {}
    self.mode = interfaces.Mode.MOVIE_MODE
    self.autoStart = False
    self.configVersion = "0.0"
    
# --------------------------------------------------------------------------------------------------------------------
class TvWorkBenchConfig(BaseConfig):
  def __init__(self):
    super(TvWorkBenchConfig, self).__init__()
    self.state = "AAAA/wAAAAAAAAABAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA14AAAAFAQAAAQAAAAAAAAAAAAAAAGT/////AAAAgQAAAAAAAAAFAAABJQAAAAEAAAAAAAAAVgAAAAEAAAAAAAAA7QAAAAEAAAAAAAAAVwAAAAEAAAAAAAAAnwAAAAEAAAAA"
    
# --------------------------------------------------------------------------------------------------------------------
class MovieWorkBenchConfig(BaseConfig):
  def __init__(self):
    super(MovieWorkBenchConfig, self).__init__()
    self.noYearAsError = True
    self.noGenreAsError = True
    self.duplicateAsError = True
    self.state = "AAAA/wAAAAAAAAABAAAAAQAAAAABAAAAAAAAAAAAAAAAAAAAAAAAA14AAAAJAAEAAQAAAAAAAAAAAAAAAGT/////AAAAhAAAAAAAAAAJAAAAGQAAAAEAAAACAAAAmQAAAAEAAAAAAAAA4wAAAAEAAAAAAAAAQgAAAAEAAAAAAAAAPwAAAAEAAAAAAAAAZAAAAAEAAAAAAAAAUAAAAAEAAAAAAAAARQAAAAEAAAAAAAAATwAAAAEAAAAA"
    self.seriesList = []    