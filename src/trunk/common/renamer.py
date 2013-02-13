#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Class responsible for the moving/copying of files
# --------------------------------------------------------------------------------------------------------------------
from common import file_helper
from common import utils

_ID_COUNT = 0

# --------------------------------------------------------------------------------------------------------------------
class BaseRenameItemGenerator(object):
  """ converts an item a BaseRenamer object """
  def __init__(self, config=None):
    super(BaseRenameItemGenerator, self).__init__()
    self.config = config or {}

  def getRenameItem(self, item):
    raise NotImplementedError("BaseRenameItemGenerator.getRenameItem not implemented")

# --------------------------------------------------------------------------------------------------------------------
class RenameItemGenerator(BaseRenameItemGenerator):
  """ converts an item a BaseRenamer object """

  def __init__(self, formatter=None, config=None):
    super(RenameItemGenerator, self).__init__()
    self._formatter = formatter
    self.config = config or {}

  def getRenameItem(self, item):
    output_folder = self.config.getOutputFolder() or None # if none the item's filenames folder is used
    name = file_helper.FileHelper.sanitizeFilename(self._formatter.getName(self.config.format, item, output_folder))
    return FileRenamer(item.filename, name, can_overwrite=not self.config.dont_overwrite,
        keep_source=not self.config.is_move,
        subtitle_extensions=self.config.getSubtitles(),
        action_text="rename {}".format(item.getInfo().mode))

# --------------------------------------------------------------------------------------------------------------------
class BaseRenamer(object):
  """ performs rename on file """
  QUEUED  = "Queued"
  IN_PROGRESS  = "In progress"
  FAILED  = "Failed"
  SUCCESS = "Success"
  
  def __init__(self, action_text=""):
    super(BaseRenamer, self).__init__()
    self.action_text = action_text
    global _ID_COUNT
    self.id_ = _ID_COUNT
    _ID_COUNT += 1

  def performAction(self, progress_cb=None):
    raise NotImplementedError("BaseRenamer.performAction not implemented")

  def shortDescription(self):
    raise NotImplementedError("BaseRenamer.shortDescription not implemented")
  
  def longDescription(self):
    raise NotImplementedError("BaseRenamer.longDescription not implemented")
  
# --------------------------------------------------------------------------------------------------------------------
class FileRenamer(BaseRenamer):
  """ Class responsible for the moving/copying of files from source to destination """
  SOURCE_DOES_NOT_EXIST = "Source does not exist"
  COULD_NOT_OVERWRITE   = "Could not overwrite"
  INVALID_FILENAME      = "Destination file invalid"

  def __init__(self, source, dest, can_overwrite, keep_source, action_text="", subtitle_extensions=None):
    super(FileRenamer, self).__init__(action_text)
    self.source = source
    self.dest = dest
    self.can_overwrite = can_overwrite
    self.keep_source = keep_source
    self.subtitle_extensions = subtitle_extensions or []
    self.status = FileRenamer.QUEUED

  def performAction(self, progress_cb=None):
    """ Move/Copy a file from source to destination. """
    #sanity checks
    self.status = FileRenamer.IN_PROGRESS
    if not file_helper.FileHelper.fileExists(self.source):
      self.status = FileRenamer.SOURCE_DOES_NOT_EXIST
    if not file_helper.FileHelper.isValidFilename(self.dest):
      self.status = FileRenamer.INVALID_FILENAME
    elif self.source == self.dest:
      self.status = FileRenamer.SUCCESS
    elif file_helper.FileHelper.fileExists(self.dest) and not self.can_overwrite:
      self.status = FileRenamer.COULD_NOT_OVERWRITE      
    elif self.keep_source:
      self.status = self._copyFile(progress_cb)
    else:
      self.status = self._moveFile(progress_cb)
    return self.status

  def _subtitleFiles(self):
    ret = []
    for ext in self.subtitle_extensions:
      sub = file_helper.FileHelper.changeExtension(self.source, ext)
      if sub != self.source and file_helper.FileHelper.fileExists(sub):
        ret.append(sub)
    return ret

  def _moveFile(self, progress_cb):
    if file_helper.FileHelper.moveFile(self.source, self.dest, progress_cb):
      for sub in self._subtitleFiles():
        ext = file_helper.FileHelper.changeExtension(self.dest, file_helper.FileHelper.getExtension(sub))
        file_helper.FileHelper.moveFile(sub, ext)
      return FileRenamer.SUCCESS
    else:
      return FileRenamer.FAILED

  def _copyFile(self, progress_cb):
    if file_helper.FileHelper.copyFile(self.source, self.dest, progress_cb):
      for sub in self._subtitleFiles():
        ext = file_helper.FileHelper.changeExtension(self.dest, file_helper.FileHelper.getExtension(sub))
        file_helper.FileHelper.copyFile(sub, ext)
      return FileRenamer.SUCCESS
    else:
      return FileRenamer.FAILED
    
  def shortDescription(self):
    return "{} -> {} #subtitle files: {}".format(file_helper.FileHelper.basename(self.source),
        file_helper.FileHelper.basename(self.dest), len(self._subtitleFiles()))
  
  def longDescription(self):
    return "{} -> {} #subtitle files: {}".format(self.source, self.dest, len(self._subtitleFiles()))
