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
  def isFile(f):
    #utils.verifyType(f, str)
    return os.path.isfile(f)

  @staticmethod
  def isDir(d):
    #utils.verifyType(d, str)
    return os.path.isdir(d)

  @staticmethod
  def dirname(f):
    #utils.verifyType(f, str)
    return os.path.dirname(f)
  
  @staticmethod
  def basename(f):
    #utils.verifyType(f, str)
    return os.path.basename(f)
  
  @staticmethod
  def splitDrive(p):
    #utils.verifyType(p, str)
    return os.path.splitdrive(p)
  
  @staticmethod
  def extension(f):
    #utils.verifyType(f, str)
    return os.path.splitext(f)[1]
  
  @staticmethod
  def joinPath(d, f):
    #utils.verifyType(d, str)
    #utils.verifyType(f, str)
    ret = os.path.join(d, f)
    return ret

  @staticmethod
  def dirExists(d):
    #utils.verifyType(d, str)
    return os.path.exists(d) and FileHelper.isDir(d)
  
  @staticmethod
  def createDir(d):
    #utils.verifyType(d, str)
    ret = True
    if not FileHelper.dirExists(d):
      try:
        os.makedirs(d)
      except os.error:
        ret = False
    return ret
  
  @staticmethod
  def removeDir(d):
    #utils.verifyType(d, str)
    ret = True
    if FileHelper.dirExists(d):
      try:
        shutil.rmtree(d)
      except shutil.Error:
        ret = False
    return ret

  @staticmethod
  def fileExists(f):
    #utils.verifyType(f, str)
    return os.path.exists(f) and FileHelper.isFile(f)
 
  @staticmethod
  def isValidFilename(f):
    #utils.verifyType(f, str)
    _, tail = FileHelper.splitDrive(f)
    isOk = bool(_RE_VALID_FILENAME.match(tail))
    return isOk
    
  @staticmethod
  def sanitizeFilename(f, replaceChar="-"):
    #utils.verifyType(f, str)
    #utils.verifyType(replaceChar, str)
    drive, tail = FileHelper.splitDrive(f)
    tail = _RE_INALID_FILENAME.sub(replaceChar, tail)
    ret = FileHelper.replaceSeparators("".join([drive, tail]), os.sep)
    return ret
  
  @staticmethod
  def getFileSize(f):
    return os.path.getsize(f) if FileHelper.fileExists(f) else 0
  
  @staticmethod
  def replaceSeparators(name, replaceChar="-"):
    return name.replace("\\", replaceChar).replace("/", replaceChar)
  
  @staticmethod
  def removeFile(f):
    #utils.verifyType(f, str)
    ret = True
    if FileHelper.fileExists(f):
      try:
        os.remove(f)
      except os.error:
        ret = False
    return ret
  
  @staticmethod
  def changeExtension(f, ext):
    return "{}{}".format(os.path.splitext(f)[0], ext)

  @staticmethod
  def moveFile(source, dest, progressCb=None):
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
      
    def unsafeMoveFile(source, dest, progressCb):
      ret = FileHelper.copyFile(source, dest, progressCb) and FileHelper.removeFile(source)
      return ret
      
    ret = False
    if FileHelper.fileExists(source):
      destFolder = FileHelper.dirname(dest)
      if not destFolder or FileHelper.createDir(destFolder):
        if os.path.commonprefix([source, dest]) or not progressCb or FileHelper.getFileSize(source) < _BLOCK_SIZE:         
          ret = safeMoveFile(source, dest)
        else:
          ret = unsafeMoveFile(source, dest, progressCb)

    return ret
  
  @staticmethod
  def copyFile(source, dest, progressCb=None):
    #utils.verifyType(source, str)
    #utils.verifyType(dest, str)

    def unsafeCopyFile(s, d, progressCb):
      """ bitwise copy so that we can be more responsive to user cancels etc. """
      assert(progressCb)
      copied = 0
      ret = False
      try:
        sourceSize = FileHelper.getFileSize(s)
        with open(s, "rb") as source:
          with open(d, "wb") as dest:
            chunk = ""
            while True:
              chunk = source.read(_BLOCK_SIZE)
              if not chunk:
                break
              copied += len(chunk)
              dest.write(chunk)
              # why 90%? closing of file handles can take a while after
              if not progressCb(int(90.0 * copied / sourceSize)): 
                break
            ret = FileHelper.getFileSize(d) == sourceSize
      except os.error:
        pass
      if not ret:
        FileHelper.removeFile(d)
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
      destFolder = FileHelper.dirname(dest)
      if not destFolder or FileHelper.createDir(destFolder):
        if FileHelper.getFileSize(source) < _BLOCK_SIZE or not progressCb:         
          ret = safeCopyFile(source, dest)
        else:
          ret = unsafeCopyFile(source, dest, progressCb)
    return ret


