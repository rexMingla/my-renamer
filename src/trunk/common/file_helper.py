#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Interface to python's file libraries
# --------------------------------------------------------------------------------------------------------------------
import os
import re
import shutil
import string

_BLOCK_SIZE = pow(2, 15)
_VALID_BASENAME_CHARACTERS = "".join([string.ascii_letters,
                                      string.digits,
                                      r" !#$%&'()+,-.\\/;=@[\]^_`{}~"]) # string.punctuation without :?"<>|
_RE_PATH = re.compile(r"(\\|/+)")
_RE_INALID_FILENAME = re.compile("[^{}]".format(re.escape(_VALID_BASENAME_CHARACTERS)))
_RE_VALID_FILENAME = re.compile("^([{}])*$".format(re.escape(_VALID_BASENAME_CHARACTERS)))

# --------------------------------------------------------------------------------------------------------------------
class FileHelper:
  """ Collection of static functions abstracting the python libraries. """

  @staticmethod
  def isFile(file_obj):
    #utils.verifyType(file_obj, str)
    return os.path.isfile(file_obj)

  @staticmethod
  def isDir(dir_obj):
    #utils.verifyType(dir_obj, str)
    return os.path.isdir(dir_obj)

  @staticmethod
  def dirname(file_obj):
    #utils.verifyType(file_obj, str)
    return os.path.dirname(file_obj)

  @staticmethod
  def basename(file_obj):
    #utils.verifyType(file_obj, str)
    return os.path.basename(file_obj)

  @staticmethod
  def splitDrive(path):
    #utils.verifyType(p, str)
    return os.path.splitdrive(path)

  @staticmethod
  def extension(file_obj):
    #utils.verifyType(file_obj, str)
    return os.path.splitext(file_obj)[1]

  @staticmethod
  def joinPath(dir_obj, file_obj):
    #utils.verifyType(dir_obj, str)
    #utils.verifyType(file_obj, str)
    ret = os.path.join(dir_obj, file_obj)
    return ret

  @staticmethod
  def dirExists(dir_obj):
    #utils.verifyType(dir_obj, str)
    return os.path.exists(dir_obj) and FileHelper.isDir(dir_obj)

  @staticmethod
  def createDir(dir_obj):
    #utils.verifyType(dir_obj, str)
    ret = True
    if not FileHelper.dirExists(dir_obj):
      try:
        os.makedirs(dir_obj)
      except os.error:
        ret = False
    return ret

  @staticmethod
  def removeDir(dir_obj):
    #utils.verifyType(dir_obj, str)
    ret = True
    if FileHelper.dirExists(dir_obj):
      try:
        shutil.rmtree(dir_obj)
      except shutil.Error:
        ret = False
    return ret

  @staticmethod
  def fileExists(file_obj):
    #utils.verifyType(file_obj, str)
    return os.path.exists(file_obj) and FileHelper.isFile(file_obj)

  @staticmethod
  def isValidFilename(file_obj):
    #utils.verifyType(file_obj, str)
    _, tail = FileHelper.splitDrive(file_obj)
    return bool(_RE_VALID_FILENAME.match(tail))

  @staticmethod
  def sanitizeFilename(file_obj, replace_char="-"):
    #utils.verifyType(file_obj, str)
    #utils.verifyType(replace_char, str)
    drive, tail = FileHelper.splitDrive(file_obj)
    tail = _RE_INALID_FILENAME.sub(replace_char, tail)
    ret = FileHelper.replaceSeparators("".join([drive, tail]), os.sep)
    return ret

  @staticmethod
  def getFileSize(file_obj):
    return os.path.getsize(file_obj) if FileHelper.fileExists(file_obj) else 0

  @staticmethod
  def replaceSeparators(name, replace_char="-"):
    return name.replace("\\", replace_char).replace("/", replace_char)

  @staticmethod
  def removeFile(file_obj):
    #utils.verifyType(file_obj, str)
    ret = True
    if FileHelper.fileExists(file_obj):
      try:
        os.remove(file_obj)
      except os.error:
        ret = False
    return ret

  @staticmethod
  def changeExtension(file_obj, ext):
    return "{}{}".format(os.path.splitext(file_obj)[0], ext)

  @staticmethod
  def moveFile(source, dest, progress_cb=None):
    #utils.verifyType(source, str)
    #utils.verifyType(dest, str)

    def safeMoveFile(source, dest):
      ret = False
      try:
        shutil.move(source, dest)
        ret = True
      except shutil.Error:
        pass
      return ret

    def unsafeMoveFile(source, dest, progress_cb):
      ret = FileHelper.copyFile(source, dest, progress_cb) and FileHelper.removeFile(source)
      return ret

    ret = False
    if FileHelper.fileExists(source):
      dest_folder = FileHelper.dirname(dest)
      if not dest_folder or FileHelper.createDir(dest_folder):
        if os.path.commonprefix([source, dest]) or not progress_cb or FileHelper.getFileSize(source) < _BLOCK_SIZE:
          ret = safeMoveFile(source, dest)
        else:
          ret = unsafeMoveFile(source, dest, progress_cb)

    return ret

  @staticmethod
  def copyFile(source, dest, progress_cb=None):
    #utils.verifyType(source, str)
    #utils.verifyType(dest, str)

    def unsafeCopyFile(source_name, dest_name, progress_cb):
      """ bitwise copy so that we can be more responsive to user cancels etc. """
      assert(progress_cb)
      copied = 0
      ret = False
      try:
        source_size = FileHelper.getFileSize(source_name)
        with open(source_name, "rb") as source:
          with open(dest_name, "wb") as dest:
            chunk = ""
            while True:
              chunk = source.read(_BLOCK_SIZE)
              if not chunk:
                break
              copied += len(chunk)
              dest.write(chunk)
              # why 90%? closing of file handles can take a while after
              if not progress_cb(int(90.0 * copied / source_size)):
                break
            ret = FileHelper.getFileSize(dest_name) == source_size
      except os.error:
        pass
      if not ret:
        FileHelper.removeFile(dest_name)
      return ret

    def safeCopyFile(source, dest):
      ret = False
      try:
        shutil.copy2(source, dest)
        ret = True
      except shutil.Error:
        pass
      return ret

    ret = False
    if FileHelper.fileExists(source):
      dest_folder = FileHelper.dirname(dest)
      if not dest_folder or FileHelper.createDir(dest_folder):
        if FileHelper.getFileSize(source) < _BLOCK_SIZE or not progress_cb:
          ret = safeCopyFile(source, dest)
        else:
          ret = unsafeCopyFile(source, dest, progress_cb)
    return ret


