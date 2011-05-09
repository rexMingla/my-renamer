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
import copy
import unittest

from common import extension, utils
from tv import episode, moveItem, outputFormat, season, seasonHelper

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
    
  def test_episodeNumInPathNotFilename(self):
    act = seasonHelper.SeasonHelper.episodeNumFromLastNumInFilename("c:/Season 1/bad.avi")
    self.assertEqual(act, episode.UNRESOLVED_KEY)

  def test_getMatchIndex(self):
    act = seasonHelper.SeasonHelper.getMatchIndex(["a01.avi", "a02.avi", "a03.avi"])
    self.assertEqual(act, 1)
  
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

  def test_getSourceEpisodeMapFromFilenames2(self):
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"xxx-a02.avi"), \
                    3:episode.SourceEpisode(3,"xxx-a03.avi"), \
                    4:episode.SourceEpisode(4,"xxx-a04.avi")}
    act = seasonHelper.SeasonHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "xxx-a02.avi", "xxx-a03.avi", "xxx-a04.avi"])
    self.assertEqual(act, exp)    
    
# --------------------------------------------------------------------------------------------------------------------
class MoveTest(unittest.TestCase):
  def setUp(self):
    self.readySrc_ = episode.SourceEpisode(1,"01 - Ready.avi")
    self.missingNewSrc_ = episode.SourceEpisode(3,"Missing New.avi")

    self.readyDest_ = episode.DestinationEpisode(1,"Ready")
    self.missingOldDest_ = episode.DestinationEpisode(2,"Missing Old.avi")
    
    source = episode.EpisodeMap()
    source.matches_ = { 1:self.readySrc_, 3:self.missingNewSrc_ }

    destination = episode.EpisodeMap()
    destination.matches_ = {1:self.readyDest_, 2:self.missingOldDest_ }
    
    self.season_ = season.Season("Test", 1, source, destination, "")
   
  def test_ready(self):
    item = moveItem.MoveItem(self.readySrc_, self.readyDest_)
    exists = item in self.season_.moveItems_
    self.assertTrue(exists)
  
  def test_missingNew(self):
    item = moveItem.MoveItem(self.missingNewSrc_, episode.DestinationEpisode.createUnresolvedDestination())
    exists = item in self.season_.moveItems_
    self.assertTrue(exists)
  
  def test_missingOld(self):
    item = moveItem.MoveItem(episode.SourceEpisode.createUnresolvedSource(), self.missingOldDest_)
    exists = item in self.season_.moveItems_
    self.assertTrue(exists)
      
# --------------------------------------------------------------------------------------------------------------------
class SwitchFilesTest(unittest.TestCase):  
  def test_switchFileNotExists(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    after = copy.copy(before)
    after.setKeyForFilename(1, "d04.avi")
    self.assertEqual(before, after)
  
  def test_switchResolvedKeyForNewResolvedKey(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi"), \
                    4:episode.SourceEpisode(4,"c03.avi")}
    act = copy.copy(before)
    act.setKeyForFilename(4, "c03.avi")
    self.assertEqual(act, exp)

  def test_switchResolvedKeyForExistingResolvedKey(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"c03.avi")}
    exp.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"b02.avi")]
    act = copy.copy(before)
    act.setKeyForFilename(2, "c03.avi")
    self.assertEqual(act, exp)
    
  def test_switchResolvedKeyForSameResolvedKey(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    after = copy.copy(before)
    after.setKeyForFilename(1, "a01.avi")
    self.assertEqual(before, after)

  def test_switchResolvedKeyForUnresolvedKey(self):
    act = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"c03.avi")]
    act.setKeyForFilename(episode.UNRESOLVED_KEY, "c03.avi")
    self.assertEqual(act, exp)
    
  def test_switchResolvedKeyForUnresolvedKey2(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "a01b.avi", "b02.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {2:episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"a01b.avi"),
                       episode.SourceEpisode(episode.UNRESOLVED_KEY,"a01.avi")] #maybe you would want this to get resolve now but for now not 
    act = copy.copy(before)
    act.setKeyForFilename(episode.UNRESOLVED_KEY, "a01.avi")
    self.assertEqual(act, exp)

  def test_switchUnresolvedKeyForNewResolvedKey(self):
    act = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c01.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"a01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi"), \
                    3:episode.SourceEpisode(3,"c01.avi")}
    act.setKeyForFilename(3, "c01.avi")
    self.assertEqual(act, exp)
    
  def test_switchUnresolvedKeyForExistingResolvedKey(self):
    act = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c01.avi"])
    exp = episode.EpisodeMap()
    exp.matches_ = {1:episode.SourceEpisode(1,"c01.avi"), \
                    2:episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved_ = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"a01.avi")]
    act.setKeyForFilename(1, "c01.avi")
    self.assertEqual(act, exp)

def test_switchUnresolvedKeyForUnresolvedKey(self):
    before = seasonHelper.SeasonHelper.episodeMapFromIndex(1, ["a01.avi", "b02.avi", "c03.avi", "xxx.avi"])
    after = copy.copy(before)
    after.setKeyForFilename(episode.UNRESOLVED_KEY, "xxx.avi")
    self.assertEqual(before, after)

# --------------------------------------------------------------------------------------------------------------------
class ExtensionTest(unittest.TestCase):
  def test_basic(self):
    ext = extension.FileExtensions([".mov",".avi"])
    self.assertEqual(ext.escapedFileTypeString(), "(?:\\.mov|\\.avi)")
    
  def test_all(self):
    ext = extension.FileExtensions([".mov",".*"])
    self.assertEqual(ext.escapedFileTypeString(), "(?:\\..*)")

# --------------------------------------------------------------------------------------------------------------------
class OutputFormatTest(unittest.TestCase):
  def setUp(self):
    self.in_ = outputFormat.InputMap("Entourage", 1, 3, "Talk Show")
    
  def test_normal(self):
    format = outputFormat.OutputFormat("[show_name] - S[season_num]E[ep_num] - [ep_name]")
    out = format.outputToString(self.in_)
    self.assertEqual(out, "Entourage - S01E03 - Talk Show")
 
  def test_missing(self):
    format = outputFormat.OutputFormat("[show_name] - S[season_num]E[ep_num] - [ep_name ]")
    out = format.outputToString(self.in_)
    self.assertEqual(out, "Entourage - S01E03 - [ep_name ]")

# --------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  utils.setLogLevel(2)
  unittest.main()