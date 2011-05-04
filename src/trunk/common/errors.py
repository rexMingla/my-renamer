#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Errors for the application
# --------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------
class RenamerError(Exception):
  """ Base class for all exceptions within the app """
  def __init__(self, what, info=""):
    self.what_ = what
    self.info_ = info

# --------------------------------------------------------------------------------------------------------------------
class InterfaceNotImplementedError(RenamerError):
  def __init__(self, info=""):
    RenamerError.__init__(self, "InterfaceNotImplementedError", info)
    
# --------------------------------------------------------------------------------------------------------------------
class SerializationError(RenamerError):
  def __init__(self, info=""):
    RenamerError.__init__(self, "SerializationError", info)
    
# --------------------------------------------------------------------------------------------------------------------
class AssertionError(RenamerError):
  def __init__(self, info=""):
    AssertionError.__init__(self, "AssertionError", info)