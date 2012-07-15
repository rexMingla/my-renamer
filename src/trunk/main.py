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
from test import test_renamer, test_move
from tv import seasonHelper, outputFormat

# --------------------------------------------------------------------------------------------------------------------
def _runGUI(cl):  
  app = QtGui.QApplication(sys.argv)
  
  mw = mainWindow.MainWindow()
  mw.show()
  
  app.exec_()

# --------------------------------------------------------------------------------------------------------------------
def _runTests():
  suite = unittest.TestSuite([
    unittest.TestLoader().loadTestsFromModule(test_renamer),
    #unittest.TestLoader().loadTestsFromModule(test_move)
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
  