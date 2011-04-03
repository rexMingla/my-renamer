#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import pickle
import sys
import pickle
import cStringIO
import os

from PyQt4 import QtCore

import errors
import utils

# --------------------------------------------------------------------------------------------------------------------
class DataItem(QtCore.QObject):
  """ Interface of loading and saving objects """
  onChangedSignal_ = QtCore.pyqtSignal()

  def __init__(self, defaultValue, parent = None):
    super(QtCore.QObject, self).__init__(parent)
    self._data_ = defaultValue
    self._defaultValue_ = defaultValue
      
  def getData(self):
    return self._data_
    
  def setData(self, obj):
    s = cStringIO.StringIO()
    p = pickle.Pickler(s)
    try:
      p.save(obj)
    except pickle.PickleError:
      raise errors.SerializationError(utils.toString(obj))           
    if not obj == self.getData():
      self._data_ = obj
      self.onChangedSignal_.emit()
      
  def getDefaultValue(self):
    return self._defaultValue_
  
  data_ = property(getData, setData)
  defaultValue_ = property(getDefaultValue)    


# --------------------------------------------------------------------------------------------------------------------
class Serializer:
  
  def __init__(self, output):
    utils.verifyType(output, str, "Serializer.__init__ output type")
    self.items_ = {}
    self.out_ = output
    
  def addItem(self, key, item):
    utils.verifyType(key, str, "Serializer.addItem key type")
    utils.verifyType(item, DataItem, "Serializer.addItem key item type")
    utils.verify(not self.items_.has_key(key), "Serializer.addItem: key is new")
    self.items_[key] = item
    
  def saveItems(self):
    data = {}    
    for key in self.items_.keys():
      item = self.items_[key]
      data[key] = item.data_
    pickle.dump(data, open(self.out_, "wb"))
    
  def loadItems(self):
    if os.path.exists(self.out_):
      data = pickle.load(open(self.out_))
      if data:
        if isinstance(data, dict):
          for key in data.keys():
            if self.items_.has_key(key):
              self.items_[key].data_ = data[key]
            else:
              utils.out("Serializer.loadItems key: %s not found. data ignored" % key)
        else:
          utils.out("Serializer.loadItems data is not dictionary. data ignored")
    else:
      utils.out("Serializer.loadItems %s file does not exist." % self.out_)
    
  def restoreFactorySettings(self):
    for key in self.items_.keys():
      item = self.items_[key]
      item.data_ = item.defaultValue_
      
    