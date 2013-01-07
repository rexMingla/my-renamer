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

from tv import tvImpl
from tv import tvInfoClient
from tv import tvManager

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
    self.assertEqual(searchParams.showName, tvImpl.UNRESOLVED_NAME)
    self.assertEqual(searchParams.seasonNum, tvImpl.UNRESOLVED_KEY)

  def test_episodeMapFromFilenamesGood(self):
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"1":tvImpl.SourceEpisode(1,"a01.avi"), \
                    "2":tvImpl.SourceEpisode(2,"b02.avi"), \
                    "3":tvImpl.SourceEpisode(3,"c03.avi")}
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    self.assertEqual(act, exp)

  def test_episodeMapFromFilenamesDuplicate(self):
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"1":tvImpl.SourceEpisode(1,"a01.avi"), \
                    "2":tvImpl.SourceEpisode(2,"b02.avi")}
    exp.unresolved = [tvImpl.SourceEpisode(tvImpl.UNRESOLVED_KEY,"c01.avi")]
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    self.assertEqual(act, exp)

  def test_getDestinationEpisodeMapFromTVDB(self):
    exp = tvImpl.DestinationEpisodeMap("Entourage", 1)
    exp.matches = {"1":tvImpl.DestinationEpisode(1,"Entourage (Pilot)"), \
                    "2":tvImpl.DestinationEpisode(2,"The Review"), \
                    "3":tvImpl.DestinationEpisode(3,"Talk Show"), \
                    "4":tvImpl.DestinationEpisode(4,"Date Night"), \
                    "5":tvImpl.DestinationEpisode(5,"The Script and the Sherpa"), \
                    "6":tvImpl.DestinationEpisode(6,"Busey and the Beach"), \
                    "7":tvImpl.DestinationEpisode(7,"The Scene"), \
                    "8":tvImpl.DestinationEpisode(8,"New York")}
    act = tvInfoClient.TvdbClient().getInfo(tvInfoClient.TvSearchParams("Entourage", 1))
    #self.assertEqual(act, exp) # take out for now
    
  def test_getDestinationEpisodeMapFromTVDBInvalid(self):
    exp = None
    act = tvInfoClient.TvdbClient().getInfo(tvInfoClient.TvSearchParams("Not real, Really", 1))
    self.assertEqual(act, exp)  
    
  def test_getSourceEpisodeMapFromFilenames(self):
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"1":tvImpl.SourceEpisode(1,"a01.avi"), \
                    "2":tvImpl.SourceEpisode(2,"a02.avi"), \
                    "3":tvImpl.SourceEpisode(3,"a03.avi"), \
                    "4":tvImpl.SourceEpisode(4,"a04x01.avi")}
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "a02.avi", "a03.avi", "a04x01.avi"])
    self.assertEqual(act, exp)

  def test_getSourceEpisodeMapFromFilenames2(self):
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"1":tvImpl.SourceEpisode(1,"a01.avi"), \
                    "2":tvImpl.SourceEpisode(2,"xxx-a02.avi"), \
                    "3":tvImpl.SourceEpisode(3,"xxx-a03.avi"), \
                    "4":tvImpl.SourceEpisode(4,"xxx-a04.avi")}
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "xxx-a02.avi", "xxx-a03.avi", "xxx-a04.avi"])
    self.assertEqual(act, exp)
    
# --------------------------------------------------------------------------------------------------------------------
class RealDataTest(unittest.TestCase):  
  def test_1(self):
    exp = tvImpl.SourceEpisodeMap()
    folder = ""
    exp.matches = {"1":tvImpl.SourceEpisode(1, folder + '01 - For Those Who Think Young.avi'),
                    "2":tvImpl.SourceEpisode(2, folder + '02 - Flight 1.avi'),
                    "3":tvImpl.SourceEpisode(3, folder + '03 - The Benefactor.avi'),
                    "4":tvImpl.SourceEpisode(4, folder + '04 - Three Sundays.avi')}
    source = [folder + '01 - For Those Who Think Young.avi',
              folder + '02 - Flight 1.avi',
              folder + '03 - The Benefactor.avi', 
              folder + '04 - Three Sundays.avi']
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(source)
    self.assertEqual(act, exp)

  def test_2(self):
    exp = tvImpl.SourceEpisodeMap()
    folder = "Season 1/"
    exp.matches = {"1":tvImpl.SourceEpisode(1, folder + '01 - For Those Who Think Young.avi'),
                    "2":tvImpl.SourceEpisode(2, folder + '02 - Flight 1.avi'),
                    "3":tvImpl.SourceEpisode(3, folder + '03 - The Benefactor.avi'),
                    "4":tvImpl.SourceEpisode(4, folder + '04 - Three Sundays.avi')}
    source = [folder + '01 - For Those Who Think Young.avi', 
              folder + '02 - Flight 1.avi', 
              folder + '03 - The Benefactor.avi', 
              folder + '04 - Three Sundays.avi']
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(source)
    self.assertEqual(act, exp)

  def test_3(self):
    #test were first two files in dir are not that good a match
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"2":tvImpl.SourceEpisode(2, 'Mad.Men.S04E02.avi'),
                "3":tvImpl.SourceEpisode(3, 'Mad.Men.S04E03.360p.HDTV.XviD.avi'),
                "4":tvImpl.SourceEpisode(4, 'Mad.Men.S04E04.360p.HDTV.XviD.avi'),
                "5":tvImpl.SourceEpisode(5, 'Mad.Men.S04E05.320p.HDTV.H264.mp4'),
                "6":tvImpl.SourceEpisode(6, 'Mad.Men.S04E06.320p.HDTV.H264.mp4'),
                "7":tvImpl.SourceEpisode(7, 'Mad.Men.S04E07.320p.HDTV.H264.mp4'),
                "8":tvImpl.SourceEpisode(8, 'Mad.Men.S04E08.320p.HDTV.H264.mp4'),
                "9":tvImpl.SourceEpisode(9, 'Mad.Men.S04E09.320p.HDTV.H264.mp4'),
                "10":tvImpl.SourceEpisode(10, 'Mad.Men.S04E10.320p.HDTV.H264.mp4'),
                "11":tvImpl.SourceEpisode(11, 'Mad.Men.S04E11.320p.HDTV.H264.mp4'),
                "12":tvImpl.SourceEpisode(12, 'Mad.Men.S04E12.480p.HDTV.H264.mp4'),
                "13":tvImpl.SourceEpisode(13, 'Mad.Men.S04E13.480p.HDTV.H264.mp4')}
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
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"1":tvImpl.SourceEpisode(1, '01 - Chapter 7.avi'),
                    "2":tvImpl.SourceEpisode(2, '02 - Chapter 8.avi'),
                    "3":tvImpl.SourceEpisode(3, '03 - Chapter 9.avi'),
                    "4":tvImpl.SourceEpisode(4, '04 - Chapter 10.avi')}
    source = ['01 - Chapter 7.avi',
              '02 - Chapter 8.avi',
              '03 - Chapter 9.avi',
              '04 - Chapter 10.avi']
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(source)
    self.assertEqual(act, exp)      
    
# --------------------------------------------------------------------------------------------------------------------
class MoveTest(unittest.TestCase):
  def setUp(self):
    self.readySrc = tvImpl.SourceEpisode(1,"01 - Ready.avi")
    self.missingNewSrc = tvImpl.SourceEpisode(3,"Missing New.avi")

    self.readyDest = tvImpl.DestinationEpisode(1,"Ready")
    self.missingOldDest = tvImpl.DestinationEpisode(2,"Missing Old.avi")
    
    source = tvImpl.SourceEpisodeMap()
    source.matches = { 1:self.readySrc, 3:self.missingNewSrc }

    destination = tvImpl.DestinationEpisodeMap()
    destination.matches = {1:self.readyDest, 2:self.missingOldDest }
    
    self.season = tvImpl.Season("Test", 1, source, destination, "")
   
  def test_ready(self):
    item = tvImpl.MoveItemCandidate(self.readySrc, self.readyDest)
    exists = item in self.season.moveItemCandidates
    self.assertTrue(exists)
  
  def test_missingNew(self):
    item = tvImpl.MoveItemCandidate(self.missingNewSrc, tvImpl.DestinationEpisode.createUnresolvedDestination())
    exists = item in self.season.moveItemCandidates
    self.assertTrue(exists)
  
  def test_missingOld(self):
    item = tvImpl.MoveItemCandidate(tvImpl.SourceEpisode.createUnresolvedSource(), self.missingOldDest)
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
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"1":tvImpl.SourceEpisode(1,"a01.avi"), \
                    "2":tvImpl.SourceEpisode(2,"b02.avi"), \
                    "4":tvImpl.SourceEpisode(4,"c03.avi")}
    act = copy.copy(before)
    act.setKeyForFilename(4, "c03.avi")
    self.assertEqual(act, exp)

  def test_switchResolvedKeyForExistingResolvedKey(self):
    before = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"1":tvImpl.SourceEpisode(1,"a01.avi"), \
                    "2":tvImpl.SourceEpisode(2,"c03.avi")}
    exp.unresolved = [tvImpl.SourceEpisode(tvImpl.UNRESOLVED_KEY,"b02.avi")]
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
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"1":tvImpl.SourceEpisode(1,"a01.avi"), \
                    "2":tvImpl.SourceEpisode(2,"b02.avi")}
    exp.unresolved = [tvImpl.SourceEpisode(tvImpl.UNRESOLVED_KEY,"c03.avi")]
    act.setKeyForFilename(tvImpl.UNRESOLVED_KEY, "c03.avi")
    self.assertEqual(act, exp)
    
  def test_switchResolvedKeyForUnresolvedKey2(self):
    before = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "a01b.avi", "b02.avi"])
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"2":tvImpl.SourceEpisode(2,"b02.avi")}
    exp.unresolved = [tvImpl.SourceEpisode(tvImpl.UNRESOLVED_KEY,"a01b.avi"),
                       tvImpl.SourceEpisode(tvImpl.UNRESOLVED_KEY,"a01.avi")] #maybe you would want this to get resolve now but for now not 
    act = copy.copy(before)
    act.setKeyForFilename(tvImpl.UNRESOLVED_KEY, "a01.avi")
    self.assertEqual(act, exp)

  def test_switchUnresolvedKeyForNewResolvedKey(self):
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"1":tvImpl.SourceEpisode(1,"a01.avi"), \
                    "2":tvImpl.SourceEpisode(2,"b02.avi"), \
                    "3":tvImpl.SourceEpisode(3,"c01.avi")}
    act.setKeyForFilename(3, "c01.avi")
    self.assertEqual(act, exp)
    
  def test_switchUnresolvedKeyForExistingResolvedKey(self):
    act = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    exp = tvImpl.SourceEpisodeMap()
    exp.matches = {"1":tvImpl.SourceEpisode(1,"c01.avi"), \
                    "2":tvImpl.SourceEpisode(2,"b02.avi")}
    exp.unresolved = [tvImpl.SourceEpisode(tvImpl.UNRESOLVED_KEY,"a01.avi")]
    act.setKeyForFilename(1, "c01.avi")
    self.assertEqual(act, exp)

  def test_switchUnresolvedKeyForUnresolvedKey(self):
    before = tvManager.TvHelper.getSourceEpisodeMapFromFilenames(["a01.avi", "b02.avi", "c03.avi", "xxx.avi"])
    after = copy.copy(before)
    after.setKeyForFilename(tvImpl.UNRESOLVED_KEY, "xxx.avi")
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