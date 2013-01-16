#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: main entry point of the program
# --------------------------------------------------------------------------------------------------------------------
import os
import sys

from app import commandLine
from common import utils

# --------------------------------------------------------------------------------------------------------------------
def _runGUI(cl):  
  from PyQt4 import QtGui
  from app import mainWindow
  
  try:
    if __name__ != "__main__":
      # HACK: for py2exe so it won't show "See log for details" message on shutdown
      # http://www.py2exe.org/index.cgi/StderrLog
      sys.stdout = open("my_stdout.log", "w")
      sys.stderr = open("my_stderr.log", "w")    
    
    dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(dir)
  except NameError:
    pass
  
  app = QtGui.QApplication(sys.argv)
  
  mw = mainWindow.MainWindow()
  mw.show()
  app.exec_()

# --------------------------------------------------------------------------------------------------------------------
def _runTests():
  import unittest

  from test import test_renamer
  from test import test_move

  suite = unittest.TestSuite([
    unittest.TestLoader().loadTestsFromModule(test_renamer),
    unittest.TestLoader().loadTestsFromModule(test_move)
  ])
  
  runner = unittest.TextTestRunner(verbosity=2)
  result = runner.run(suite)
  
# --------------------------------------------------------------------------------------------------------------------
def main(argv):
  utils.initLogging("log.txt")
  cl = commandLine.CommandLineParser()
  if cl.showHelp:
    utils.logError(cl.usageMessage())
    return
  
  if cl.testOnly:
    _runTests()
  else:
    _runGUI(cl)

# --------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
  main(sys.argv)  
  