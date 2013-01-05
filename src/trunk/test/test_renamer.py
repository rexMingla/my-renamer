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

from common import utils
from common import extension
from common import outputFormat

from tv import episode
from tv import moveItemCandidate
from tv import season
from tv import tvManager
from tv import tvInfoClient

# --------------------------------------------------------------------------------------------------------------------
class SeriesTest(unittest.TestCase):
  def test_seasonFromFolderName(self):
    searchParams = tvManager.TvHelper.seasonFromFolderName("c:/folder/Show - Season 1")
    self.assertEqual(searchParams.showName, "Show")
    self.assertEqual(searchParams.seasonNum, 1)

  def test_seasonFromFolderName2(self):
    searchParams = tvManager.TvHelper.seasonFromFolderName("c:/folder/Show Name - Series 12")
    self.assertEqual(searchParams.showName, "Show Name")
    self.assertEqual(searchParams.seasonNum, 12)
    
  def test_seasonFromFolderName3(self):
    searchParams = tvManager.TvHelper.seasonFromFolderName("c:/folder/Show/Season 1")
    self.assertEqual(searchParams.showName, "Show")
    self.assertEqual(searchParams.seasonNum, 1)

  def test_seasonFromFolderNameMoMatch(self):
    searchParams = tvManager.TvHelper.seasonFromFolderName("c:/folder/Show Seaso 1")
    self.assertEqual(searchParams.showName, episode.UNRESOLVED_NAME)
    self.assertEqual(searchParams.seasonNum, episode.UNRESOLVED_KEY)

  def test_episodeMapFromFilenamesGood(self):
    exp = episode.SourceEpisodeMap()
    exp.matches = {"1":episode.SourceEpisode(1,"a01.avi"), \
                    "2":episode.SourceEpisode(2,"b02.avi"), \
                    "3":episode.SourceEpisode(3,"c03.avi")}
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    self.assertEqual(act, exp)

  def test_episodeMapFromFilenamesDuplicate(self):
    exp = episode.SourceEpisodeMap()
    exp.matches = {"1":episode.SourceEpisode(1,"a01.avi"), \
                    "2":episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"c01.avi")]
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    self.assertEqual(act, exp)

  def test_getDestinationEpisodeMapFromTVDB(self):
    exp = episode.DestinationEpisodeMap("Entourage", 1)
    exp.matches = {"1":episode.DestinationEpisode(1,"Entourage (Pilot)"), \
                    "2":episode.DestinationEpisode(2,"The Review"), \
                    "3":episode.DestinationEpisode(3,"Talk Show"), \
                    "4":episode.DestinationEpisode(4,"Date Night"), \
                    "5":episode.DestinationEpisode(5,"The Script and the Sherpa"), \
                    "6":episode.DestinationEpisode(6,"Busey and the Beach"), \
                    "7":episode.DestinationEpisode(7,"The Scene"), \
                    "8":episode.DestinationEpisode(8,"New York")}
    act = tvInfoClient.TvdbClient().getInfo(tvInfoClient.TvSearchParams("Entourage", 1))
    #self.assertEqual(act, exp) # take out for now
    
  def test_getDestinationEpisodeMapFromTVDBInvalid(self):
    exp = None
    act = tvInfoClient.TvdbClient().getInfo(tvInfoClient.TvSearchParams("Not real, Really", 1))
    self.assertEqual(act, exp)  
    
  def test_getSourceEpisodeMapFromFilenames(self):
    exp = episode.SourceEpisodeMap()
    exp.matches = {"1":episode.SourceEpisode(1,"a01.avi"), \
                    "2":episode.SourceEpisode(2,"a02.avi"), \
                    "3":episode.SourceEpisode(3,"a03.avi"), \
                    "4":episode.SourceEpisode(4,"a04x01.avi")}
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "a02.avi", "a03.avi", "a04x01.avi"])
    self.assertEqual(act, exp)

  def test_getSourceEpisodeMapFromFilenames2(self):
    exp = episode.SourceEpisodeMap()
    exp.matches = {"1":episode.SourceEpisode(1,"a01.avi"), \
                    "2":episode.SourceEpisode(2,"xxx-a02.avi"), \
                    "3":episode.SourceEpisode(3,"xxx-a03.avi"), \
                    "4":episode.SourceEpisode(4,"xxx-a04.avi")}
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "xxx-a02.avi", "xxx-a03.avi", "xxx-a04.avi"])
    self.assertEqual(act, exp)
    
# --------------------------------------------------------------------------------------------------------------------
class RealDataTest(unittest.TestCase):  
  def test_1(self):
    exp = episode.SourceEpisodeMap()
    folder = ""
    exp.matches = {"1":episode.SourceEpisode(1, folder + '01 - For Those Who Think Young.avi'),
                    "2":episode.SourceEpisode(2, folder + '02 - Flight 1.avi'),
                    "3":episode.SourceEpisode(3, folder + '03 - The Benefactor.avi'),
                    "4":episode.SourceEpisode(4, folder + '04 - Three Sundays.avi')}
    source = [folder + '01 - For Those Who Think Young.avi',
              folder + '02 - Flight 1.avi',
              folder + '03 - The Benefactor.avi', 
              folder + '04 - Three Sundays.avi']
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(source)
    self.assertEqual(act, exp)

  def test_2(self):
    exp = episode.SourceEpisodeMap()
    folder = "Season 1/"
    exp.matches = {"1":episode.SourceEpisode(1, folder + '01 - For Those Who Think Young.avi'),
                    "2":episode.SourceEpisode(2, folder + '02 - Flight 1.avi'),
                    "3":episode.SourceEpisode(3, folder + '03 - The Benefactor.avi'),
                    "4":episode.SourceEpisode(4, folder + '04 - Three Sundays.avi')}
    source = [folder + '01 - For Those Who Think Young.avi', 
              folder + '02 - Flight 1.avi', 
              folder + '03 - The Benefactor.avi', 
              folder + '04 - Three Sundays.avi']
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(source)
    self.assertEqual(act, exp)

  def test_3(self):
    #test were first two files in dir are not that good a match
    exp = episode.SourceEpisodeMap()
    exp.matches = {"2":episode.SourceEpisode(2, 'Mad.Men.S04E02.avi'),
                "3":episode.SourceEpisode(3, 'Mad.Men.S04E03.360p.HDTV.XviD.avi'),
                "4":episode.SourceEpisode(4, 'Mad.Men.S04E04.360p.HDTV.XviD.avi'),
                "5":episode.SourceEpisode(5, 'Mad.Men.S04E05.320p.HDTV.H264.mp4'),
                "6":episode.SourceEpisode(6, 'Mad.Men.S04E06.320p.HDTV.H264.mp4'),
                "7":episode.SourceEpisode(7, 'Mad.Men.S04E07.320p.HDTV.H264.mp4'),
                "8":episode.SourceEpisode(8, 'Mad.Men.S04E08.320p.HDTV.H264.mp4'),
                "9":episode.SourceEpisode(9, 'Mad.Men.S04E09.320p.HDTV.H264.mp4'),
                "10":episode.SourceEpisode(10, 'Mad.Men.S04E10.320p.HDTV.H264.mp4'),
                "11":episode.SourceEpisode(11, 'Mad.Men.S04E11.320p.HDTV.H264.mp4'),
                "12":episode.SourceEpisode(12, 'Mad.Men.S04E12.480p.HDTV.H264.mp4'),
                "13":episode.SourceEpisode(13, 'Mad.Men.S04E13.480p.HDTV.H264.mp4')}
    source = ['Mad.Men.S04E02.avi',
              'Mad.Men.S04E03.360p.HDTV.XviD.avi', 
              'Mad.Men.S04E04.360p.HDTV.XviD.avi', 
              'Mad.Men.S04E05.320p.HDTV.H264.mp4', 
              'Mad.Men.S04E06.320p.HDTV.H264.mp4', 
              'Mad.Men.S04E07.320p.HDTV.H264.mp4', 
              'Mad.Men.S04E08.320p.HDTV.H264.mp4', 
              'Mad.Men.S04E09.320p.HDTV.H264.mp4', 
              'Mad.Men.S04E10.320p.HDTV.H264.mp4', 
              'Mad.Men.S04E11.320p.HDTV.H264.mp4', 
              'Mad.Men.S04E12.480p.HDTV.H264.mp4', 
              'Mad.Men.S04E13.480p.HDTV.H264.mp4']
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(source)
    self.assertEqual(act, exp)

  def test_4(self):
    #test were filename match is found but is not the best match. ie. starting from 1. 
    exp = episode.SourceEpisodeMap()
    exp.matches = {"1":episode.SourceEpisode(1, '01 - Chapter 7.avi'),
                    "2":episode.SourceEpisode(2, '02 - Chapter 8.avi'),
                    "3":episode.SourceEpisode(3, '03 - Chapter 9.avi'),
                    "4":episode.SourceEpisode(4, '04 - Chapter 10.avi')}
    source = ['01 - Chapter 7.avi',
              '02 - Chapter 8.avi',
              '03 - Chapter 9.avi',
              '04 - Chapter 10.avi']
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(source)
    self.assertEqual(act, exp)      
    
# --------------------------------------------------------------------------------------------------------------------
class MoveTest(unittest.TestCase):
  def setUp(self):
    self.readySrc = episode.SourceEpisode(1,"01 - Ready.avi")
    self.missingNewSrc = episode.SourceEpisode(3,"Missing New.avi")

    self.readyDest = episode.DestinationEpisode(1,"Ready")
    self.missingOldDest = episode.DestinationEpisode(2,"Missing Old.avi")
    
    source = episode.SourceEpisodeMap()
    source.matches = { 1:self.readySrc, 3:self.missingNewSrc }

    destination = episode.DestinationEpisodeMap()
    destination.matches = {1:self.readyDest, 2:self.missingOldDest }
    
    self.season = season.Season("Test", 1, source, destination, "")
   
  def test_ready(self):
    item = moveItemCandidate.MoveItemCandidate(self.readySrc, self.readyDest)
    exists = item in self.season.moveItemCandidates
    self.assertTrue(exists)
  
  def test_missingNew(self):
    item = moveItemCandidate.MoveItemCandidate(self.missingNewSrc, episode.DestinationEpisode.createUnresolvedDestination())
    exists = item in self.season.moveItemCandidates
    self.assertTrue(exists)
  
  def test_missingOld(self):
    item = moveItemCandidate.MoveItemCandidate(episode.SourceEpisode.createUnresolvedSource(), self.missingOldDest)
    exists = item in self.season.moveItemCandidates
    self.assertTrue(exists)
      
# --------------------------------------------------------------------------------------------------------------------
class SwitchFilesTest(unittest.TestCase):  
  def test_switchFileNotExists(self):
    before = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    after = copy.copy(before)
    after.setKeyForFilename(1, "d04.avi")
    self.assertEqual(before, after)
  
  def test_switchResolvedKeyForNewResolvedKey(self):
    before = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    exp = episode.SourceEpisodeMap()
    exp.matches = {"1":episode.SourceEpisode(1,"a01.avi"), \
                    "2":episode.SourceEpisode(2,"b02.avi"), \
                    "4":episode.SourceEpisode(4,"c03.avi")}
    act = copy.copy(before)
    act.setKeyForFilename(4, "c03.avi")
    self.assertEqual(act, exp)

  def test_switchResolvedKeyForExistingResolvedKey(self):
    before = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    exp = episode.SourceEpisodeMap()
    exp.matches = {"1":episode.SourceEpisode(1,"a01.avi"), \
                    "2":episode.SourceEpisode(2,"c03.avi")}
    exp.unresolved = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"b02.avi")]
    act = copy.copy(before)
    act.setKeyForFilename(2, "c03.avi")
    self.assertEqual(act, exp)
    
  def test_switchResolvedKeyForSameResolvedKey(self):
    before = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    after = copy.copy(before)
    after.setKeyForFilename(1, "a01.avi")
    self.assertEqual(before, after)

  def test_switchResolvedKeyForUnresolvedKey(self):
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    exp = episode.SourceEpisodeMap()
    exp.matches = {"1":episode.SourceEpisode(1,"a01.avi"), \
                    "2":episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"c03.avi")]
    act.setKeyForFilename(episode.UNRESOLVED_KEY, "c03.avi")
    self.assertEqual(act, exp)
    
  def test_switchResolvedKeyForUnresolvedKey2(self):
    before = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "a01b.avi", "b02.avi"])
    exp = episode.SourceEpisodeMap()
    exp.matches = {"2":episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"a01b.avi"),
                       episode.SourceEpisode(episode.UNRESOLVED_KEY,"a01.avi")] #maybe you would want this to get resolve now but for now not 
    act = copy.copy(before)
    act.setKeyForFilename(episode.UNRESOLVED_KEY, "a01.avi")
    self.assertEqual(act, exp)

  def test_switchUnresolvedKeyForNewResolvedKey(self):
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    exp = episode.SourceEpisodeMap()
    exp.matches = {"1":episode.SourceEpisode(1,"a01.avi"), \
                    "2":episode.SourceEpisode(2,"b02.avi"), \
                    "3":episode.SourceEpisode(3,"c01.avi")}
    act.setKeyForFilename(3, "c01.avi")
    self.assertEqual(act, exp)
    
  def test_switchUnresolvedKeyForExistingResolvedKey(self):
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    exp = episode.SourceEpisodeMap()
    exp.matches = {"1":episode.SourceEpisode(1,"c01.avi"), \
                    "2":episode.SourceEpisode(2,"b02.avi")}
    exp.unresolved = [episode.SourceEpisode(episode.UNRESOLVED_KEY,"a01.avi")]
    act.setKeyForFilename(1, "c01.avi")
    self.assertEqual(act, exp)

  def test_switchUnresolvedKeyForUnresolvedKey(self):
    before = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c03.avi", "xxx.avi"])
    after = copy.copy(before)
    after.setKeyForFilename(episode.UNRESOLVED_KEY, "xxx.avi")
    self.assertEqual(before, after)

# --------------------------------------------------------------------------------------------------------------------
class OutputFormatTest(unittest.TestCase):
  def setUp(self):
    self.ip = outputFormat.TvInputMap("Entourage", 1, 3, "Talk Show")
    
  def test_normal(self):
    fmt = outputFormat.OutputFormat("<show> - S<s_num>E<ep_num> - <ep_name>")
    out = fmt.outputToString(self.ip)
    self.assertEqual(out, "Entourage - S01E03 - Talk Show")
 
  def test_missing(self):
    fmt = outputFormat.OutputFormat("<show> - S<s_num>E<ep_num> - <ep_name >")
    out = fmt.outputToString(self.ip)
    self.assertEqual(out, "Entourage - S01E03 - <ep_name >")

# --------------------------------------------------------------------------------------------------------------------
class AdvancedOutputFormat(unittest.TestCase):
    
  def test_omit(self):
    ip = outputFormat.MovieInputMap("Anchorman", 2004, "Comedy", "", "")    
    fmt = outputFormat.OutputFormat("<g> - <t> (<y>)%( - Disc <p>)%")
    out = fmt.outputToString(ip)
    self.assertEqual(out, "Comedy - Anchorman (2004)")

  def test_include(self):
    ip = outputFormat.MovieInputMap("Anchorman", 2004, "Comedy", "2", "")
    fmt = outputFormat.OutputFormat("<g> - <t> (<y>)%( - Disc <p>)%")
    out = fmt.outputToString(ip)
    self.assertEqual(out, "Comedy - Anchorman (2004) - Disc 2")

# --------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  unittest.main()