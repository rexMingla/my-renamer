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

import app
from tv import extension, outputFormat, seasonHelper

# --------------------------------------------------------------------------------------------------------------------
class SeriesTest(unittest.TestCase):
  def test_basic(self):
    pass
    #eps = seasonHelper.SeasonHelper.getSourceEpisodeMapFromFilenames(["a.mpg", "b.mpg"])
    
# --------------------------------------------------------------------------------------------------------------------
class ExtensionTest(unittest.TestCase):
  def test_basic(self):
    extension.FileExtensions.setExtensionsFromList([".mov",".avi"])
    self.assertEqual(extension.FileExtensions.escapedFileTypeString(), "(?:\\.mov|\\.avi)")
    
  def test_all(self):
    extension.FileExtensions.setExtensionsFromList([".mov",".*"])
    self.assertEqual(extension.FileExtensions.escapedFileTypeString(), "(?:\\..*)")

# --------------------------------------------------------------------------------------------------------------------
class OutputFormatTest(unittest.TestCase):
  def setUp(self):
    self.in_ = outputFormat.InputMap("Entourage", 1, 3, "Talk Show")
    
  def test_normal(self):
    format = outputFormat.OutputFormat("[show_name] - S[series_num]E[ep_num] - [ep_name]")
    out = format.outputToString(self.in_)
    self.assertEqual(out, "Entourage - S01E03 - Talk Show")
 
  def test_missing(self):
    format = outputFormat.OutputFormat("[show_name] - S[series_num]E[ep_num] - [ep_name ]")
    out = format.outputToString(self.in_)
    self.assertEqual(out, "Entourage - S01E03 - [ep_name ]")

# --------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  unittest.main()