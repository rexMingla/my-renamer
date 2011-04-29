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
#import copy

from tv import moveItem, moveHelper
from app import outputWidget

# --------------------------------------------------------------------------------------------------------------------
class MoveTest(unittest.TestCase):
  def __init__(self):
    self.outputSettings_ = outputWidget.OutputSettings()
    self.outputSettings_.doNotOverwrite_ = True
    self.moveHelper_ = moveHelper.MoveHelper(self.outputSettings_)
    
  def test_basicMoveSameLocation(self):
    self.moveHelper_.moveFile("a.txt", "a.txt")

  def test_basicMoveNoErase(self):
    pass

  def test_basicMoveWithErase(self):
    pass

  def test_basicMoveWithOverwrite(self):
    pass
  
  def test_basicMoveNoOverwrite(self):
    pass
  
  
# --------------------------------------------------------------------------------------------------------------------
class CopyTest(unittest.TestCase):
  def test_basicCopySameLocation(self):
    pass
  
  def test_basicCopyNoErase(self):
    pass
  
  def test_basicCopyWithErase(self):
    pass

  def test_basicCopyWithOverwrite(self):
    pass
  
  def test_basicCopyNoOverwrite(self):
    pass
  
# --------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':    
  unittest.main()