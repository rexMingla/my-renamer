#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import utils
import getopt
import os

class CommandLineParser:
  def usageMessage(self):
    ret = self.name_ + " [-h | -u | -c configFile | -n options]\n" + \
           "  -h -? --help        Show this message\n" + \
           "  -u --unit-tests     Run unit tests\n" + \
           "  -c --config <name>  Config file for GUI mode\n" + \
           "  -n --no-gui         Run in console mode\n" + \
           "options are:\n" + \
           "  -f --folder <name>  Folder to rename.\n" + \
           "  -r --recursive      Recurse sub folders. Default False\n" + \
           "  -t --test-only      Show changes without moving files. Default False\n"
    if self.errorMessage_:
      ret += "Error: " + self.errorMessage_
    return ret

  def __init__(self, argv, defaultConfig=""):
    utils.verifyType(argv, list)
    utils.verifyType(defaultConfig, str)
    utils.verify(len(argv), "Must be at least one argument")
    self.name_ = argv[0]
    self.errorMessage_ = ""
    try:
      opts, args = getopt.getopt(argv[1:], "?hc:uf:rnt", ["help", "config=", "folder=", "recursive", "no-gui", "test"])
    except getopt.GetoptError, err:
      self.errorMessage_ = err
    
    self.showGui_ = True
    self.folder_ = ""
    self.isRecursive_ = False
    self.config_ = defaultConfig
    self.testOnly_ = False
    self.runUnitTests_ = False
    self.showHelp_ = False
    if not self.errorMessage_:
      for opt, arg in opts:
        if opt in ("-?", "-h", "--help"):
          self.showHelp_ = True
        elif opt in ("-c", "--config"):
          self.config_ = arg
        elif opt in ("-u", "--unit-tests"):
          self.runUnitTests_ = True
        elif opt in ("-f", "--folder"):
          self.folder_ = arg
        elif opt in ("-t", "--test-only"):
          self.testOnly_ = True
        elif opt in ("-r", "--recursive"):
          self.isRecursive_ = True
        elif opt in ("-n", "--no-gui"):
          self.showGui_ = False
        else:
          assert(False)    
    if not self.showGui_ and not self.folder_:
      self.errorMessage_ = "folder must be supplied"
    elif self.showGui_ and not self.config_:
      self.errorMessage_ = "configFile must be supplied"
        
    self.showHelp_ = self.showHelp_ or not not self.errorMessage_
  
