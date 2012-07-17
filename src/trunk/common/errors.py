#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Errors for the application
# --------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------
class RenamerError(Exception):
  """ Base class for all exceptions within the app. """
  def __init__(self, what, info=""):
    super(RenamerError, self).__init__()
    self.what_ = what
    self.info_ = info

# --------------------------------------------------------------------------------------------------------------------
class InterfaceNotImplementedError(RenamerError):
  """ Calling a 'pure virtual' that has not been overloaded in a derived class. """
  def __init__(self, info=""):
    super(InterfaceNotImplementedError, self).__init__("InterfaceNotImplementedError", info)
    
# --------------------------------------------------------------------------------------------------------------------
class SerializationError(RenamerError):
  """ Unable to read from/write error. """
  def __init__(self, info=""):
    super(SerializationError, self).__init__("SerializationError", info)
    
# --------------------------------------------------------------------------------------------------------------------
class AssertionError(RenamerError):
  """ Actual and expected resuls differ. """
  def __init__(self, info=""):
    super(AssertionError, self).__init__("AssertionError", info)