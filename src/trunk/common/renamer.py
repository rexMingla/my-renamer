#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Class responsible for the moving/copying of files
# --------------------------------------------------------------------------------------------------------------------
import abc

from common import file_helper
from common import utils

# --------------------------------------------------------------------------------------------------------------------
class BaseRenameItemGenerator(object):
  """ converts an item a BaseRenamer object """
  __metaclass__ = abc.ABCMeta
  
  def __init__(self, config=None):
    super(BaseRenameItemGenerator, self).__init__()
    self.config = config or {}
    
  @abc.abstractmethod
  def get_rename_item(self, item):
    pass

# --------------------------------------------------------------------------------------------------------------------
class RenameItemGenerator(BaseRenameItemGenerator):
  """ converts an item a BaseRenamer object """
  
  def __init__(self, formatter=None, config=None):
    super(RenameItemGenerator, self).__init__()
    self._formatter = formatter
    self.config = config or {}
    
  def get_rename_item(self, item):
    if self.config.get_output_folder():
      item.output_folder = self.config.get_output_folder()
    name = file_helper.FileHelper.sanitize_filename(self._formatter.get_name(self.config.format, item))
    return FileRenamer(item.filename, name, can_overwrite=not self.config.dont_overwrite, 
                                            keep_source=not self.config.is_move,
                                            subtitle_extensions=self.config.get_subtitles())
    
# --------------------------------------------------------------------------------------------------------------------
class BaseRenamer(object):
  """ performs rename on file """
  __metaclass__ = abc.ABCMeta
  def __init__(self):
    super(BaseRenamer, self).__init__()
    
  @abc.abstractmethod
  def perform_action(self, progress_cb=None):
    pass
    
# --------------------------------------------------------------------------------------------------------------------
class FileRenamer(BaseRenamer):
  """ Class responsible for the moving/copying of files from source to destination """ 
  SOURCE_DOES_NOT_EXIST = -4
  COULD_NOT_OVERWRITE   = -3
  FAILED                = -2
  INVALID_FILENAME      = -1
  SUCCESS               = 1
  
  @staticmethod
  def result_str(res):
    if res == FileRenamer.SOURCE_DOES_NOT_EXIST: 
      return "Source does not exist"
    elif res == FileRenamer.COULD_NOT_OVERWRITE: 
      return "Could not overwrite"
    elif res == FileRenamer.FAILED:              
      return "Failed"
    elif res == FileRenamer.INVALID_FILENAME:    
      return "Destination file invalid"
    else:
      utils.verify(res == FileRenamer.SUCCESS, "Invalid res")
      return "Success"

  def __init__(self, source, dest, can_overwrite, keep_source, subtitle_extensions=None):
    super(FileRenamer, self).__init__()
    self.source = source
    self.dest = dest
    self.can_overwrite = can_overwrite
    self.keep_source = keep_source
    self.subtitle_extensions = subtitle_extensions or []
    
  def result_to_log_item(self, res):
    long_text = "{} -> {}".format(self.source, self.dest) 
    short_text = "{} -> {}".format(file_helper.FileHelper.basename(self.source), 
                                  file_helper.FileHelper.basename(self.dest))
    num_subtitle_files = len(self._subtitle_files())
    if res == FileRenamer.SUCCESS and num_subtitle_files:
      long_text += " #subtitle files:{}".format(num_subtitle_files)
      short_text += " #subtitle files:{}".format(num_subtitle_files)
    level = utils.LogLevel.INFO
    if res != FileRenamer.SUCCESS:
      level = utils.LogLevel.ERROR
    return utils.LogItem(level, FileRenamer.result_str(res), short_text, long_text)
  
  def perform_action(self, progress_cb=None):
    """ Move/Copy a file from source to destination. """
    #sanity checks
    if not file_helper.FileHelper.file_exists(self.source):
      return FileRenamer.SOURCE_DOES_NOT_EXIST
    if not file_helper.FileHelper.is_valid_filename(self.dest):
      return FileRenamer.INVALID_FILENAME
    elif self.source == self.dest:
      return FileRenamer.SUCCESS
    elif file_helper.FileHelper.file_exists(self.dest) and not self.can_overwrite:
      return FileRenamer.COULD_NOT_OVERWRITE    

    if self.keep_source:
      return self._copy_file(progress_cb)
    else:
      return self._move_file(progress_cb)    
    
  def _subtitle_files(self):
    ret = []
    for ext in self.subtitle_extensions:
      sub = file_helper.FileHelper.change_extension(self.source, ext)
      if sub != self.source and file_helper.FileHelper.file_exists(sub):
        ret.append(sub)
    return ret
  
  def _move_file(self, progress_cb):
    if file_helper.FileHelper.move_file(self.source, self.dest, progress_cb):
      for sub in self._subtitle_files():
        ext = file_helper.FileHelper.change_extension(self.dest, file_helper.FileHelper.extension(sub))
        file_helper.FileHelper.move_file(sub, ext)
      return FileRenamer.SUCCESS
    else:
      return FileRenamer.FAILED
    
  def _copy_file(self, progress_cb):
    if file_helper.FileHelper.copy_file(self.source, self.dest, progress_cb):
      for sub in self._subtitle_files():
        ext = file_helper.FileHelper.change_extension(self.dest, file_helper.FileHelper.extension(sub))
        file_helper.FileHelper.copy_file(sub, ext)
      return FileRenamer.SUCCESS
    else:
      return FileRenamer.FAILED
    