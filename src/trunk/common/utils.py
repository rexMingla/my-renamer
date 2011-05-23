#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Website:             http://code.google.com/p/dps-x509/
# Purpose of document: All the generic functions that don't have a more appropriate home
# --------------------------------------------------------------------------------------------------------------------
import logging
import inspect

import errors

# --------------------------------------------------------------------------------------------------------------------
def stackFunctionName(index = 2): #1 is calling, 2 parent etc.
  """ Print the function name. Useful in debugging """
  ret = "??"
  try:
    ret = inspect.stack()[index][3]
  except:
    pass
  return ret

# --------------------------------------------------------------------------------------------------------------------
class LogOutputModes:
  """ Defines the output formats for logging. """
  NONE = 0  
  LOG_ONLY = 1
  PRINT_ONLY = 2
  LOG_AND_PRINT = 3
  
def setLogMode(mode):
  """ Set the global log mode """
  global LOG_MODE
  assert(mode == LogOutputModes.NONE or \
         mode == LogOutputModes.LOG_ONLY or \
         mode == LogOutputModes.PRINT_ONLY or \
         mode == LogOutputModes.LOG_AND_PRINT)
  LOG_MODE = mode

def setLogLevel(level):
  """ Set the log level. level 0 -> always print. level 2 -> print only in debug. """
  global LOG_LEVEL
  LOG_LEVEL = level

def out(s, level = 0):
  """ Print to standard out and log """
  global LOG_LEVEL
  global LOG_MODE
  
  if level <= LOG_LEVEL:
    if LOG_MODE == LogOutputModes.PRINT_ONLY or LOG_MODE == LogOutputModes.LOG_AND_PRINT:
      try:
        print(s)
      except:
        pass
    if LOG_MODE == LogOutputModes.LOG_ONLY or LOG_MODE == LogOutputModes.LOG_AND_PRINT:
      try:      
        logging.info(s)
      except:
        pass

# --------------------------------------------------------------------------------------------------------------------
def verify(test, message):
  """ If test is not true print and throw. """
  if not test:
    text = "assertion failed: %s stack: %s" % (message, stackFunctionName(2))
    out(text)
    raise errors.AssertionError(text)      
      
# --------------------------------------------------------------------------------------------------------------------
def verifyType(obj, class_or_type_or_tuple, msg=""):
  """ Compare type and object are of the same class. If not true print and throw. """
  if not isinstance(obj, class_or_type_or_tuple):
    text = "%s type mismatch: %s is not %s. real type: %s" % (stackFunctionName(2), toString(obj), str(class_or_type_or_tuple), type(obj))
    out(text)
    raise errors.AssertionError(text)

# --------------------------------------------------------------------------------------------------------------------
def listCompare(left, right):
  """ 
  Compare two lists (both assumed to already be sorted). 
  Returns False if the lists are different sizes or their contents do not match up and True othewise. """
  verifyType(left, list)
  verifyType(right, list)
  isSame = len(left) == len(right)
  if isSame:
    for l, r in zip(left, right):
      if not l == r:
        out("listCompare failure: %s != %s " % (toString(l), toString(r)), 1)
        isSame = False
        break
  else:
    out("listCompare failure: #key mismatch left:%d right: %d" % (len(left), len(right)), 1)
  return isSame
  
# --------------------------------------------------------------------------------------------------------------------
def dictCompare(left, right):
  """ Compare two dictionaries. 
  Returns False if the dictionaries are different sizes or their contents do not match up and True othewise. """
  verifyType(left, dict)
  verifyType(right, dict)
  isSame = len(left) == len(right)
  if isSame:
    for key in left.keys():
      if not right.has_key(key):
        out("dictCompare failure: right missing key: %s" % key, 1)
        isSame = False
        break
      elif not left[key] == right[key]:
        out("dictCompare value mismatch: %s != %s " % (toString(left[key]), toString(right[key])), 1)
        isSame = False
        break
    for key in right.keys():
      if not left.has_key(key):
        out("dictCompare failure: left missing key: %s" % key, 1)
        isSame = False
        break
  else:
    out("dictCompare failure: #key mismatch left:%d right: %d" % (len(left), len(right)), 1)
  return isSame   

# --------------------------------------------------------------------------------------------------------------------
def toString(value, defaultIfNull=""):
  """ Attempt to convert string. returns defaultIfNull if null. """
  verify(isinstance(defaultIfNull, str), "type mismatch: defaultIfNull") #will go recursive if we use verifyType() here
  v = defaultIfNull
  try:
    v = str(value)
  except ValueError:
    pass
  
  return v

# --------------------------------------------------------------------------------------------------------------------
def toInt(value):
  """ Attempt to convert string to int. Returns 0 if it is not possible. """
  v = 0
  try:
    v = int(value)
  except ValueError:
    pass
  
  return v

# --------------------------------------------------------------------------------------------------------------------
def strToBool(value):
  """ Cast a string to a Boolean """
  verifyType(value, str)
  return value.lower() in ("yes", "true", "t", "1")

# --------------------------------------------------------------------------------------------------------------------
#set the filthy globals...
LOG_LEVEL = 0
LOG_MODE = LogOutputModes.LOG_AND_PRINT

