#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Command line arguments for the program
# --------------------------------------------------------------------------------------------------------------------
import getopt
import os

from common import utils

class CommandLineParser:
  def usageMessage(self):
    """ Help message text displayed to user on start up error or if requested by the user. """
    ret = self._name + " [-h | -u | -g ]\n" + \
           "  -h -? --help   Show this message\n" + \
           "  -u --unittest  Run unit tests\n" + \
           "  -g --gui       Run gui (default)"
    if self._errorMessage:
      ret += "Error: " + utils.toString(self._errorMessage)
    return ret

  def __init__(self, argv):
    utils.verifyType(argv, list)
    self._name = argv[0]
    self._errorMessage = ""
    try:
      opts, args = getopt.getopt(argv[1:], "?hug", ["help", "unittest", "gui"])
    except getopt.GetoptError, err:
      self._errorMessage = err
    
    self.testOnly = False
    self.showHelp = False
    if not self._errorMessage:
      for opt, arg in opts:
        if opt in ("-?", "-h", "--help"):
          self.showHelp = True
        elif opt in ("-u", "--unittest"):
          self.testOnly = True
        elif opt in ("-g", "--gui"):
          pass
        else:
          assert(False)    
    self.showHelp = self.showHelp or bool(self._errorMessage)
  
