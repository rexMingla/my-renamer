#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import sys
sys.path.append("..")

import tvdb_api
import os
import re
import string
import unicodedata

import moveItem

MODE_TEST   = 0
MODE_NORMAL = 1

FILE_TYPES = [".avi", ".mov"] 

# -----------------------------------------------------------------------------------
def escapedFileTypes():
  global FILE_TYPES
  exts = []
  for type in FILE_TYPES:
    exts.append(re.escape(type))
  ret = "(?:%s)" % "|".join(exts)
  return ret

# -----------------------------------------------------------------------------------
def episodeFromShow(episode):
  ep = -1
  episodeRegex = "^.*?(\\d\\d?)\\D*%s$" % escapedFileTypes()
  m = re.match(episodeRegex, episode, flags=re.IGNORECASE)
  if m:
    ep = int(m.group(1))
    out("episode: %s #:%d" % (episode, ep), 1)
  else:
    out("** unresolved: %s" % episode, 1)
  return ep

# -----------------------------------------------------------------------------------
def filenameGenerator(show, season, epNum, epName, ext=".avi"):
  #ret = "%s - %sx%s - %s" % (show, season, epNum, epName)
  ret = "%s - %s%s" % (epNum, epName, ext)
  
  validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)
  cleanedFilename = unicodedata.normalize('NFKD', ret).encode('ASCII', 'ignore')
  return ''.join(c for c in cleanedFilename if c in validFilenameChars)
  
# -----------------------------------------------------------------------------------
def episodeMapFromIndex(index, season):
  out("episodeMapFromIndex...", 1)
  epMap = {}
  if index != -1:
    epRegex = "^.{%d}(\\d\\d?).*%s$" % (index, escapedFileTypes())
    for file in season:
      m = re.match(epRegex, file)
      if m:
        ep = "%02d" % int(m.group(1))
        if not epMap.has_key(ep):
          epMap[ep] = file
  return epMap

# -----------------------------------------------------------------------------------
def episodeMapFromSeason(season):
  epMap = {}
  for file in season:
    epNum = episodeFromShow(file)
    if epNum != -1:
      epMap["%02d" % epNum] = file
  return epMap
  
# -----------------------------------------------------------------------------------
def getMatchIndex(fileA, fileB):
  #search for two concecutive numbers where the second ones are the same
  index = -1
  minLen = len(fileA)
  if len(fileB) < minLen:
    minLen = len(fileB)
  for i in range(minLen-1):
    if fileA[i] == fileB[i]:
      a = fileA[i:i+2]
      b = fileB[i:i+2]
      if re.match("\\d{2}", a) and re.match("\\d{2}", b) and not a == b:
        index = i
        break
    else:
      break
  return index




# -----------------------------------------------------------------------------------
class SeasonChecker:
  OK                          = 1
  UNBALANCED_FILES            = -1
  NEW_NAME_PATTERN_UNRESOLVED = -2
  OLD_NAME_PATTERN_UNRESOLVED = -3
  SEASON_UNRESOLVED           = -4
  UNKNOWN                     = -5
  
# -----------------------------------------------------------------------------------
  @staticmethod
  def resultStr(result):
    if   result == SeasonChecker.OK:                          return "OK"
    elif result == SeasonChecker.UNBALANCED_FILES:            return "UNBALANCED_FILES"
    elif result == SeasonChecker.NEW_NAME_PATTERN_UNRESOLVED: return "NEW_NAME_PATTERN_UNRESOLVED"
    elif result == SeasonChecker.OLD_NAME_PATTERN_UNRESOLVED: return "OLD_NAME_PATTERN_UNRESOLVED"
    elif result == SeasonChecker.SEASON_UNRESOLVED:           return "SEASON_UNRESOLVED"
    else:                                                      assert(False); return "UNKNOWN"

# -----------------------------------------------------------------------------------
  def __init__(self, root, show, seriesNum, realFiles):
    self.root_          = root
    self.show_          = show
    self.seriesNum_     = seriesNum
    
    self.oldFiles_      = []
    for f in realFiles:
      global FILE_TYPES
      for ext in FILE_TYPES:
        if f.endswith(ext):
          self.oldFiles_.append(f)
          break
    self.oldFiles_.sort()

    self.tvdbseriesNum_ = getSeason(show, seriesNum)
    self.oldEpMap_      = {}
    self.newEpMap_      = {}
    self.state_         = SeasonChecker.UNKNOWN
    self.moveList_      = []
    
    self._createMaps()
    self._createMoveList()
          
# -----------------------------------------------------------------------------------
  def __str__(self):
    lenOld = lenNew = lenOldRes = lenNewRes ="n/a"
    if self.oldFiles_:
      lenOld = str(len(self.oldFiles_))
    if self.tvdbseriesNum_:
      lenNew = str(len(self.tvdbseriesNum_))
    if self.oldEpMap_:
      lenOldRes = str(len(self.oldEpMap_))
    if self.newEpMap_:
      lenNewRes = str(len(self.newEpMap_))
    return "show: [%s] %s seriesNum: %d #total (old:new) (%s:%s) #resolved (%s:%s)" % \
      (SeasonChecker.resultStr(self.state_), self.show_, self.seriesNum_, lenOld, lenNew, lenOldRes, lenNewRes)
      
 # ----------------------------------------------------------------------------------- 
  def _createMaps(self):
    self.oldEpMap_ = {}
    ext = ".avi"
    if len(self.oldFiles_):
      (newBase, ext) = os.path.splitext(self.oldFiles_[0])
      tmpMaps = []
      tmpMaps.append(episodeMapFromIndex(0, self.oldFiles_)) #should match all if previously done
      tmpMaps.append(episodeMapFromSeason(self.oldFiles_))
      
      if len(self.oldFiles_) > 1:
        index = getMatchIndex(self.oldFiles_[0], self.oldFiles_[1])
        if index != -1:
          tmpMaps.append(episodeMapFromIndex(index, self.oldFiles_))
      for m in tmpMaps:
        if len(m) > len(self.oldEpMap_):
          self.oldEpMap_ = m

    if not self.tvdbseriesNum_:
      self.state_ = SeasonChecker.SEASON_UNRESOLVED
      return      
      
    self.newEpMap_ = {}
    for i in self.tvdbseriesNum_:
      show = self.tvdbseriesNum_[i]
      epNum = "%02d" % int(show["episodenumber"])
      self.newEpMap_[epNum] = filenameGenerator(self.show_, "%02d" % self.seriesNum_, epNum, show["episodename"], ext)

    if len(self.tvdbseriesNum_) != len(self.newEpMap_):
      self.state_ = SeasonChecker.UNBALANCED_FILES
      return 

    if len(self.tvdbseriesNum_) != len(self.oldFiles_):
      self.state_ = SeasonChecker.UNBALANCED_FILES
      return 

    oldMapList = self.oldEpMap_.keys()
    oldMapList.sort()
    newMapList = self.newEpMap_.keys()
    newMapList.sort()
    if oldMapList == newMapList:
      self.state_ = SeasonChecker.OK
    else:
      self.state_ = SeasonChecker.UNBALANCED_FILES

 # ----------------------------------------------------------------------------------- 
  def _createMoveList(self):
    type = moveItem.MoveItem.UNKNOWN
    for key in self.oldEpMap_:
      oldFile = self.oldEpMap_[key]
      newFile = "n/a"
      type = moveItem.MoveItem.M_NEW
      if self.newEpMap_ and self.newEpMap_.has_key(key):
        newFile = self.newEpMap_[key]
        if newFile == oldFile:
          type = moveItem.MoveItem.DONE
        else:
          type = moveItem.MoveItem.READY
      self.moveList_.append(MoveItem(key, type, oldFile, newFile))
    
    if self.newEpMap_:
      for key in self.newEpMap_:
        if not key in self.oldEpMap_.keys():
          self.moveList_.append(MoveItem(key, moveItem.MoveItem.M_OLD, "n/a", self.newEpMap_[key]))
    
    for file in self.oldFiles_:
      if not file in self.oldEpMap_.values():
        self.moveList_.append(MoveItem("n/a", moveItem.MoveItem.U_OLD, file, ""))

    if self.tvdbseriesNum_:
      for i in self.tvdbseriesNum_:
        if not self.newEpMap_ or not ("%02d" % i) in self.newEpMap_.keys():
          show = self.tvdbseriesNum_[i]
          epNum = "%02d" % int(show["episodenumber"])
          newName = filenameGenerator(self.show_, "%02d" % self.seriesNum_, epNum, show["episodename"])
          self.moveList_.append(MoveItem("n/a", moveItem.MoveItem.U_NEW, "", newName))
          
    self.moveList_ = sorted(self.moveList_, key=lambda item: item.key_)

# -----------------------------------------------------------------------------------
  def printMoveFiles(self):
    for moveItem in self.moveList_:
      out("%s" % str(moveItem))
      
# -----------------------------------------------------------------------------------
  def moveFiles(self):
    nMoved = nFailed = 0
    for item in self.moveList_:
      if moveItem.matchType_ == moveItem.READY:
        old = os.path.join(self.root_, moveItem.oldName_)
        new = os.path.join(self.root_, moveItem.newName_)
        if os.path.exists(new):
          utils.out("** File exists in location: %s **" % new)
          nFailed += 1
        else:          
          os.rename(old, new)
          nMoved += 1
    return nMoved, nFailed
  
# -----------------------------------------------------------------------------------
def updateDir(dir, mode=MODE_TEST):
  splitFolderRegex = "^.*/(.*)/(?:season|series)\\s+(\\d+)$"        #/show/season
  sameFolderRegex  = "^.*/(.*)\\s+(?:season|series)\\s+(\\d+)$"  #/show - season
  dir = dir.replace("\\", "/") #for regex
  
  seriesList = []
  utils.out("---- Directory: %s : Dir exists? %s ----" % (dir, os.path.exists(dir)))
  for root, dirs, files in os.walk(dir):
    isAcceptedMsg = ""
    if len(files):
      show = ""
      seriesNum = -1
      m = re.match(splitFolderRegex, root, flags=re.IGNORECASE)
      if not m:
        m = re.match(sameFolderRegex, root, flags=re.IGNORECASE)
      if m:
        show = m.group(1)
        seriesNum = int(m.group(2))
        sc = SeasonChecker(root, show, seriesNum, files)
        if len(sc.oldFiles_):
          isAcceptedMsg = "*"
          seriesList.append(sc)
    utils.out("root: %s #dirs: %d #files: %d%s" % (root, len(dirs), len(files), isAcceptedMsg))
        
  results = {}
  utils.out("------------")
  utils.out("   Dirs found: %d" % len(seriesList))
  utils.out("------------")
  nMoved = nFailed = 0
  for series in seriesList:
    out("---%s" % str(series))
    series.printMoveFiles()
    ret = series.state_
    if not results.has_key(ret):
      results[ret] = []
    results[ret].append(series)
    #if ret == SeasonChecker.OK and not mode == MODE_TEST:
    if not mode == MODE_TEST:
      moved, failed = series.moveFiles()
      nMoved += moved
      nFailed += failed  
  utils.out("------------")
  utils.out("Summary:")
  for key in results:
    utils.out("%s: %d" % (SeasonChecker.resultStr(key), len(results[key]))) 
  if not mode == MODE_TEST:
    utils.out("------------")
    utils.out("Moved: %d Failed: %d" % (nMoved, nFailed))
  utils.out("------------")

# -----------------------------------------------------------------------------------
dir = "J:/media/Tv Series/"
#dir = "H:/media/Tv Series/"
#dir = "\\\\10.1.1.8\\OneTouch_4\\media\\Tv Series\\"
#dir = "C:\\Users\\Tim\\Documents\\Azureus Downloads\\Mad Men"
#dir = "C:/Users/Tim/Documents/Azureus Downloads/Mad Men/Mad Men Season 2"

if __name__ == "__main__": 
  updateDir(dir, mode=MODE_NORMAL) #MODE_NORMAL | MODE_TEST