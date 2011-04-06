#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: main entry point of the program
# --------------------------------------------------------------------------------------------------------------------
import sys

# --------------------------------------------------------------------------------------------------------------------
def _runGUI():
  from PyQt4 import QtGui, QtCore
  from app import mainWindow
  
  app = QtGui.QApplication(sys.argv)
  
  mw = mainWindow.MainWindow()
  mw.show()
  
  app.exec_()

# --------------------------------------------------------------------------------------------------------------------
def _runTests():
  import unittest
  from test import test_app, test_renamer

  suite = unittest.TestSuite([
      unittest.TestLoader().loadTestsFromModule(test_app),
      unittest.TestLoader().loadTestsFromModule(test_renamer)
  ])
  
  runner = unittest.TextTestRunner(verbosity=2)
  result = runner.run(suite)
  if result.wasSuccessful():
      return 0
  else:
      return 1
  
# --------------------------------------------------------------------------------------------------------------------
def main(argv):
  #TODO:parse command line args
  
  if False:
    _runGUI()
  else:
    _runTests()

# --------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
  main(sys.argv)  
  