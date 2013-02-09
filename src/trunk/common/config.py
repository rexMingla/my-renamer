#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Website:             http://code.google.com/p/dps-x509/
# Purpose of document: Config data
# --------------------------------------------------------------------------------------------------------------------
from common import extension
from common import interfaces
from common import utils

CONFIG_VERSION = "1.0"
CACHE_VERSION = "1.0"

# --------------------------------------------------------------------------------------------------------------------
class BaseConfig(object):
  pass

# --------------------------------------------------------------------------------------------------------------------
class InputConfig(BaseConfig):
  def __init__(self):
    super(InputConfig, self).__init__()
    self.folder = ""
    self.recursive = True
    self.all_extensions = False
    self.extensions = extension.DEFAULT_VIDEO_EXTENSIONS.extensionString()
    self.all_file_sizes = False
    self.min_file_size_bytes = utils.MIN_VIDEO_SIZE_BYTES
    self.sources = []

  def getExtensions(self):
    return extension.ALL_FILE_EXTENSIONS if self.all_extensions else extension.FileExtensions(self.extensions.split())

  def getMinFileSizeBytes(self):
    return 0 if self.all_file_sizes else self.min_file_size_bytes

# --------------------------------------------------------------------------------------------------------------------
class WorkbenchConfig(BaseConfig):
  def _init__(self):
    super(WorkbenchConfig, self).__init__()

# --------------------------------------------------------------------------------------------------------------------
class OutputConfig(BaseConfig):
  def __init__(self):
    self.format = None
    self.folder = ""
    self.use_source = True
    self.is_move = True
    self.dont_overwrite = True
    self.show_help = True
    self.action_subtitles = True
    self.subtitle_exts = extension.DEFAULT_SUBTITLE_EXTENSIONS.extensionString()

  def getOutputFolder(self):
    return self.folder if self.use_source else ""

  def getSubtitles(self):
    return [] if not self.action_subtitles else extension.FileExtensions(self.subtitle_exts).extensionString().split()

# --------------------------------------------------------------------------------------------------------------------
class MainWindowConfig(BaseConfig):
  def __init__(self):
    super(MainWindowConfig, self).__init__()
    self.geo = "AdnQywABAAAAAABbAAAACQAABEsAAALmAAAAYwAAACcAAARDAAAC3gAAAAAAAA=="
    self.state = "AAAA/wAAAAD9AAAAAgAAAAIAAAPhAAAAsvwBAAAAAfsAAAAcAEkAbgBwAHUAdAAgAFMAZQB0AHQAaQBuAGcAcwEAAAAAAAAD4QAAAKMA////AAAAAwAAA+EAAADU/AEAAAAC+wAAAB4ATwB1AHQAcAB1AHQAIABTAGUAdAB0AGkAbgBnAHMBAAAAAAAAAnIAAAGIAP////sAAAAWAE0AZQBzAHMAYQBnAGUAIABMAG8AZwEAAAJ2AAABawAAAHsA////AAAD4QAAAPMAAAAEAAAABAAAAAgAAAAI/AAAAAEAAAACAAAAAQAAABoAYQBjAHQAaQBvAG4AVABvAG8AbABCAGEAcgEAAAAA/////wAAAAAAAAAA"
    self.dont_shows = {}
    self.mode = interfaces.MOVIE_MODE
    self.auto_start = False
    self.config_version = CONFIG_VERSION

# --------------------------------------------------------------------------------------------------------------------
class TvWorkBenchConfig(BaseConfig):
  def __init__(self):
    super(TvWorkBenchConfig, self).__init__()
    self.state = "AAAA/wAAAAAAAAABAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA14AAAAFAQAAAQAAAAAAAAAAAAAAAGT/////AAAAgQAAAAAAAAAFAAABJQAAAAEAAAAAAAAAVgAAAAEAAAAAAAAA7QAAAAEAAAAAAAAAVwAAAAEAAAAAAAAAnwAAAAEAAAAA"

# --------------------------------------------------------------------------------------------------------------------
class MovieWorkBenchConfig(BaseConfig):
  def __init__(self):
    super(MovieWorkBenchConfig, self).__init__()
    self.no_year_as_error = True
    self.no_genre_as_error = True
    self.duplicate_as_error = True
    self.state = "AAAA/wAAAAAAAAABAAAAAQAAAAABAAAAAAAAAAAAAAAAAAAAAAAAA14AAAAJAAEAAQAAAAAAAAAAAAAAAGT/////AAAAhAAAAAAAAAAJAAAAGQAAAAEAAAACAAAAmQAAAAEAAAAAAAAA4wAAAAEAAAAAAAAAQgAAAAEAAAAAAAAAPwAAAAEAAAAAAAAAZAAAAAEAAAAAAAAAUAAAAAEAAAAAAAAARQAAAAEAAAAAAAAATwAAAAEAAAAA"
    self.series_list = []
