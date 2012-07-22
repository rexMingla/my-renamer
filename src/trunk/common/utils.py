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
import time

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
def initLogging(logfile):
  logging.basicConfig(level=logging.DEBUG,
                      format="%(asctime)s %(title)s %(name)-12s %(levelname)-8s %(message)s",
                      datefmt="%Y-%m-%d %H:%M",
                      filename=logfile,
                      filemode="a")

  for log in ("PyQt4", "requests"):
    logging.getLogger(log).setLevel(logging.CRITICAL)

  console = logging.StreamHandler()
  console.setFormatter(logging.Formatter("%(name)-12s %(levelname)-8s %(message)s"))
  console.setLevel(logging.INFO)
  logging.getLogger("app").addHandler(console)
  
def logDebug(msg, longMsg="", title=""):
  log(logging.DEBUG, msg, longMsg, title)
  
def logInfo(msg, longMsg="", title=""):
  log(logging.INFO, msg, longMsg, title)

def logWarning(msg, longMsg="", title=""):
  log(logging.WARNING, msg, longMsg, title)
  
def logError(msg, longMsg="", title=""):
  log(logging.ERROR, msg, longMsg, title)
  
def log(level, msg, longMsg="", title=""):
  logging.getLogger("app").log(level, msg or longMsg, extra={"title":title})  

# --------------------------------------------------------------------------------------------------------------------
def verify(test, message):
  """ If test is not true print and throw. """
  if not test:
    text = "assertion failed: {} stack: {}".format(message, stackFunctionName(2))
    logDebug("utils.verify", text)
    raise errors.AssertionError(text)      
      
# --------------------------------------------------------------------------------------------------------------------
def verifyType(obj, class_or_type_or_tuple, msg=""):
  """ Compare type and object are of the same class. If not true print and throw. """
  if not isinstance(obj, class_or_type_or_tuple):
    text = "{} type mismatch: {} is not {}. real type: {}".format(stackFunctionName(2), 
                                                                  toString(obj), 
                                                                  str(class_or_type_or_tuple), 
                                                                  type(obj))
    logDebug("utils.verifyType", text)
    #raise errors.AssertionError(text)

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
def printTiming(func):
  def wrapper(*arg):
      t1 = time.time()
      res = func(*arg)
      t2 = time.time()
      logDebug(func.func_name, "{}({}) took {:.2} ms".format(",".join(map(str, arg)), (t2-t1) * 1000.0))
      return res
  return wrapper


