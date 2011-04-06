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
from tv import extension, outputFormat, seasonHelper, episode

# --------------------------------------------------------------------------------------------------------------------
class SeriesTest(unittest.TestCase):
  def test_seasonFromFolderName(self):
    name, num = seasonHelper.SeasonHelper.seasonFromFolderName("c:/folder/Show Season 1/")
    self.assertEqual(name, "Show")
    self.assertEqual(num, 1)

  def test_seasonFromFolderName2(self):
    name, num = seasonHelper.SeasonHelper.seasonFromFolderName("c:/folder/Show Name Series 12")
    self.assertEqual(name, "Show Name")
    self.assertEqual(num, 12)
    
  def test_seasonFromFolderName3(self):
    name, num = seasonHelper.SeasonHelper.seasonFromFolderName("c:/folder/Show/Season 1")
    self.assertEqual(name, "Show")
    self.assertEqual(num, 1)

  def test_seasonFromFolderNameMoMatch(self):
    name, num = seasonHelper.SeasonHelper.seasonFromFolderName("c:/folder/Show Seaso 1")
    self.assertEqual(name, episode.UNRESOLVED_NAME)
    self.assertEqual(num, episode.UNRESOLVED_KEY)

  def test_episodeMapFromFilenamesGood(self):
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi"), \
                    3:episode.SourceEpisode(3,"c03.avi")}
    act = seasonHelper.SeasonHelper.episodeMapFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    #self.assertTrue(episode.EpisodeMap.areEqual(act, exp))
    self.assertEqual(act, exp)

  def test_episodeMapFromFilenamesDuplicate(self):
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved_ = [episode.SourceEpisode(1, "c01.avi")]
    act = seasonHelper.SeasonHelper.episodeMapFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    #self.assertTrue(episode.EpisodeMap.areEqual(act, exp))
    print (act)
    print (exp)
    self.assertEqual(act, exp)

  def test_episodeMapFromValidIndex(self):
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi"), \
                    3:episode.SourceEpisode(3,"c03.avi")}
    act = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    #self.assertTrue(episode.EpisodeMap.areEqual(act, exp))
    self.assertEqual(act, exp)

  def test_episodeMapFromInvalidIndex(self):
    exp = episode.EpisodeMap()
    exp.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"a01.avi"), \
                       episode.SourceEpisode(episode.UNRESOLVED_KEY,"b02.avi"), \
                       episode.SourceEpisode(episode.UNRESOLVED_KEY,"c03.avi")]
    act = seasonHelper.SeasonHelper.episodeMapFromIndex(-1, ["a01.avi", "b02.avi", "c03.avi"])
    #self.assertTrue(episode.EpisodeMap.areEqual(act, exp))
    self.assertEqual(act, exp)

  def test_episodeNumFromFilename(self):
    act = seasonHelper.SeasonHelper.episodeNumFromFilename("b02.avi")
    self.assertEqual(act, 2)

  def test_episodeNumFromInvalidFilename(self):
    act = seasonHelper.SeasonHelper.episodeNumFromFilename("bad.avi")
    self.assertEqual(act, episode.UNRESOLVED_KEY)

  def test_getMatchIndex(self):
    exp = 1
    act = seasonHelper.SeasonHelper.getMatchIndex(["a01.avi", "a02.avi", "a03.avi"])
    self.assertEqual(act, exp)
  
  def _getDestinationEpisodeMapFromTVDB(self):
    pass #covered by tvdb_api tests
    
  def _getSourceEpisodeMapFromFilenames(self):
    pass #not yet
    
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