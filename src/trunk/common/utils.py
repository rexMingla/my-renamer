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
import re
import time

UNDECODABLE_ERROR_MESSAGE = "<could not decode>"
MIN_VIDEO_SIZE_BYTES = 20 * 1024 * 1024 # 20 MB

# --------------------------------------------------------------------------------------------------------------------
def stackFunctionName(index = 2): #1 is calling, 2 parent etc.
  """ Print the function name. Useful in debugging """
  ret = "??"
  try:
    ret = inspect.stack()[index][3]
  except IndexError:
    pass
  return ret

# --------------------------------------------------------------------------------------------------------------------
def initLogging(logfile):
  logging.basicConfig(level=logging.DEBUG,
                      format="%(asctime)s %(title)-12s %(name)-12s %(levelname)-8s %(message)s",
                      datefmt="%Y-%m-%d %H:%M",
                      filename=logfile,
                      filemode="a")

  for log in ("PyQt4", "requests", "tvdb_api"):
    logging.getLogger(log).setLevel(logging.CRITICAL)

  console = logging.StreamHandler()
  console.setFormatter(logging.Formatter("%(name)-12s %(levelname)-8s %(message)s"))
  console.setLevel(logging.INFO)
  logging.getLogger("renamer").addHandler(console)

def logNotSet(msg, longMsg="", title=""):
  log(logging.NOTSET, msg, longMsg, title)
  
def logDebug(msg, longMsg="", title=""):
  log(logging.DEBUG, msg, longMsg, title)
  
def logInfo(msg, longMsg="", title=""):
  log(logging.INFO, msg, longMsg, title)

def logWarning(msg, longMsg="", title=""):
  log(logging.WARNING, msg, longMsg, title)
  
def logError(msg, longMsg="", title=""):
  log(logging.ERROR, msg, longMsg, title)
  
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
def verifyType(obj, class_or_type_or_tuple, msg=""):
  """ Compare type and object are of the same class. If not true print and throw. """
  if not isinstance(obj, class_or_type_or_tuple):
    text = "{} type mismatch: {} is not {}. real type: {}".format(stackFunctionName(2), 
                                                                  toString(obj), 
                                                                  str(class_or_type_or_tuple), 
                                                                  type(obj))
    logNotSet(text, title="utils.verifyType")
    #raise AssertionError(text)

# --------------------------------------------------------------------------------------------------------------------
def listCompare(left, right):
  """ 
  Compare two lists (both assumed to already be sorted). 
  Returns False if the lists are different sizes or their contents do not match up and True othewise. """
  verifyType(left, list)
  verifyType(right, list)
  isSame = len(left) == len(right) and all(l == r for l, r in zip(left, right))
  return isSame
  
# --------------------------------------------------------------------------------------------------------------------
def dictCompare(left, right):
  """ Compare two dictionaries. 
  Returns False if the dictionaries are different sizes or their contents do not match up and True othewise. """
  verifyType(left, dict)
  verifyType(right, dict)
  isSame = len(left) == len(right) and all(l in right and left[l] == right[l] for l in left)
  return isSame 

# --------------------------------------------------------------------------------------------------------------------
def toString(value, defaultIfError=""):
  """ Attempt to convert string. returns defaultIfError if null. """
  verify(isinstance(defaultIfError, str), "type mismatch: defaultIfError") #will go recursive if we use verifyType() here
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
      logNotSet("{}({}) took {:.2} ms".format(func.func_name, ",".join(map(str, arg)), (t2-t1) * 1000.0))
      return res
  return wrapper

# --------------------------------------------------------------------------------------------------------------------
def stringToBytes(text):
  m = re.match(r"^(\d+)\s+(B|KB|MB|GB)$", text, re.IGNORECASE)
  return int(m.group(1)) * pow(1024, ["B", "KB", "MB", "GB"].index(m.group(2).upper())) if m else 0

# --------------------------------------------------------------------------------------------------------------------
def bytesToString(bytes_):
  bytes_ = bytes_ if bytes_ > 0 else MIN_VIDEO_SIZE_BYTES
  denoms = ["B", "KB", "MB", "GB"]
  for i, denom in enumerate(denoms):
    if bytes_ < pow(1024, i + 1):
      break
  return "{:.1f} {}".format(bytes_ / pow(1024, i), denom)
