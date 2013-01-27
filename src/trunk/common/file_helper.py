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
  def is_file(file_obj):
    #utils.verify_type(file_obj, str)
    return os.path.isfile(file_obj)

  @staticmethod
  def is_dir(dir_obj):
    #utils.verify_type(dir_obj, str)
    return os.path.isdir(dir_obj)

  @staticmethod
  def dirname(file_obj):
    #utils.verify_type(file_obj, str)
    return os.path.dirname(file_obj)
  
  @staticmethod
  def basename(file_obj):
    #utils.verify_type(file_obj, str)
    return os.path.basename(file_obj)
  
  @staticmethod
  def split_drive(path):
    #utils.verify_type(p, str)
    return os.path.splitdrive(path)
  
  @staticmethod
  def extension(file_obj):
    #utils.verify_type(file_obj, str)
    return os.path.splitext(file_obj)[1]
  
  @staticmethod
  def join_path(dir_obj, file_obj):
    #utils.verify_type(dir_obj, str)
    #utils.verify_type(file_obj, str)
    ret = os.path.join(dir_obj, file_obj)
    return ret

  @staticmethod
  def dir_exists(dir_obj):
    #utils.verify_type(dir_obj, str)
    return os.path.exists(dir_obj) and FileHelper.is_dir(dir_obj)
  
  @staticmethod
  def create_dir(dir_obj):
    #utils.verify_type(dir_obj, str)
    ret = True
    if not FileHelper.dir_exists(dir_obj):
      try:
        os.makedirs(dir_obj)
      except os.error:
        ret = False
    return ret
  
  @staticmethod
  def remove_dir(dir_obj):
    #utils.verify_type(dir_obj, str)
    ret = True
    if FileHelper.dir_exists(dir_obj):
      try:
        shutil.rmtree(dir_obj)
      except shutil.Error:
        ret = False
    return ret

  @staticmethod
  def file_exists(file_obj):
    #utils.verify_type(file_obj, str)
    return os.path.exists(file_obj) and FileHelper.is_file(file_obj)
 
  @staticmethod
  def is_valid_filename(file_obj):
    #utils.verify_type(file_obj, str)
    _, tail = FileHelper.split_drive(file_obj)
    return bool(_RE_VALID_FILENAME.match(tail))
    
  @staticmethod
  def sanitize_filename(file_obj, replace_char="-"):
    #utils.verify_type(file_obj, str)
    #utils.verify_type(replace_char, str)
    drive, tail = FileHelper.split_drive(file_obj)
    tail = _RE_INALID_FILENAME.sub(replace_char, tail)
    ret = FileHelper.replace_separators("".join([drive, tail]), os.sep)
    return ret
  
  @staticmethod
  def get_file_size(file_obj):
    return os.path.getsize(file_obj) if FileHelper.file_exists(file_obj) else 0
  
  @staticmethod
  def replace_separators(name, replace_char="-"):
    return name.replace("\\", replace_char).replace("/", replace_char)
  
  @staticmethod
  def remove_file(file_obj):
    #utils.verify_type(file_obj, str)
    ret = True
    if FileHelper.file_exists(file_obj):
      try:
        os.remove(file_obj)
      except os.error:
        ret = False
    return ret
  
  @staticmethod
  def change_extension(file_obj, ext):
    return "{}{}".format(os.path.splitext(file_obj)[0], ext)

  @staticmethod
  def move_file(source, dest, progress_cb=None):
    #utils.verify_type(source, str)
    #utils.verify_type(dest, str)
    
    def safe_move_file(source, dest):
      ret = False
      try:
        shutil.move(source, dest)
        ret = True
      except shutil.Error:
        pass
      return ret
      
    def unsafe_move_file(source, dest, progress_cb):
      ret = FileHelper.copy_file(source, dest, progress_cb) and FileHelper.remove_file(source)
      return ret
      
    ret = False
    if FileHelper.file_exists(source):
      dest_folder = FileHelper.dirname(dest)
      if not dest_folder or FileHelper.create_dir(dest_folder):
        if os.path.commonprefix([source, dest]) or not progress_cb or FileHelper.get_file_size(source) < _BLOCK_SIZE:
          ret = safe_move_file(source, dest)
        else:
          ret = unsafe_move_file(source, dest, progress_cb)

    return ret
  
  @staticmethod
  def copy_file(source, dest, progress_cb=None):
    #utils.verify_type(source, str)
    #utils.verify_type(dest, str)

    def unsafe_copy_file(source_name, dest_name, progress_cb):
      """ bitwise copy so that we can be more responsive to user cancels etc. """
      assert(progress_cb)
      copied = 0
      ret = False
      try:
        source_size = FileHelper.get_file_size(source_name)
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
            ret = FileHelper.get_file_size(dest_name) == source_size
      except os.error:
        pass
      if not ret:
        FileHelper.remove_file(dest_name)
      return ret
      
    def safe_copy_file(source, dest):
      ret = False
      try:
        shutil.copy2(source, dest)
        ret = True
      except shutil.Error:
        pass 
      return ret
    
    ret = False
    if FileHelper.file_exists(source):
      dest_folder = FileHelper.dirname(dest)
      if not dest_folder or FileHelper.create_dir(dest_folder):
        if FileHelper.get_file_size(source) < _BLOCK_SIZE or not progress_cb:         
          ret = safe_copy_file(source, dest)
        else:
          ret = unsafe_copy_file(source, dest, progress_cb)
    return ret


