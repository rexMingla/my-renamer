#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
  import sys 
  import os
  sys.path.insert(0, os.path.abspath(__file__+"/../../"))

import unittest

from common import file_helper
from common import renamer

# --------------------------------------------------------------------------------------------------------------------
def createTestFile(name):
  #utils.verify_type(name, str)
  f = file(name, "w")
  f.close()

# --------------------------------------------------------------------------------------------------------------------
class BasicTest(unittest.TestCase):
  def test_createRemove(self):
    src = "basicMoveSrc.txt"
    dest = "basicMoveDest.txt"
    createTestFile(src)
    self.assertTrue(file_helper.FileHelper.move_file(src, dest))
    self.assertFalse(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    file_helper.FileHelper.remove_file(dest)

# --------------------------------------------------------------------------------------------------------------------
class BasicCopyTest(unittest.TestCase):
  def test_basicCopy(self):
    src = "basicCopySrc.txt"
    dest = "basicCopyDest.txt"
    createTestFile(src)
    self.assertTrue(file_helper.FileHelper.copy_file(src, dest))
    self.assertTrue(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    file_helper.FileHelper.remove_file(src)
    file_helper.FileHelper.remove_file(dest)
    
  def test_basicCopyToNewDir(self):
    src = "basicCopyToDir.txt"
    destDir = "test/"
    dest = destDir + "basicCopyToDir.txt"
    createTestFile(src)
    self.assertTrue(file_helper.FileHelper.remove_dir(destDir))
    self.assertTrue(file_helper.FileHelper.copy_file(src, dest))
    self.assertTrue(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    file_helper.FileHelper.remove_file(src)
    file_helper.FileHelper.remove_file(dest)
    file_helper.FileHelper.remove_dir(destDir)
    
  def test_basicCopyToNewDir2(self):
    src = "basicCopyToDir.txt"
    destDir = "test/test/"
    dest = destDir + "basicCopyToDir.txt"
    createTestFile(src)
    self.assertTrue(file_helper.FileHelper.remove_dir(destDir))
    self.assertTrue(file_helper.FileHelper.copy_file(src, dest))
    self.assertTrue(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    file_helper.FileHelper.remove_file(src)
    file_helper.FileHelper.remove_file(dest)
    file_helper.FileHelper.remove_dir("test")
    
# --------------------------------------------------------------------------------------------------------------------
class BasicMoveTest(unittest.TestCase):
  def test_createAndRemove(self):
    name = "createAndRemove.txt"
    createTestFile(name)
    self.assertTrue(file_helper.FileHelper.file_exists(name))
    file_helper.FileHelper.remove_file(name)
    self.assertFalse(file_helper.FileHelper.file_exists(name))

  def test_basicMoveToNewDir(self):
    src = "basicMoveToDir.txt"
    destDir = "test/"
    dest = destDir + "basicMoveToDir.txt"
    createTestFile(src)
    self.assertTrue(file_helper.FileHelper.remove_dir(destDir))
    self.assertTrue(file_helper.FileHelper.move_file(src, dest))
    self.assertFalse(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    file_helper.FileHelper.remove_file(dest)
    file_helper.FileHelper.remove_dir(destDir)
    
  def test_basicMoveToNewDir2(self):
    src = "basicMoveToDir.txt"
    destDir = "test/test/"
    dest = destDir + "basicMoveToDir.txt"
    createTestFile(src)
    self.assertTrue(file_helper.FileHelper.remove_dir(destDir))
    self.assertTrue(file_helper.FileHelper.move_file(src, dest))
    self.assertFalse(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    file_helper.FileHelper.remove_file(dest)
    file_helper.FileHelper.remove_dir("test")
    
# --------------------------------------------------------------------------------------------------------------------
class MoveItemCandidateTest(unittest.TestCase):
  def test_basic(self):
    src = "basicMoveSrc.txt"
    dest = "basicMoveDest.txt"
    mover = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=False)
    createTestFile(src)
    res = mover.perform_action()
    self.assertFalse(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.SUCCESS)
    file_helper.FileHelper.remove_file(dest)
    
  def test_sameLocation(self):
    src = "sameLocation.txt"
    dest = "sameLocation.txt"
    mover = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=False)
    createTestFile(src)
    res = mover.perform_action()
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.SUCCESS)
    file_helper.FileHelper.remove_file(dest)
  
  def test_overwrite(self):
    src = "moveOverwriteSrc.txt"
    dest = "moveOverwriteDest.txt"
    mover = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=False)
    createTestFile(src)
    createTestFile(dest)
    res = mover.perform_action()
    self.assertFalse(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.SUCCESS)
    file_helper.FileHelper.remove_file(dest)

  def test_noOverwrite(self):
    src = "moveOverwriteSrc.txt"
    dest = "moveOverwriteDest.txt"
    mover = renamer.FileRenamer(src, dest, can_overwrite=False, keep_source=False)
    createTestFile(src)
    createTestFile(dest)
    res = mover.perform_action()
    self.assertTrue(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.COULD_NOT_OVERWRITE)
    file_helper.FileHelper.remove_file(src)
    file_helper.FileHelper.remove_file(dest)

  def test_badFilename(self):
    src = "src.txt"
    dest = "dest?.txt"
    mover = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=False)
    createTestFile(src)
    res = mover.perform_action()
    self.assertTrue(file_helper.FileHelper.file_exists(src))
    self.assertFalse(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.INVALID_FILENAME)
    file_helper.FileHelper.remove_file(dest)
    
  def test_badFilename2(self):
    src = "src.txt"
    dest = "dest:.txt"
    mover = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=False)
    createTestFile(src)
    res = mover.perform_action()
    self.assertEqual(res, renamer.FileRenamer.INVALID_FILENAME)
    file_helper.FileHelper.remove_file(src)
    
  def test_badFilename3(self):
    src = "src.txt"
    dest = "c:/src/dest:.txt"
    mover = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=False)
    createTestFile(src)
    res = mover.perform_action()
    self.assertEqual(res, renamer.FileRenamer.INVALID_FILENAME)
    file_helper.FileHelper.remove_file(src)

  def test_badFilename4(self):
    src = "src.txt"
    dest = "c:/wtf:src/dest.txt"
    mover = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=False)
    createTestFile(src)
    res = mover.perform_action()
    self.assertEqual(res, renamer.FileRenamer.INVALID_FILENAME)
    file_helper.FileHelper.remove_file(src)

  def test_badSource(self):
    src = ""
    dest = "dest.txt"
    copier = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=False)
    res = copier.perform_action()
    self.assertFalse(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.SOURCE_DOES_NOT_EXIST)

# --------------------------------------------------------------------------------------------------------------------
class CopyItemTest(unittest.TestCase):
  def test_basic(self):
    src = "basicDest.txt"
    dest = "basicDest.txt"
    copier = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=True)
    createTestFile(src)
    res = copier.perform_action()
    self.assertTrue(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.SUCCESS)
    file_helper.FileHelper.remove_file(dest)
    
  def test_sameLocation(self):
    src = "sameLocation.txt"
    dest = "sameLocation.txt"
    copier = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=True)
    createTestFile(src)
    res = copier.perform_action()
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.SUCCESS)
    file_helper.FileHelper.remove_file(dest)
  
  def test_overwrite(self):
    src = "overwriteSrc.txt"
    dest = "overwriteDest.txt"
    copier = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=True)
    createTestFile(src)
    createTestFile(dest)
    res = copier.perform_action()
    self.assertTrue(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.SUCCESS)
    file_helper.FileHelper.remove_file(dest)

  def test_noOverwrite(self):
    src = "overwriteSrc.txt"
    dest = "overwriteDest.txt"
    copier = renamer.FileRenamer(src, dest, can_overwrite=False, keep_source=True)
    createTestFile(src)
    createTestFile(dest)
    res = copier.perform_action()
    self.assertTrue(file_helper.FileHelper.file_exists(src))
    self.assertTrue(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.COULD_NOT_OVERWRITE)
    file_helper.FileHelper.remove_file(src)
    file_helper.FileHelper.remove_file(dest)
    
  def test_badFilename(self):
    src = "src.txt"
    dest = "dest?.txt"
    copier = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=True)
    createTestFile(src)
    res = copier.perform_action()
    self.assertTrue(file_helper.FileHelper.file_exists(src))
    self.assertFalse(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.INVALID_FILENAME)
    file_helper.FileHelper.remove_file(src)
    file_helper.FileHelper.remove_file(dest)

  def test_badSource(self):
    src = ""
    dest = "dest.txt"
    copier = renamer.FileRenamer(src, dest, can_overwrite=True, keep_source=True)
    res = copier.perform_action()
    self.assertFalse(file_helper.FileHelper.file_exists(dest))
    self.assertEqual(res, renamer.FileRenamer.SOURCE_DOES_NOT_EXIST)
    
# --------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__': 
  unittest.main()