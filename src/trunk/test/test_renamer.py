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

from tv import extension, outputFormat, seasonHelper, episode, season, moveItem

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
    exp.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"c01.avi")]
    act = seasonHelper.SeasonHelper.episodeMapFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
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
    
  def test_getDestinationEpisodeMapFromTVDBInvalid(self):
    exp = episode.EpisodeMap()
    act = seasonHelper.SeasonHelper.getDestinationEpisodeMapFromTVDB("Not real, Really", 1)
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
class MoveTest(unittest.TestCase):
  def setUp(self):
    source = episode.EpisodeMap()
    source.matches_ = { 1:episode.SourceEpisode(1,"01 - Done.avi"), \
                        2:episode.SourceEpisode(2,"Ready To Change.avi"), \
                        3:episode.SourceEpisode(3,"Missing New.avi")}
    source.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"Unresolved Old.avi")]

    destination = episode.EpisodeMap()
    destination.matches_ = {1:episode.DestinationEpisode(1,"Done"), \
                            2:episode.DestinationEpisode(2,"Ready"), \
                            4:episode.DestinationEpisode(4,"Missing Old")}
    #dest *should* never really happen as the tv show should always get resolved
    destination.unresolved_ = [episode.DestinationEpisode(episode.UNRESOLVED_KEY, episode.UNRESOLVED_NAME)] 
    
    self.season_ = season.Season("Test", 1, source, destination, outputFormat.DEFAULT_FORMAT)
  
  def test_done(self):
    item = moveItem.MoveItem(1, moveItem.MoveItem.DONE, "01 - Done.avi", "01 - Done.avi")
    exists = item in self.season_.moveItems_
    self.assertTrue(exists)
 
  def test_ready(self):
    item = moveItem.MoveItem(2, moveItem.MoveItem.READY, "Ready To Change.avi", "02 - Ready.avi")
    exists = item in self.season_.moveItems_
    self.assertTrue(exists)
  
  def test_missingNew(self):
    item = moveItem.MoveItem(3, moveItem.MoveItem.MISSING_NEW, "Missing New.avi", episode.UNRESOLVED_NAME)
    exists = item in self.season_.moveItems_
    self.assertTrue(exists)
  
  def test_missingOld(self):
    item = moveItem.MoveItem(4, moveItem.MoveItem.MISSING_OLD, episode.UNRESOLVED_NAME, "04 - Missing Old.avi")
    exists = item in self.season_.moveItems_
    self.assertTrue(exists)
  
  def test_unresolvedNew(self):
    item = moveItem.MoveItem(episode.UNRESOLVED_KEY, moveItem.MoveItem.UNRESOLVED_NEW, episode.UNRESOLVED_NAME, episode.UNRESOLVED_NAME)
    exists = item in self.season_.moveItems_
    self.assertTrue(exists)
  
  def test_unresolvedOld(self):
    item = moveItem.MoveItem(episode.UNRESOLVED_KEY, moveItem.MoveItem.UNRESOLVED_OLD, "Unresolved Old.avi", episode.UNRESOLVED_NAME)
    exists = item in self.season_.moveItems_
    self.assertTrue(exists)    
    
# --------------------------------------------------------------------------------------------------------------------
class SwitchFilesTest(unittest.TestCase):  
  def test_switchFileNotExists(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    after = seasonHelper.SeasonHelper.setKeyForFilename(before, 1, "d04.avi")
    self.assertEqual(before, after)
  
  def test_switchResolvedKeyForNewResolvedKey(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi"), \
                    4:episode.SourceEpisode(4,"c03.avi")}
    act = seasonHelper.SeasonHelper.setKeyForFilename(before, 4, "c03.avi")
    self.assertEqual(act, exp)

  def test_switchResolvedKeyForExistingResolvedKey(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"c03.avi")}
    exp.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"b02.avi")]
    act = seasonHelper.SeasonHelper.setKeyForFilename(before, 2, "c03.avi")
    self.assertEqual(act, exp)
    
  def test_switchResolvedKeyForSameResolvedKey(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    after = seasonHelper.SeasonHelper.setKeyForFilename(before, 1, "a01.avi")
    self.assertEqual(before, after)

  def test_switchResolvedKeyForUnresolvedKey(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"c03.avi")]
    act = seasonHelper.SeasonHelper.setKeyForFilename(before, episode.UNRESOLVED_KEY, "c03.avi")
    self.assertEqual(act, exp)
    
  def test_switchResolvedKeyForUnresolvedKey2(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "a01b.avi", "b02.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {2:episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"a01b.avi"),
                       episode.SourceEpisode(episode.UNRESOLVED_KEY,"a01.avi")] #maybe you would want this to get resolve now but for now not 
    act = seasonHelper.SeasonHelper.setKeyForFilename(before, episode.UNRESOLVED_KEY, "a01.avi")
    self.assertEqual(act, exp)

  def test_switchUnresolvedKeyForNewResolvedKey(self):
    act = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c01.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi"), \
                    3:episode.SourceEpisode(3,"c01.avi")}
    act = seasonHelper.SeasonHelper.setKeyForFilename(act, 3, "c01.avi")
    self.assertEqual(act, exp)
    
  def test_switchUnresolvedKeyForExistingResolvedKey(self):
    act = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c01.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"c01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"a01.avi")]
    act = seasonHelper.SeasonHelper.setKeyForFilename(act, 1, "c01.avi")
    self.assertEqual(act, exp)

def test_switchUnresolvedKeyForUnresolvedKey(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi", "xxx.avi"])
    after = seasonHelper.SeasonHelper.setKeyForFilename(before, episode.UNRESOLVED_KEY, "xxx.avi")
    self.assertEqual(before, after)

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