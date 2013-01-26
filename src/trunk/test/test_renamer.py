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

from common import formatting

from media.tv import types as tv_types
from media.tv import client as tv_client
from media.tv import manager as tv_manager

from media.movie import types as movie_types

# --------------------------------------------------------------------------------------------------------------------
class SeriesTest(unittest.TestCase):
  def test_seasonFromFolderName(self):
    searchParams = tv_manager.TvHelper.seasonFromFolderName("c:/folder/Show - Season 1")
    self.assertEqual(searchParams.showName, "Show")
    self.assertEqual(searchParams.seasonNum, 1)

  def test_seasonFromFolderName2(self):
    searchParams = tv_manager.TvHelper.seasonFromFolderName("c:/folder/Show Name - Series 12")
    self.assertEqual(searchParams.showName, "Show Name")
    self.assertEqual(searchParams.seasonNum, 12)
    
  def test_seasonFromFolderName3(self):
    searchParams = tv_manager.TvHelper.seasonFromFolderName("c:/folder/Show/Season 1")
    self.assertEqual(searchParams.showName, "Show")
    self.assertEqual(searchParams.seasonNum, 1)

  def test_seasonFromFolderNameMoMatch(self):
    searchParams = tv_manager.TvHelper.seasonFromFolderName("c:/folder/Show Seaso 1")
    self.assertEqual(searchParams.showName, tv_types.UNRESOLVED_NAME)
    self.assertEqual(searchParams.seasonNum, tv_types.UNRESOLVED_KEY)

  def test_episodeMapFromFilenamesGood(self):
    exp = tv_types.SourceFiles()
    exp.extend([tv_types.SourceFile(1,"a01.avi"), 
                tv_types.SourceFile(2,"b02.avi"), 
                tv_types.SourceFile(3,"c03.avi")])
    act = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    self.assertEqual(act, exp)

  def test_episodeMapFromFilenamesDuplicate(self):
    exp = tv_types.SourceFiles()
    exp.extend([tv_types.SourceFile(1,"a01.avi"),
                tv_types.SourceFile(2,"b02.avi"),
                tv_types.SourceFile(tv_types.UNRESOLVED_KEY,"c01.avi")])
    act = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    self.assertEqual(act, exp)
  
  def _test_getDestinationEpisodeMapFromTVDB(self):
    exp = tv_types.SeasonInfo("Entourage", 1)
    exp.episodes.extend([tv_types.EpisodeInfo(1,"Entourage (Pilot)"), 
                          tv_types.EpisodeInfo(2,"The Review"), 
                          tv_types.EpisodeInfo(3,"Talk Show"), 
                          tv_types.EpisodeInfo(4,"Date Night"), 
                          tv_types.EpisodeInfo(5,"The Script and the Sherpa"), 
                          tv_types.EpisodeInfo(6,"Busey and the Beach"), 
                          tv_types.EpisodeInfo(7,"The Scene"),
                          tv_types.EpisodeInfo(8,"New York")])
    act = tv_client.TvdbClient().getInfo(tv_types.TvSearchParams("Entourage", 1))
    self.assertEqual(act, exp)
    
  def test_getDestinationEpisodeMapFromTVDBInvalid(self):
    exp = None
    act = tv_client.TvdbClient().getInfo(tv_types.TvSearchParams("Not real, Really", 1))
    self.assertEqual(act, exp)  
    
  def test_getSourceEpisodeMapFromFilenames(self):
    exp = tv_types.SourceFiles()
    exp.extend([tv_types.SourceFile(1,"a01.avi"), 
               tv_types.SourceFile(2,"a02.avi"), 
               tv_types.SourceFile(3,"a03.avi"), 
               tv_types.SourceFile(4,"a04x01.avi")])
    act = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "a02.avi", "a03.avi", "a04x01.avi"])
    self.assertEqual(act, exp)

  def test_getSourceEpisodeMapFromFilenames2(self):
    exp = tv_types.SourceFiles()
    exp.extend([tv_types.SourceFile(1,"a01.avi"), \
                tv_types.SourceFile(2,"xxx-a02.avi"), \
                tv_types.SourceFile(3,"xxx-a03.avi"), \
                tv_types.SourceFile(4,"xxx-a04.avi")])
    act = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "xxx-a02.avi", "xxx-a03.avi", "xxx-a04.avi"])
    self.assertEqual(act, exp)
    
# --------------------------------------------------------------------------------------------------------------------
class RealDataTest(unittest.TestCase):  
  def test_1(self):
    exp = tv_types.SourceFiles()
    folder = ""
    exp.extend([tv_types.SourceFile(1, folder + '01 - For Those Who Think Young.avi'),
               tv_types.SourceFile(2, folder + '02 - Flight 1.avi'),
               tv_types.SourceFile(3, folder + '03 - The Benefactor.avi'),
               tv_types.SourceFile(4, folder + '04 - Three Sundays.avi')])
    source = [folder + '01 - For Those Who Think Young.avi',
              folder + '02 - Flight 1.avi',
              folder + '03 - The Benefactor.avi', 
              folder + '04 - Three Sundays.avi']
    act = tv_manager.TvHelper.getSourcesFromFilenames(source)
    self.assertEqual(act, exp)

  def test_2(self):
    exp = tv_types.SourceFiles()
    folder = "Season 1/"
    exp.extend([tv_types.SourceFile(1, folder + '01 - For Those Who Think Young.avi'),
               tv_types.SourceFile(2, folder + '02 - Flight 1.avi'),
               tv_types.SourceFile(3, folder + '03 - The Benefactor.avi'),
               tv_types.SourceFile(4, folder + '04 - Three Sundays.avi')])
    source = [folder + '01 - For Those Who Think Young.avi', 
              folder + '02 - Flight 1.avi', 
              folder + '03 - The Benefactor.avi', 
              folder + '04 - Three Sundays.avi']
    act = tv_manager.TvHelper.getSourcesFromFilenames(source)
    self.assertEqual(act, exp)

  def test_3(self):
    #test were first two files in dir are not that good a match
    exp = tv_types.SourceFiles()
    exp.extend([tv_types.SourceFile(2, 'Mad.Men.S04E02.avi'),
               tv_types.SourceFile(3, 'Mad.Men.S04E03.360p.HDTV.XviD.avi'),
               tv_types.SourceFile(4, 'Mad.Men.S04E04.360p.HDTV.XviD.avi'),
               tv_types.SourceFile(5, 'Mad.Men.S04E05.320p.HDTV.H264.mp4'),
               tv_types.SourceFile(6, 'Mad.Men.S04E06.320p.HDTV.H264.mp4'),
               tv_types.SourceFile(7, 'Mad.Men.S04E07.320p.HDTV.H264.mp4'),
               tv_types.SourceFile(8, 'Mad.Men.S04E08.320p.HDTV.H264.mp4'),
               tv_types.SourceFile(9, 'Mad.Men.S04E09.320p.HDTV.H264.mp4'),
               tv_types.SourceFile(10, 'Mad.Men.S04E10.320p.HDTV.H264.mp4'),
               tv_types.SourceFile(11, 'Mad.Men.S04E11.320p.HDTV.H264.mp4'),
               tv_types.SourceFile(12, 'Mad.Men.S04E12.480p.HDTV.H264.mp4'),
               tv_types.SourceFile(13, 'Mad.Men.S04E13.480p.HDTV.H264.mp4')])
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
    act = tv_manager.TvHelper.getSourcesFromFilenames(source)
    self.assertEqual(act, exp)

  def test_4(self):
    #test were filename match is found but is not the best match. ie. starting from 1. 
    exp = tv_types.SourceFiles()
    exp.extend([tv_types.SourceFile(1, '01 - Chapter 7.avi'),
               tv_types.SourceFile(2, '02 - Chapter 8.avi'),
               tv_types.SourceFile(3, '03 - Chapter 9.avi'),
               tv_types.SourceFile(4, '04 - Chapter 10.avi')])
    source = ['01 - Chapter 7.avi',
              '02 - Chapter 8.avi',
              '03 - Chapter 9.avi',
              '04 - Chapter 10.avi']
    act = tv_manager.TvHelper.getSourcesFromFilenames(source)
    self.assertEqual(act, exp)      
    
# --------------------------------------------------------------------------------------------------------------------
class MoveTest(unittest.TestCase):
  def setUp(self):
    self.readySrc = tv_types.SourceFile(1,"01 - Ready.avi")
    self.missingNewSrc = tv_types.SourceFile(3,"Missing New.avi")

    self.readyDest = tv_types.EpisodeInfo(1,"Ready")
    self.missingOldDest = tv_types.EpisodeInfo(2,"Missing Old.avi")
    
    source = tv_types.SourceFiles()
    source.extend([tv_types.SourceFile(1, self.readySrc.filename),
                   tv_types.SourceFile(3, self.missingNewSrc.filename)])

    destination = tv_types.SeasonInfo()
    destination.episodes.extend([self.readyDest, self.missingOldDest])
    self.season = tv_types.Season("Test", destination, source)
   
  def test_ready(self):
    item = tv_types.EpisodeRenameItem(self.readySrc.filename, self.readyDest)
    self.assertTrue(item in self.season.episodeMoveItems)
  
  def test_missingNew(self):
    item = tv_types.EpisodeRenameItem(self.missingNewSrc.filename, tv_types.EpisodeInfo.createUnresolvedEpisode())
    self.assertTrue(item in self.season.episodeMoveItems)
  
  def test_missingOld(self):
    item = tv_types.EpisodeRenameItem(tv_types.UNRESOLVED_NAME, self.missingOldDest)
    self.assertTrue(item in self.season.episodeMoveItems)
      
# --------------------------------------------------------------------------------------------------------------------
class SwitchFilesTest(unittest.TestCase):  
  def test_switchFileNotExists(self):
    before = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    after = copy.copy(before)
    after.setEpisodeForFilename(1, "d04.avi")
    self.assertEqual(before, after)
  
  def test_switchResolvedKeyForNewResolvedKey(self):
    act = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    exp = tv_types.SourceFiles()
    exp.extend([tv_types.SourceFile(1,"a01.avi"), 
                tv_types.SourceFile(2,"b02.avi"),
                tv_types.SourceFile(4,"c03.avi")])
    act.setEpisodeForFilename(4, "c03.avi")
    self.assertEqual(act, exp)

  def test_switchResolvedKeyForExistingResolvedKey(self):
    act = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    act.setEpisodeForFilename(2, "c03.avi")
    self.assertTrue(tv_types.SourceFile(1,"a01.avi") in act)
    self.assertTrue(tv_types.SourceFile(2,"c03.avi") in act)
    self.assertTrue(tv_types.SourceFile(tv_types.UNRESOLVED_KEY,"b02.avi") in act)
    
  def test_switchResolvedKeyForSameResolvedKey(self):
    before = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    after = copy.copy(before)
    after.setEpisodeForFilename(1, "a01.avi")
    self.assertEqual(before, after)

  def test_switchResolvedKeyForUnresolvedKey(self):
    act = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi"])
    exp = tv_types.SourceFiles()
    exp.extend([tv_types.SourceFile(1,"a01.avi"),
                tv_types.SourceFile(2,"b02.avi"),
                tv_types.SourceFile(tv_types.UNRESOLVED_KEY,"c03.avi")])
    act.setEpisodeForFilename(tv_types.UNRESOLVED_KEY, "c03.avi")
    self.assertEqual(act, exp)
    
  def test_switchResolvedKeyForUnresolvedKey2(self):
    act = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "a01b.avi", "b02.avi"])
    act.setEpisodeForFilename(tv_types.UNRESOLVED_KEY, "a01.avi")
    self.assertTrue(tv_types.SourceFile(2,"b02.avi") in act)
    self.assertTrue(tv_types.SourceFile(tv_types.UNRESOLVED_KEY,"a01.avi") in act)
    self.assertTrue(tv_types.SourceFile(tv_types.UNRESOLVED_KEY,"a01b.avi") in act) 
  
  def test_switchUnresolvedKeyForNewResolvedKey(self):
    act = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    act.setEpisodeForFilename(3, "c01.avi")
    self.assertTrue(tv_types.SourceFile(1,"a01.avi") in act)
    self.assertTrue(tv_types.SourceFile(2,"b02.avi") in act)
    self.assertTrue(tv_types.SourceFile(3,"c01.avi") in act)
    
  def test_switchUnresolvedKeyForExistingResolvedKey(self):
    act = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c01.avi"])
    act.setEpisodeForFilename(1, "c01.avi")
    self.assertTrue(tv_types.SourceFile(1,"c01.avi") in act)
    self.assertTrue(tv_types.SourceFile(2,"b02.avi") in act)
    self.assertTrue(tv_types.SourceFile(tv_types.UNRESOLVED_KEY,"a01.avi") in act)

  def test_switchUnresolvedKeyForUnresolvedKey(self):
    before = tv_manager.TvHelper.getSourcesFromFilenames(["a01.avi", "b02.avi", "c03.avi", "xxx.avi"])
    after = copy.copy(before)
    after.setEpisodeForFilename(tv_types.UNRESOLVED_KEY, "xxx.avi")
    self.assertEqual(before, after)

# --------------------------------------------------------------------------------------------------------------------
class OutputFormatTest(unittest.TestCase):
  def setUp(self):
    self.formatter = formatting.TvNameFormatter()
    self.info = tv_types.AdvancedEpisodeInfo("Entourage", 1, 3, "Talk Show")
    
  def test_normal(self):
    out = self.formatter.getNameFromInfo("<show> - S<s_num>E<ep_num> - <ep_name>", self.info)
    self.assertEqual(out, "Entourage - S01E03 - Talk Show")
 
  def test_missing(self):
    out = self.formatter.getNameFromInfo("<show> - S<s_num>E<ep_num> - <ep_name >", self.info)
    self.assertEqual(out, "Entourage - S01E03 - <ep_name >")

# --------------------------------------------------------------------------------------------------------------------
class AdvancedOutputFormat(unittest.TestCase):
    
  def test_omit(self):
    formatter = formatting.MovieNameFormatter()
    info = movie_types.MovieInfo("Anchorman", 2004, ["Comedy"], "", "")
    out = formatter.getNameFromInfo("<g> - <t> (<y>)%( - Disc <p>)%", info)
    self.assertEqual(out, "Comedy - Anchorman (2004)")

  def test_include(self):
    formatter = formatting.MovieNameFormatter()
    info = movie_types.MovieInfo("Anchorman", 2004, ["Comedy"], "", "2")
    out = formatter.getNameFromInfo("<g> - <t> (<y>)%( - Disc <p>)%", info)
    self.assertEqual(out, "Comedy - Anchorman (2004) - Disc 2")

# --------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  unittest.main()