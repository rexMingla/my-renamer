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
    name, num = seasonHelper.SeasonHelper.seasonFromFolderName("c:/folder/Show - Season 1/")
    self.assertEqual(name, "Show")
    self.assertEqual(num, 1)

  def test_seasonFromFolderName2(self):
    name, num = seasonHelper.SeasonHelper.seasonFromFolderName("c:/folder/Show Name - Series 12")
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
    self.assertEqual(act, exp)

  def test_episodeMapFromFilenamesDuplicate(self):
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved_ = [episode.SourceEpisode(1,"c01.avi")]
    act = seasonHelper.SeasonHelper.episodeMapFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    print (act)
    print (exp)
    self.assertEqual(act, exp)

  def test_episodeMapFromValidIndex(self):
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi"), \
                    3:episode.SourceEpisode(3,"c03.avi")}
    act = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    self.assertEqual(act, exp)

  def test_episodeMapFromInvalidIndex(self):
    exp = episode.EpisodeMap()
    exp.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"a01.avi"), \
                       episode.SourceEpisode(episode.UNRESOLVED_KEY,"b02.avi"), \
                       episode.SourceEpisode(episode.UNRESOLVED_KEY,"c03.avi")]
    act = seasonHelper.SeasonHelper.episodeMapFromIndex(-1, ["a01.avi", "b02.avi", "c03.avi"])
    self.assertEqual(act, exp)

  def test_episodeNumFromLastNumInFilename(self):
    act = seasonHelper.SeasonHelper.episodeNumFromLastNumInFilename("b02.avi")
    self.assertEqual(act, 2)

  def test_episodeNumFromLastNumInFilename2(self):
    act = seasonHelper.SeasonHelper.episodeNumFromLastNumInFilename("b02x03.avi")
    self.assertEqual(act, 3)

  def test_episodeNumFromInvalidFilename(self):
    act = seasonHelper.SeasonHelper.episodeNumFromLastNumInFilename("bad.avi")
    self.assertEqual(act, episode.UNRESOLVED_KEY)

  def test_getMatchIndex(self):
    exp = 1
    act = seasonHelper.SeasonHelper.getMatchIndex(["a01.avi", "a02.avi", "a03.avi"])
    self.assertEqual(act, exp)
  
  def test_getDestinationEpisodeMapFromTVDB(self):
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.DestinationEpisode(1,"Entourage (Pilot)"), \
                    2:episode.DestinationEpisode(2,"The Review"), \
                    3:episode.DestinationEpisode(3,"Talk Show"), \
                    4:episode.DestinationEpisode(4,"Date Night"), \
                    5:episode.DestinationEpisode(5,"The Script & The Sherpa"), \
                    6:episode.DestinationEpisode(6,"Busey And The Beach"), \
                    7:episode.DestinationEpisode(7,"The Scene"), \
                    8:episode.DestinationEpisode(8,"New York")}
    act = seasonHelper.SeasonHelper.getDestinationEpisodeMapFromTVDB("Entourage", 1)
    self.assertEqual(act, exp)
    
  def test_getSourceEpisodeMapFromFilenames(self):
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"a02.avi"), \
                    3:episode.SourceEpisode(3,"a03.avi"), \
                    4:episode.SourceEpisode(4,"a04x01.avi")}
    act = seasonHelper.SeasonHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "a02.avi", "a03.avi", "a04x01.avi"])
    self.assertEqual(act, exp)

    
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