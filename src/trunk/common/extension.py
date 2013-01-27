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
      self.set_extension_from_string(extensions)
    else:
      self.set_extension_from_list(extensions)
  
  @staticmethod
  def delimiter():
    return " "

  def set_extension_from_string(self, text):
    #utils.verify_type(text, str)
    self.set_extension_from_list(text.split(FileExtensions.delimiter()))

  def set_extension_from_list(self, obj):
    #utils.verify_type(l, list)
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
  
  def extension_string(self):
    return FileExtensions.delimiter().join(self._extensions)
  
  def filter_files(self, files):
    """ Return list of files matching extension filter """
    #utils.verify_type(files, list)
    ret = []
    if self == ALL_FILE_EXTENSIONS:
      ret = files
    else:
      ret = [filename for filename in files for ext in self._extensions if filename.lower().endswith(ext)]
    return ret
  
ALL_FILE_EXTENSIONS         = FileExtensions([FileExtensions.ALL_FILES])
DEFAULT_VIDEO_EXTENSIONS    = FileExtensions([".avi", ".divx", ".mkv", ".mpg", ".mp4", ".vob", ".wmv"])
DEFAULT_SUBTITLE_EXTENSIONS = FileExtensions([".sub", ".srt", ".rar", ".sfv"])
