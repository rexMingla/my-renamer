#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Class associated with all things FileExtensions
# --------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------
class FileExtensions:
  """
  Handling of file extensions. Extensions can be loaded from a string or a list.
  Strings will be FileExtensions.delimiter separated before being cleaned as follows
  (using mpg as the example extension):
  *.mpg -> .mpg
  .mpg  -> .mpg
  mpg   -> .mpg
  Additionally, an extension list that contains "", "*", "*.*", ".*" will be resolved to FileExtensions.ALL_FILES
  for the entire list.
  """
  ALL_FILES = ".*"

  def __init__(self, extensions):
    self._extensions = []
    if isinstance(extensions, basestring):
      self.setExtensionFromString(extensions)
    else:
      self.setExtensionFromList(extensions)

  @staticmethod
  def delimiter():
    return " "

  def setExtensionFromString(self, text):
    #utils.verifyType(text, str)
    self.setExtensionFromList(text.split(FileExtensions.delimiter()))

  def setExtensionFromList(self, obj):
    #utils.verifyType(l, list)
    is_all = not obj
    sanitized = []
    for item in obj:
      if item in ["", "*", "*.*", ".*"]:
        is_all = True
        break
      else:
        #leave in format of .ext
        if item.startswith("*"):
          sanitized.append(item[1:])
        elif not item.startswith("."):
          sanitized.append(".{}".format(item))
        else:
          sanitized.append(item)
    if is_all:
      self._extensions = [FileExtensions.ALL_FILES] #make a copy
    else:
      self._extensions = sanitized

  def extensionString(self):
    return FileExtensions.delimiter().join(self._extensions)

  def filterFiles(self, files):
    """ Return list of files matching extension filter """
    #utils.verifyType(files, list)
    ret = []
    if self == ALL_FILE_EXTENSIONS:
      ret = files
    else:
      ret = [filename for filename in files for ext in self._extensions if filename.lower().endswith(ext)]
    return ret

ALL_FILE_EXTENSIONS         = FileExtensions([FileExtensions.ALL_FILES])
DEFAULT_VIDEO_EXTENSIONS    = FileExtensions([".avi", ".divx", ".mkv", ".mpg", ".mp4", ".vob", ".wmv"])
DEFAULT_SUBTITLE_EXTENSIONS = FileExtensions([".sub", ".srt", ".rar", ".sfv"])
