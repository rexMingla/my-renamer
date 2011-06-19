#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: main entry point of the program
# --------------------------------------------------------------------------------------------------------------------
import sys
hasQt = False

try:
  from PyQt4 import QtGui, QtCore
  hasQt = True
except ImportError:  
  pass

if hasQt:
  from app import mainWindow

import unittest

from app import commandLine
from common import extension, utils
from test import test_app, test_renamer
from tv import seasonHelper, outputFormat

# --------------------------------------------------------------------------------------------------------------------
def _runGUI(cl):  
  app = QtGui.QApplication(sys.argv)
  
  mw = mainWindow.MainWindow()
  mw.show()
  
  app.exec_()
  
# --------------------------------------------------------------------------------------------------------------------
def _runNonGUI(cl):   
  utils.verify(cl.folder_, "Folder is not empty")
  seasons = seasonHelper.SeasonHelper.getSeasonsForFolders(cl.folder_, cl.isRecursive_, extension.DEFAULT_VIDEO_EXTENSIONS)
  for season in seasons:
    utils.out(season)
    for item in season.moveItemCandidates_:
      utils.out(item)

# --------------------------------------------------------------------------------------------------------------------
def _runTests():
  suite = unittest.TestSuite([
    unittest.TestLoader().loadTestsFromModule(test_app),
    unittest.TestLoader().loadTestsFromModule(test_renamer)
  ])
  
  runner = unittest.TextTestRunner(verbosity=2)
  result = runner.run(suite)
  
# --------------------------------------------------------------------------------------------------------------------
def main(argv):
  cl = commandLine.CommandLineParser(argv, "config.p")
  if cl.showHelp_:
    utils.out(cl.usageMessage())
    return
  
  if cl.runUnitTests_:
    _runTests()
  elif not cl.showGui_:
    _runNonGUI(cl)
  elif hasQt:
    _runGUI(cl)
  else:
    utils.out(cl.usageMessage())
    utils.out("PyQt4 could not be found")

# --------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
  main(sys.argv)  
  