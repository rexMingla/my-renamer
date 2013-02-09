#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Website:             http://code.google.com/p/my-renamer/
# Purpose of document: All the generic functions that don't have a more appropriate home
# --------------------------------------------------------------------------------------------------------------------
import logging
import logging.handlers
import inspect
import re
import time

UNDECODABLE_ERROR_MESSAGE = "<could not decode>"
MIN_VIDEO_SIZE_BYTES = 20 * 1024 * 1024 # 20 MB
MAX_LOG_SIZE_BYTES = 1024 * 1024 # 1 MB
LOG_NAME = "renamer"

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
  def __init__(self, log_level, action, short_message, long_message=""):
    #utils.verifyType(log_level, int)
    #utils.verifyType(action, str)
    #utils.verifyType(short_message, str)
    #utils.verifyType(long_message, str)
    self.log_level = log_level
    self.action = action
    self.short_message = short_message
    self.long_message = long_message or short_message

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
                      format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                      datefmt="%Y-%m-%d %H:%M")

  for log_name in ("PyQt4", "requests", "tvdb_api"):
    logging.getLogger(log_name).setLevel(logging.CRITICAL)

  handler = logging.handlers.RotatingFileHandler(logfile, "a", maxBytes=MAX_LOG_SIZE_BYTES, backupCount=5)

  console = logging.StreamHandler()
  console.setFormatter(logging.Formatter("%(name)-12s %(levelname)-8s %(message)s"))
  console.setLevel(logging.INFO)

  logging.getLogger(LOG_NAME).addHandler(console)
  logging.getLogger(LOG_NAME).addHandler(handler)

def logNotSet(msg, long_msg="", title=""):
  log(LogLevel.NOTSET, msg, long_msg, title)

def logDebug(msg, long_msg="", title=""):
  log(LogLevel.DEBUG, msg, long_msg, title)

def logInfo(msg, long_msg="", title=""):
  log(LogLevel.INFO, msg, long_msg, title)

def logWarning(msg, long_msg="", title=""):
  log(LogLevel.WARNING, msg, long_msg, title)

def logError(msg, long_msg="", title=""):
  log(LogLevel.ERROR, msg, long_msg, title)

def log(level, msg, long_msg="", title=""):
  logging.getLogger("renamer").log(level, msg or long_msg, extra={"title":title})

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
def toString(value, default_if_error=""):
  """ Attempt to convert string. returns default_if_error if null. """
  verify(isinstance(default_if_error, str), "type mismatch: default_if_error")
  ret = default_if_error
  try:
    ret = str(value)
  except ValueError:
    pass

  return ret

# --------------------------------------------------------------------------------------------------------------------
def sanitizeString(value, default_if_error=UNDECODABLE_ERROR_MESSAGE):
  """ Attempt to convert string. returns defaultIfNull if null. """
  verify(isinstance(value, basestring), "type mismatch: sanitizeString")
  ret = default_if_error
  for text_type in ("utf-8", "latin1", "ascii"):
    try:
      ret = str(value.decode(text_type, "replace"))
      break
    except UnicodeEncodeError:
      pass
  return ret

# --------------------------------------------------------------------------------------------------------------------
def printTiming(func):
  def wrapper(*arg):
    start = time.time()
    res = func(*arg)
    end = time.time()
    logDebug("{}({}) took {:.2} ms".format(func.func_name, ",".join([str(a) for a in arg]), (end - start) * 1000.0))
    return res
  return wrapper

# --------------------------------------------------------------------------------------------------------------------
def stringToBytes(text):
  vals = ["B", "KB", "MB", "GB"]
  match = re.match(r"^(\d+)\s+({})$".format("|".join(vals)), text, re.IGNORECASE)
  return int(match.group(1)) * pow(1024, vals.index(match.group(2).upper())) if match else 0

# --------------------------------------------------------------------------------------------------------------------
def bytesToString(bytes_):
  bytes_ = bytes_ if bytes_ > 0 else MIN_VIDEO_SIZE_BYTES
  denoms = ["B", "KB", "MB", "GB"]

  i, denom = None, None
  for i, denom in enumerate(denoms):
    if bytes_ < pow(1024, i + 1):
      break
  return "{:.1f} {}".format(bytes_ / pow(1024, i), denom)
