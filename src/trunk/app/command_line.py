#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Command line arguments for the program
# --------------------------------------------------------------------------------------------------------------------
import getopt
import sys

class CommandLineParser:
  def usage_message(self):
    """ Help message text displayed to user on start up error or if requested by the user. """
    ret = ("{} [-h | -u | -g ]\n"
           "  -h -? --help   Show this message\n"
           "  -u --unittest  Run unit tests\n"
           "  -g --gui       Run gui (default)").format(sys.argv[0])
    if self._error:
      ret += "Error: {}".format(self._error)
    return ret

  def __init__(self):
    self._error = ""
    self.test_only = False
    self.show_help = False
    try:
      opts, _ = getopt.getopt(sys.argv[1:], "?hug", ["help", "unittest", "gui"])
    except getopt.GetoptError as err:
      self._error = str(err)
    
    if not self._error:
      for opt, _ in opts:
        if opt in ("-?", "-h", "--help"):
          self.show_help = True
        elif opt in ("-u", "--unittest"):
          self.test_only = True
        elif opt in ("-g", "--gui"):
          pass
        else:
          assert(False)    
    self.show_help = self.show_help or bool(self._error)
  
