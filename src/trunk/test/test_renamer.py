#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
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

from movie import movieInfoClient

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
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(1,"a01.avi"), 
                tvImpl.SourceFile(2,"b02.avi"), 
                tvImpl.SourceFile(3,"c03.avi")])
    act = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    self.assertEqual(act, exp)

  def test_episodeMapFromFilenamesDuplicate(self):
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(1,"a01.avi"),
                tvImpl.SourceFile(2,"b02.avi"),
                tvImpl.SourceFile(tvImpl.UNRESOLVED_KEY,"c01.avi")])
    act = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    self.assertEqual(act, exp)
  
  def _test_getDestinationEpisodeMapFromTVDB(self):
    exp = tvImpl.SeasonInfo("Entourage", 1)
    exp.episodes.extend([tvImpl.EpisodeInfo(1,"Entourage (Pilot)"), 
                          tvImpl.EpisodeInfo(2,"The Review"), 
                          tvImpl.EpisodeInfo(3,"Talk Show"), 
                          tvImpl.EpisodeInfo(4,"Date Night"), 
                          tvImpl.EpisodeInfo(5,"The Script and the Sherpa"), 
                          tvImpl.EpisodeInfo(6,"Busey and the Beach"), 
                          tvImpl.EpisodeInfo(7,"The Scene"),
                          tvImpl.EpisodeInfo(8,"New York")])
    act = tvInfoClient.TvdbClient().getInfo(tvInfoClient.TvSearchParams("Entourage", 1))
    self.assertEqual(act, exp)
    
  def test_getDestinationEpisodeMapFromTVDBInvalid(self):
    exp = None
    act = tvInfoClient.TvdbClient().getInfo(tvInfoClient.TvSearchParams("Not real, Really", 1))
    self.assertEqual(act, exp)  
    
  def test_getSourceEpisodeMapFromFilenames(self):
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(1,"a01.avi"), 
               tvImpl.SourceFile(2,"a02.avi"), 
               tvImpl.SourceFile(3,"a03.avi"), 
               tvImpl.SourceFile(4,"a04x01.avi")])
    act = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "a02.avi", "a03.avi", "a04x01.avi"])
    self.assertEqual(act, exp)

  def test_getSourceEpisodeMapFromFilenames2(self):
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(1,"a01.avi"), \
                tvImpl.SourceFile(2,"xxx-a02.avi"), \
                tvImpl.SourceFile(3,"xxx-a03.avi"), \
                tvImpl.SourceFile(4,"xxx-a04.avi")])
    act = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "xxx-a02.avi", "xxx-a03.avi", "xxx-a04.avi"])
    self.assertEqual(act, exp)
    
# --------------------------------------------------------------------------------------------------------------------
class RealDataTest(unittest.TestCase):  
  def test_1(self):
    exp = tvImpl.SourceFiles()
    folder = ""
    exp.extend([tvImpl.SourceFile(1, folder + '01 - For Those Who Think Young.avi'),
               tvImpl.SourceFile(2, folder + '02 - Flight 1.avi'),
               tvImpl.SourceFile(3, folder + '03 - The Benefactor.avi'),
               tvImpl.SourceFile(4, folder + '04 - Three Sundays.avi')])
    source = [folder + '01 - For Those Who Think Young.avi',
              folder + '02 - Flight 1.avi',
              folder + '03 - The Benefactor.avi', 
              folder + '04 - Three Sundays.avi']
    act = tvManager.TvHelper.getSourcesFromFilenames(source)
    self.assertEqual(act, exp)

  def test_2(self):
    exp = tvImpl.SourceFiles()
    folder = "Season 1/"
    exp.extend([tvImpl.SourceFile(1, folder + '01 - For Those Who Think Young.avi'),
               tvImpl.SourceFile(2, folder + '02 - Flight 1.avi'),
               tvImpl.SourceFile(3, folder + '03 - The Benefactor.avi'),
               tvImpl.SourceFile(4, folder + '04 - Three Sundays.avi')])
    source = [folder + '01 - For Those Who Think Young.avi', 
              folder + '02 - Flight 1.avi', 
              folder + '03 - The Benefactor.avi', 
              folder + '04 - Three Sundays.avi']
    act = tvManager.TvHelper.getSourcesFromFilenames(source)
    self.assertEqual(act, exp)

  def test_3(self):
    #test were first two files in dir are not that good a match
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(2, 'Mad.Men.S04E02.avi'),
               tvImpl.SourceFile(3, 'Mad.Men.S04E03.360p.HDTV.XviD.avi'),
               tvImpl.SourceFile(4, 'Mad.Men.S04E04.360p.HDTV.XviD.avi'),
               tvImpl.SourceFile(5, 'Mad.Men.S04E05.320p.HDTV.H264.mp4'),
               tvImpl.SourceFile(6, 'Mad.Men.S04E06.320p.HDTV.H264.mp4'),
               tvImpl.SourceFile(7, 'Mad.Men.S04E07.320p.HDTV.H264.mp4'),
               tvImpl.SourceFile(8, 'Mad.Men.S04E08.320p.HDTV.H264.mp4'),
               tvImpl.SourceFile(9, 'Mad.Men.S04E09.320p.HDTV.H264.mp4'),
               tvImpl.SourceFile(10, 'Mad.Men.S04E10.320p.HDTV.H264.mp4'),
               tvImpl.SourceFile(11, 'Mad.Men.S04E11.320p.HDTV.H264.mp4'),
               tvImpl.SourceFile(12, 'Mad.Men.S04E12.480p.HDTV.H264.mp4'),
               tvImpl.SourceFile(13, 'Mad.Men.S04E13.480p.HDTV.H264.mp4')])
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
    act = tvManager.TvHelper.getSourcesFromFilenames(source)
    self.assertEqual(act, exp)

  def test_4(self):
    #test were filename match is found but is not the best match. ie. starting from 1. 
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(1, '01 - Chapter 7.avi'),
               tvImpl.SourceFile(2, '02 - Chapter 8.avi'),
               tvImpl.SourceFile(3, '03 - Chapter 9.avi'),
               tvImpl.SourceFile(4, '04 - Chapter 10.avi')])
    source = ['01 - Chapter 7.avi',
              '02 - Chapter 8.avi',
              '03 - Chapter 9.avi',
              '04 - Chapter 10.avi']
    act = tvManager.TvHelper.getSourcesFromFilenames(source)
    self.assertEqual(act, exp)      
    
# --------------------------------------------------------------------------------------------------------------------
class MoveTest(unittest.TestCase):
  def setUp(self):
    self.readySrc = tvImpl.SourceFile(1,"01 - Ready.avi")
    self.missingNewSrc = tvImpl.SourceFile(3,"Missing New.avi")

    self.readyDest = tvImpl.EpisodeInfo(1,"Ready")
    self.missingOldDest = tvImpl.EpisodeInfo(2,"Missing Old.avi")
    
    source = tvImpl.SourceFiles()
    source.extend([tvImpl.SourceFile(1, self.readySrc.filename),
                   tvImpl.SourceFile(3, self.missingNewSrc.filename)])

    destination = tvImpl.SeasonInfo()
    destination.episodes.extend([self.readyDest, self.missingOldDest])
    self.season = tvImpl.Season("Test", destination, source)
   
  def test_ready(self):
    item = tvImpl.EpisodeRenameItem(self.readySrc.filename, self.readyDest)
    self.assertTrue(item in self.season.episodeMoveItems)
  
  def test_missingNew(self):
    item = tvImpl.EpisodeRenameItem(self.missingNewSrc.filename, tvImpl.EpisodeInfo.createUnresolvedEpisode())
    self.assertTrue(item in self.season.episodeMoveItems)
  
  def test_missingOld(self):
    item = tvImpl.EpisodeRenameItem(tvImpl.UNRESOLVED_NAME, self.missingOldDest)
    self.assertTrue(item in self.season.episodeMoveItems)
      
# --------------------------------------------------------------------------------------------------------------------
class SwitchFilesTest(unittest.TestCase):  
  def test_switchFileNotExists(self):
    before = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    after = copy.copy(before)
    after.setEpisodeForFilename(1, "d04.avi")
    self.assertEqual(before, after)
  
  def test_switchResolvedKeyForNewResolvedKey(self):
    before = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(1,"a01.avi"), 
                tvImpl.SourceFile(2,"b02.avi"),
                tvImpl.SourceFile(4,"c03.avi")])
    act = copy.copy(before)
    act.setEpisodeForFilename(4, "c03.avi")
    self.assertEqual(act, exp)

  def test_switchResolvedKeyForExistingResolvedKey(self):
    act = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    act.setEpisodeForFilename(2, "c03.avi")
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(1,"a01.avi"),
                tvImpl.SourceFile(2,"c03.avi"),
                tvImpl.SourceFile(tvImpl.UNRESOLVED_KEY,"b02.avi")])
    self.assertEqual(act, exp)
    
  def test_switchResolvedKeyForSameResolvedKey(self):
    before = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    after = copy.copy(before)
    after.setEpisodeForFilename(1, "a01.avi")
    self.assertEqual(before, after)

  def test_switchResolvedKeyForUnresolvedKey(self):
    act = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(1,"a01.avi"),
                tvImpl.SourceFile(2,"b02.avi"),
                tvImpl.SourceFile(tvImpl.UNRESOLVED_KEY,"c03.avi")])
    act.setEpisodeForFilename(tvImpl.UNRESOLVED_KEY, "c03.avi")
    self.assertEqual(act, exp)
    
  def test_switchResolvedKeyForUnresolvedKey2(self):
    before = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "a01b.avi", "b02.avi"])
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(2,"b02.avi"),
                tvImpl.SourceFile(tvImpl.UNRESOLVED_KEY,"a01.avi"),
                tvImpl.SourceFile(tvImpl.UNRESOLVED_KEY,"a01b.avi")]) 
    #maybe you would want a01.avi this to get resolve now but for now not 
    act = copy.copy(before)
    act.setEpisodeForFilename(tvImpl.UNRESOLVED_KEY, "a01.avi")
    self.assertEqual(act, exp)

  def test_switchUnresolvedKeyForNewResolvedKey(self):
    act = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(1,"a01.avi"),
               tvImpl.SourceFile(2,"b02.avi"),
               tvImpl.SourceFile(3,"c01.avi")])
    act.setEpisodeForFilename(3, "c01.avi")
    self.assertEqual(act, exp)
    
  def test_switchUnresolvedKeyForExistingResolvedKey(self):
    act = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    exp = tvImpl.SourceFiles()
    exp.extend([tvImpl.SourceFile(1,"c01.avi"),
                tvImpl.SourceFile(2,"b02.avi"),
                tvImpl.SourceFile(tvImpl.UNRESOLVED_KEY,"a01.avi")])
    act.setEpisodeForFilename(1, "c01.avi")
    self.assertEqual(act, exp)

  def test_switchUnresolvedKeyForUnresolvedKey(self):
    before = tvManager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi", "xxx.avi"])
    after = copy.copy(before)
    after.setEpisodeForFilename(tvImpl.UNRESOLVED_KEY, "xxx.avi")
    self.assertEqual(before, after)

# --------------------------------------------------------------------------------------------------------------------
class OutputFormatTest(unittest.TestCase):
  def setUp(self):
    self.formatter = outputFormat.TvNameFormatter()
    self.info = tvImpl.AdvancedEpisodeInfo("Entourage", 1, 3, "Talk Show")
    
  def test_normal(self):
    out = self.formatter.getNameFromInfo("<show> - S<s_num>E<ep_num> - <ep_name>", self.info)
    self.assertEqual(out, "Entourage - S01E03 - Talk Show")
 
  def test_missing(self):
    out = self.formatter.getNameFromInfo("<show> - S<s_num>E<ep_num> - <ep_name >", self.info)
    self.assertEqual(out, "Entourage - S01E03 - <ep_name >")

# --------------------------------------------------------------------------------------------------------------------
class AdvancedOutputFormat(unittest.TestCase):
    
  def test_omit(self):
    formatter = outputFormat.MovieNameFormatter()
    info = movieInfoClient.MovieInfo("Anchorman", 2004, ["Comedy"], "", "")
    out = formatter.getNameFromInfo("<g> - <t> (<y>)%( - Disc <p>)%", info)
    self.assertEqual(out, "Comedy - Anchorman (2004)")

  def test_include(self):
    formatter = outputFormat.MovieNameFormatter()
    info = movieInfoClient.MovieInfo("Anchorman", 2004, ["Comedy"], "", "2")
    out = formatter.getNameFromInfo("<g> - <t> (<y>)%( - Disc <p>)%", info)
    self.assertEqual(out, "Comedy - Anchorman (2004) - Disc 2")

# --------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  unittest.main()