#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: main entry point of the program
# --------------------------------------------------------------------------------------------------------------------
import argparse
import os
import sys

from PyQt4 import QtGui

from app import widget
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
  return runner.run(suite)
  
# --------------------------------------------------------------------------------------------------------------------
def main():
  utils.init_logging("log.txt") # TODO: make this configurable
  utils.log_info("Starting app")
    
  parser = argparse.ArgumentParser(description="run renamer app or unit tests")
  parser.add_argument("-u", "--unit-test", help="run unit tests", dest="is_test_only", 
                      action="store_true", default=False)
  args = parser.parse_args()

  if args.is_test_only:
    _runTests()
  else:
    _runGUI()

# --------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
  main()  
  