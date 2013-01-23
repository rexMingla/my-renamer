#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: main entry point of the program
# --------------------------------------------------------------------------------------------------------------------
import os
import sys

from PyQt4 import QtGui

from app import widget
from app import command_line
from common import utils

# --------------------------------------------------------------------------------------------------------------------
def _runGUI():    
  try:
    if __name__ != "__main__":
      # HACK: for py2exe so it won't show "See log for details" message on shutdown
      # http://www.py2exe.org/index.cgi/StderrLog
      sys.stdout = open("my_stdout.log", "w")
      sys.stderr = open("my_stderr.log", "w")    
    
    cwd = os.path.dirname(os.path.abspath(__file__))
    os.chdir(cwd)
  except NameError:
    pass
  
  app = QtGui.QApplication(sys.argv)
  
  mw = widget.MainWindow()
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
  utils.initLogging("log.txt") # TODO: make this configurable
  utils.logInfo("Starting app")
  
  cl = command_line.CommandLineParser()
  if cl.show_help:
    utils.logError(cl.usage_message())
    return
  
  if cl.test_only:
    _runTests()
  else:
    _runGUI()

# --------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
  main(sys.argv)  
  