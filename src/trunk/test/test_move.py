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

from app import outputWidget
from common import fileHelper, moveItemActioner, utils
from tv import moveItemCandidate

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
class MoveItemCandidateTest(unittest.TestCase):
  def test_basic(self):
    src = "basicMoveSrc.txt"
    dest = "basicMoveDest.txt"
    mover = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=False)
    createTestFile(src)
    res = mover.performAction()
    self.assertFalse(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)
    
  def test_sameLocation(self):
    src = "sameLocation.txt"
    dest = "sameLocation.txt"
    mover = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=False)
    createTestFile(src)
    res = mover.performAction()
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)
  
  def test_overwrite(self):
    src = "moveOverwriteSrc.txt"
    dest = "moveOverwriteDest.txt"
    mover = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=False)
    createTestFile(src)
    createTestFile(dest)
    res = mover.performAction()
    self.assertFalse(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)

  def test_noOverwrite(self):
    src = "moveOverwriteSrc.txt"
    dest = "moveOverwriteDest.txt"
    mover = moveItemActioner.FileRenamer(src, dest, canOverwrite=False, keepSource=False)
    createTestFile(src)
    createTestFile(dest)
    res = mover.performAction()
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.COULD_NOT_OVERWRITE)
    fileHelper.FileHelper.removeFile(src)
    fileHelper.FileHelper.removeFile(dest)

  def test_badFilename(self):
    src = "src.txt"
    dest = "dest?.txt"
    mover = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=False)
    createTestFile(src)
    res = mover.performAction()
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertFalse(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.INVALID_FILENAME)
    fileHelper.FileHelper.removeFile(dest)
    
  def test_badFilename2(self):
    src = "src.txt"
    dest = "dest:.txt"
    mover = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=False)
    createTestFile(src)
    res = mover.performAction()
    self.assertEqual(res, moveItemActioner.FileRenamer.INVALID_FILENAME)
    fileHelper.FileHelper.removeFile(src)
    
  def test_badFilename3(self):
    src = "src.txt"
    dest = "c:/src/dest:.txt"
    mover = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=False)
    createTestFile(src)
    res = mover.performAction()
    self.assertEqual(res, moveItemActioner.FileRenamer.INVALID_FILENAME)
    fileHelper.FileHelper.removeFile(src)

  def test_badFilename4(self):
    src = "src.txt"
    dest = "c:/wtf:src/dest.txt"
    mover = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=False)
    createTestFile(src)
    res = mover.performAction()
    self.assertEqual(res, moveItemActioner.FileRenamer.INVALID_FILENAME)
    fileHelper.FileHelper.removeFile(src)

  def test_badSource(self):
    src = ""
    dest = "dest.txt"
    copier = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=False)
    res = copier.performAction()
    self.assertFalse(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.SOURCE_DOES_NOT_EXIST)

# --------------------------------------------------------------------------------------------------------------------
class CopyItemTest(unittest.TestCase):
  def test_basic(self):
    src = "basicDest.txt"
    dest = "basicDest.txt"
    copier = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=True)
    createTestFile(src)
    res = copier.performAction()
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)
    
  def test_sameLocation(self):
    src = "sameLocation.txt"
    dest = "sameLocation.txt"
    copier = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=True)
    createTestFile(src)
    res = copier.performAction()
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)
  
  def test_overwrite(self):
    src = "overwriteSrc.txt"
    dest = "overwriteDest.txt"
    copier = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=True)
    createTestFile(src)
    createTestFile(dest)
    res = copier.performAction()
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.SUCCESS)
    fileHelper.FileHelper.removeFile(dest)

  def test_noOverwrite(self):
    src = "overwriteSrc.txt"
    dest = "overwriteDest.txt"
    copier = moveItemActioner.FileRenamer(src, dest, canOverwrite=False, keepSource=True)
    createTestFile(src)
    createTestFile(dest)
    res = copier.performAction()
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertTrue(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.COULD_NOT_OVERWRITE)
    fileHelper.FileHelper.removeFile(src)
    fileHelper.FileHelper.removeFile(dest)
    
  def test_badFilename(self):
    src = "src.txt"
    dest = "dest?.txt"
    copier = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=True)
    createTestFile(src)
    res = copier.performAction()
    self.assertTrue(fileHelper.FileHelper.fileExists(src))
    self.assertFalse(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.INVALID_FILENAME)
    fileHelper.FileHelper.removeFile(src)
    fileHelper.FileHelper.removeFile(dest)

  def test_badSource(self):
    src = ""
    dest = "dest.txt"
    copier = moveItemActioner.FileRenamer(src, dest, canOverwrite=True, keepSource=True)
    res = copier.performAction()
    self.assertFalse(fileHelper.FileHelper.fileExists(dest))
    self.assertEqual(res, moveItemActioner.FileRenamer.SOURCE_DOES_NOT_EXIST)
    
# --------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__': 
  unittest.main()