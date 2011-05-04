#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import sys 
import os
sys.path.insert(0, os.path.abspath(__file__+"/../../"))
import unittest

from app import outputWidget, utils
from common import fileHelper
from tv import moveItem

# --------------------------------------------------------------------------------------------------------------------
def createTestFile(name):
  utils.verifyType(name, str)
  f = file(name, "w")
  f.close()

# --------------------------------------------------------------------------------------------------------------------
class BasicTest(unittest.TestCase):
  def test_createRemove(self):
    src = "basicMoveSrc.txt"
    dest = "basicMoveDest.txt"
    createTestFile(src)
    self.assertTrue(fileHelper.FileHelper.moveFile(src, dest))
    self.assertFalse(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    fileHelper.FileHelper.removeFile(dest)

# --------------------------------------------------------------------------------------------------------------------
class BasicCopyTest(unittest.TestCase):
  def test_basicCopy(self):
    src = "basicCopySrc.txt"
    dest = "basicCopyDest.txt"
    createTestFile(src)
    self.assertTrue(fileHelper.FileHelper.copyFile(src, dest))
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    fileHelper.FileHelper.removeFile(src)
    fileHelper.FileHelper.removeFile(dest)
    
  def test_basicCopyToNewDir(self):
    src = "basicCopyToDir.txt"
    destDir = "test/"
    dest = destDir + "basicCopyToDir.txt"
    createTestFile(src)
    self.assertTrue(fileHelper.FileHelper.removeDir(destDir))
    self.assertTrue(fileHelper.FileHelper.copyFile(src, dest))
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    fileHelper.FileHelper.removeFile(src)
    fileHelper.FileHelper.removeFile(dest)
    fileHelper.FileHelper.removeDir(destDir)
    
  def test_basicCopyToNewDir2(self):
    src = "basicCopyToDir.txt"
    destDir = "test/test/"
    dest = destDir + "basicCopyToDir.txt"
    createTestFile(src)
    self.assertTrue(fileHelper.FileHelper.removeDir(destDir))
    self.assertTrue(fileHelper.FileHelper.copyFile(src, dest))
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    fileHelper.FileHelper.removeFile(src)
    fileHelper.FileHelper.removeFile(dest)
    fileHelper.FileHelper.removeDir("test")
    
# --------------------------------------------------------------------------------------------------------------------
class BasicMoveTest(unittest.TestCase):
  def test_createAndRemove(self):
    name = "createAndRemove.txt"
    createTestFile(name)
    self.assertTrue(fileHelper.FileHelper.fileExists(name))
    fileHelper.FileHelper.removeFile(name)
    self.assertFalse(fileHelper.FileHelper.fileExists(name))

  def test_basicMoveToNewDir(self):
    src = "basicMoveToDir.txt"
    destDir = "test/"
    dest = destDir + "basicMoveToDir.txt"
    createTestFile(src)
    self.assertTrue(fileHelper.FileHelper.removeDir(destDir))
    self.assertTrue(fileHelper.FileHelper.moveFile(src, dest))
    self.assertFalse(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    fileHelper.FileHelper.removeFile(dest)
    fileHelper.FileHelper.removeDir(destDir)
    
  def test_basicMoveToNewDir2(self):
    src = "basicMoveToDir.txt"
    destDir = "test/test/"
    dest = destDir + "basicMoveToDir.txt"
    createTestFile(src)
    self.assertTrue(fileHelper.FileHelper.removeDir(destDir))
    self.assertTrue(fileHelper.FileHelper.moveFile(src, dest))
    self.assertFalse(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    fileHelper.FileHelper.removeFile(dest)
    fileHelper.FileHelper.removeDir("test")
    
# --------------------------------------------------------------------------------------------------------------------
class MoveItemTest(unittest.TestCase):
  def test_basic(self):
    mover = fileHelper.MoveItemActioner(canOverwrite=True, keepSource=False)
    src = "basicMoveSrc.txt"
    dest = "basicMoveDest.txt"
    createTestFile(src)
    res = mover.performAction(src, dest)
    self.assertFalse(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)
    
  def test_sameLocation(self):
    mover = fileHelper.MoveItemActioner(canOverwrite=True, keepSource=False)
    src = "sameLocation.txt"
    dest = "sameLocation.txt"
    createTestFile(src)
    res = mover.performAction(src, dest)
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)
  
  def test_overwrite(self):
    mover = fileHelper.MoveItemActioner(canOverwrite=True, keepSource=False)
    src = "moveOverwriteSrc.txt"
    dest = "moveOverwriteDest.txt"
    createTestFile(src)
    createTestFile(dest)
    res = mover.performAction(src, dest)
    self.assertFalse(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)

  def test_noOverwrite(self):
    mover = fileHelper.MoveItemActioner(canOverwrite=False, keepSource=False)
    src = "moveOverwriteSrc.txt"
    dest = "moveOverwriteDest.txt"
    createTestFile(src)
    createTestFile(dest)
    res = mover.performAction(src, dest)
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.COULD_NOT_OVERWRITE)
    fileHelper.FileHelper.removeFile(src)
    fileHelper.FileHelper.removeFile(dest)

  def test_badFilename(self):
    mover = fileHelper.MoveItemActioner(canOverwrite=True, keepSource=False)
    src = "src.txt"
    dest = "dest?.txt"
    createTestFile(src)
    res = mover.performAction(src, dest)
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertFalse(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.INVALID_FILENAME)
    fileHelper.FileHelper.removeFile(dest)
    
  def test_badSource(self):
    copier = fileHelper.MoveItemActioner(canOverwrite=True, keepSource=False)
    src = ""
    dest = "dest.txt"
    res = copier.performAction(src, dest)
    self.assertFalse(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.SOURCE_DOES_NOT_EXIST)

# --------------------------------------------------------------------------------------------------------------------
class CopyItemTest(unittest.TestCase):
  def test_basic(self):
    copier = fileHelper.MoveItemActioner(canOverwrite=True, keepSource=True)
    src = "basicDest.txt"
    dest = "basicDest.txt"
    createTestFile(src)
    res = copier.performAction(src, dest)
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)
    
  def test_sameLocation(self):
    copier = fileHelper.MoveItemActioner(canOverwrite=True, keepSource=True)
    src = "sameLocation.txt"
    dest = "sameLocation.txt"
    createTestFile(src)
    res = copier.performAction(src, dest)
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)
  
  def test_overwrite(self):
    copier = fileHelper.MoveItemActioner(canOverwrite=True, keepSource=True)
    src = "overwriteSrc.txt"
    dest = "overwriteDest.txt"
    createTestFile(src)
    createTestFile(dest)
    res = copier.performAction(src, dest)
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)

  def test_noOverwrite(self):
    copier = fileHelper.MoveItemActioner(canOverwrite=False, keepSource=True)
    src = "overwriteSrc.txt"
    dest = "overwriteDest.txt"
    createTestFile(src)
    createTestFile(dest)
    res = copier.performAction(src, dest)
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.COULD_NOT_OVERWRITE)
    fileHelper.FileHelper.removeFile(src)
    fileHelper.FileHelper.removeFile(dest)
    
  def test_badFilename(self):
    copier = fileHelper.MoveItemActioner(canOverwrite=True, keepSource=True)
    src = "src.txt"
    dest = "dest?.txt"
    createTestFile(src)
    res = copier.performAction(src, dest)
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertFalse(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.INVALID_FILENAME)
    fileHelper.FileHelper.removeFile(src)
    fileHelper.FileHelper.removeFile(dest)

  def test_badSource(self):
    copier = fileHelper.MoveItemActioner(canOverwrite=True, keepSource=True)
    src = ""
    dest = "dest.txt"
    res = copier.performAction(src, dest)
    self.assertFalse(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, fileHelper.MoveItemActioner.SOURCE_DOES_NOT_EXIST)
    
# --------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__': 
  unittest.main()