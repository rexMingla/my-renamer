#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Website:             http://code.google.com/p/my-renamer/
# Purpose of document: All the generic functions that don't have a more appropriate home
# --------------------------------------------------------------------------------------------------------------------
import logging
import inspect
import re
import time

UNDECODABLE_ERROR_MESSAGE = "<could not decode>"
MIN_VIDEO_SIZE_BYTES = 20 * 1024 * 1024 # 20 MB

# --------------------------------------------------------------------------------------------------------------------
def stackFunctionName(index=2): #1 is calling, 2 parent etc.
  """ Print the function name. Useful in debugging """
  ret = "??"
  try:
    ret = inspect.stack()[index][3]
  except IndexError:
    pass
  return ret

# --------------------------------------------------------------------------------------------------------------------
class LogItem:
  """ Information contained in a log entry. """
  def __init__(self, logLevel, action, shortMessage, longMessage=""):
    #utils.verifyType(logLevel, int)
    #utils.verifyType(action, str)
    #utils.verifyType(shortMessage, str)
    #utils.verifyType(longMessage, str)
    self.logLevel = logLevel
    self.action = action
    self.shortMessage = shortMessage
    self.longMessage = longMessage or shortMessage
    
# --------------------------------------------------------------------------------------------------------------------
class LogLevel:
  """ Log levels copied from logging. """
  CRITICAL = 50
  FATAL = CRITICAL
  ERROR = 40
  WARNING = 30
  WARN = WARNING
  INFO = 20
  DEBUG = 10
  NOTSET = 0

# --------------------------------------------------------------------------------------------------------------------
def initLogging(logfile):
  logging.basicConfig(level=logging.DEBUG,
                      format="%(asctime)s %(title)-12s %(name)-12s %(levelname)-8s %(message)s",
                      datefmt="%Y-%m-%d %H:%M",
                      filename=logfile,
                      filemode="a")

  for logName in ("PyQt4", "requests", "tvdb_api"):
    logging.getLogger(logName).setLevel(logging.CRITICAL)

  console = logging.StreamHandler()
  console.setFormatter(logging.Formatter("%(name)-12s %(levelname)-8s %(message)s"))
  console.setLevel(logging.INFO)
  logging.getLogger("renamer").addHandler(console)

def logNotSet(msg, longMsg="", title=""):
  log(LogLevel.NOTSET, msg, longMsg, title)

def logDebug(msg, longMsg="", title=""):
  log(LogLevel.DEBUG, msg, longMsg, title)

def logInfo(msg, longMsg="", title=""):
  log(LogLevel.INFO, msg, longMsg, title)

def logWarning(msg, longMsg="", title=""):
  log(LogLevel.WARNING, msg, longMsg, title)

def logError(msg, longMsg="", title=""):
  log(LogLevel.ERROR, msg, longMsg, title)

def log(level, msg, longMsg="", title=""):
  logging.getLogger("renamer").log(level, msg or longMsg, extra={"title":title}) 

# --------------------------------------------------------------------------------------------------------------------
def verify(test, message):
  """ If test is not true print and throw. """
  if not test:
    text = "assertion failed: {} stack: {}".format(message, stackFunctionName(2))
    logNotSet(text, title="utils.verify")
    raise AssertionError(text)      

# --------------------------------------------------------------------------------------------------------------------
def verifyType(obj, class_or_type_or_tuple, _msg=""):
  """ Compare type and object are of the same class. If not true print and throw. """
  if not isinstance(obj, class_or_type_or_tuple):
    text = "{} type mismatch: {} is not {}. real type: {}".format(stackFunctionName(2), 
                                                                  toString(obj), 
                                                                  str(class_or_type_or_tuple), 
                                                                  type(obj))
    logNotSet(text, title="utils.verifyType")
    #raise AssertionError(text)

# --------------------------------------------------------------------------------------------------------------------
def toString(value, defaultIfError=""):
  """ Attempt to convert string. returns defaultIfError if null. """
  verify(isinstance(defaultIfError, str), "type mismatch: defaultIfError") 
  v = defaultIfError
  try:
    v = str(value)
  except ValueError:
    pass

  return v

# --------------------------------------------------------------------------------------------------------------------
def sanitizeString(value, defaultIfError=UNDECODABLE_ERROR_MESSAGE):
  """ Attempt to convert string. returns defaultIfNull if null. """
  verify(isinstance(value, basestring), "type mismatch: sanitizeString")
  ret = defaultIfError
  for t in ("utf-8", "latin1", "ascii"):
    try:
      ret = str(value.decode(t, "replace"))
      break
    except UnicodeEncodeError:
      pass
  return ret

# --------------------------------------------------------------------------------------------------------------------
def printTiming(func):
  def wrapper(*arg):
    t1 = time.time()
    res = func(*arg)
    t2 = time.time()
    logDebug("{}({}) took {:.2} ms".format(func.func_name, ",".join([str(a) for a in arg]), (t2-t1) * 1000.0))
    return res
  return wrapper

# --------------------------------------------------------------------------------------------------------------------
def stringToBytes(text):
  vals = ["B", "KB", "MB", "GB"]
  m = re.match(r"^(\d+)\s+({})$".format("|".join(vals)), text, re.IGNORECASE)
  return int(m.group(1)) * pow(1024, vals.index(m.group(2).upper())) if m else 0

# --------------------------------------------------------------------------------------------------------------------
def bytesToString(bytes_):
  bytes_ = bytes_ if bytes_ > 0 else MIN_VIDEO_SIZE_BYTES
  denoms = ["B", "KB", "MB", "GB"]

  i, denom = None, None
  for i, denom in enumerate(denoms):
    if bytes_ < pow(1024, i + 1):
      break
  return "{:.1f} {}".format(bytes_ / pow(1024, i), denom)