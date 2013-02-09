#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Class responsible for the moving/copying of files
# --------------------------------------------------------------------------------------------------------------------
from common import file_helper
from common import utils

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
    if self.config.getOutputFolder():
      item.output_folder = self.config.getOutputFolder()
    name = file_helper.FileHelper.sanitizeFilename(self._formatter.getName(self.config.format, item))
    return FileRenamer(item.filename, name, can_overwrite=not self.config.dont_overwrite,
                                            keep_source=not self.config.is_move,
                                            subtitle_extensions=self.config.getSubtitles())

# --------------------------------------------------------------------------------------------------------------------
class BaseRenamer(object):
  """ performs rename on file """
  def __init__(self):
    super(BaseRenamer, self).__init__()

  def performAction(self, progress_cb=None):
    raise NotImplementedError("BaseRenamer.performAction not implemented")

# --------------------------------------------------------------------------------------------------------------------
class FileRenamer(BaseRenamer):
  """ Class responsible for the moving/copying of files from source to destination """
  SOURCE_DOES_NOT_EXIST = -4
  COULD_NOT_OVERWRITE   = -3
  FAILED                = -2
  INVALID_FILENAME      = -1
  SUCCESS               = 1

  @staticmethod
  def resultStr(res):
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

  def resultToLogItem(self, res):
    long_text = "{} -> {}".format(self.source, self.dest)
    short_text = "{} -> {}".format(file_helper.FileHelper.basename(self.source),
                                  file_helper.FileHelper.basename(self.dest))
    num_subtitle_files = len(self._subtitleFiles())
    if res == FileRenamer.SUCCESS and num_subtitle_files:
      long_text += " #subtitle files:{}".format(num_subtitle_files)
      short_text += " #subtitle files:{}".format(num_subtitle_files)
    level = utils.LogLevel.INFO
    if res != FileRenamer.SUCCESS:
      level = utils.LogLevel.ERROR
    return utils.LogItem(level, FileRenamer.resultStr(res), short_text, long_text)

  def performAction(self, progress_cb=None):
    """ Move/Copy a file from source to destination. """
    #sanity checks
    if not file_helper.FileHelper.fileExists(self.source):
      return FileRenamer.SOURCE_DOES_NOT_EXIST
    if not file_helper.FileHelper.isValidFilename(self.dest):
      return FileRenamer.INVALID_FILENAME
    elif self.source == self.dest:
      return FileRenamer.SUCCESS
    elif file_helper.FileHelper.fileExists(self.dest) and not self.can_overwrite:
      return FileRenamer.COULD_NOT_OVERWRITE

    if self.keep_source:
      return self._copyFile(progress_cb)
    else:
      return self._moveFile(progress_cb)

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
        ext = file_helper.FileHelper.changeExtension(self.dest, file_helper.FileHelper.extension(sub))
        file_helper.FileHelper.moveFile(sub, ext)
      return FileRenamer.SUCCESS
    else:
      return FileRenamer.FAILED

  def _copyFile(self, progress_cb):
    if file_helper.FileHelper.copyFile(self.source, self.dest, progress_cb):
      for sub in self._subtitleFiles():
        ext = file_helper.FileHelper.changeExtension(self.dest, file_helper.FileHelper.extension(sub))
        file_helper.FileHelper.copyFile(sub, ext)
      return FileRenamer.SUCCESS
    else:
      return FileRenamer.FAILED

