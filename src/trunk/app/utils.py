#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Website:             http://code.google.com/p/dps-x509/
# Purpose of document: All the generic functions that don't have a more appropriate home
# --------------------------------------------------------------------------------------------------------------------
import errors
import logging
import inspect

# --------------------------------------------------------------------------------------------------------------------
def stackFunctionName(index = 2): #1 is calling, 2 parent etc.
  ret = "??"
  try:
    ret = inspect.stack()[index][3]
  except:
    pass
  return ret

# --------------------------------------------------------------------------------------------------------------------
class LogOutputModes:
  """ defines the output formats for logging """
  NONE = 0  
  LOG_ONLY = 1
  PRINT_ONLY = 2
  LOG_AND_PRINT = 3
  
def setLogMode(mode):
  """ set the global log mode """
  global LOG_MODE
  assert(mode == LogOutputModes.NONE or \
         mode == LogOutputModes.LOG_ONLY or \
         mode == LogOutputModes.PRINT_ONLY or \
         mode == LogOutputModes.LOG_AND_PRINT)
  LOG_MODE = mode

def setLogLevel(level):
  """ level 0 -> always print. level 2 -> print only in debug """
  global LOG_LEVEL
  LOG_LEVEL = 0

def out(s, level = 0):
  """ print to standard out and log """
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
  """ if test is not true throw
  @param test: test to assert on
  @type  test: bool
  @param message: to display on error
  @type  message: string
  @raise errors.AssertionError: if test == False """
  if not test:
    text = "assertion failed: %s stack: %s" % (message, stackFunctionName(2))
    out(text)
    raise errors.AssertionError(text)      
      
# --------------------------------------------------------------------------------------------------------------------
def verifyType(obj, class_or_type_or_tuple, msg=""):
  """ if test is not true throw
  @param test: test to assert on
  @type  test: bool
  @param message: to display on error
  @type  message: string
  @raise errors.AssertionError: if different """
  if not isinstance(obj, class_or_type_or_tuple):
    text = "%s type mismatch: %s is not %s" % (stackFunctionName(2), toString(obj), str(class_or_type_or_tuple))
    out(text)
    raise errors.AssertionError(text)

# --------------------------------------------------------------------------------------------------------------------
def listCompare(left, right):
  #assumes lists are already ordered
  verifyType(left, list)
  verifyType(right, list)
  isSame = len(left) == len(right)
  if isSame:
    for l, r in zip(left, right):
      if not l == r:
        out("listCompare failure: %s != %s " % (toString(l), toString(r)))
        isSame = False
        break
  return isSame
  
# --------------------------------------------------------------------------------------------------------------------
def dictCompare(left, right):
  verifyType(left, dict)
  verifyType(right, dict)
  isSame = len(left) == len(right)
  if isSame:
    for key in left.keys():
      if not right.has_key(key):
        out("dictCompare failure: right missing key: %s" % key)
        isSame = False
        break
      elif not left[key] == right[key]:
        out("dictCompare value mismatch: %s != %s " % (toString(left[key]), toString(right[key])))
        isSame = False
        break
    if isSame:
      for key in right.keys():
        if not left.has_key(key):
          out("dictCompare failure: left missing key: %s" % key)
          isSame = False
          break
  return isSame   

# --------------------------------------------------------------------------------------------------------------------
def toString(value, defaultIfNull=""):
  """ 
  attempt to convert string. returns defaultIfNull if null 
  @rtype: string 
  """
  verify(isinstance(defaultIfNull, str), "type mismatch: defaultIfNull")
  v = defaultIfNull
  try:
    v = str(value)
  except ValueError:
    pass
  
  return v

# --------------------------------------------------------------------------------------------------------------------
def toInt(value):
  """ 
  attempt to convert string to int. returns 0 if it is not possible
  @rtype: int
  """
  v = 0
  try:
    v = int(value)
  except ValueError:
    pass
  
  return v

# --------------------------------------------------------------------------------------------------------------------
def strToBool(value):
  verifyType(value, str)
  return value.lower() in ("yes", "true", "t", "1")

# --------------------------------------------------------------------------------------------------------------------
#set the filthy globals...
LOG_LEVEL = 0
LOG_MODE = LogOutputModes.LOG_AND_PRINT

