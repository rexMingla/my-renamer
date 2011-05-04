#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
import sys 
import os
sys.path.insert(0, os.path.abspath(__file__+"/../../"))
import unittest

from common import errors, serializer

# --------------------------------------------------------------------------------------------------------------------
class DataItemTest(unittest.TestCase):
  def setUp(self):
    self.item_ = serializer.DataItem("10")
  
  def test_getData(self):
    self.assertEqual(self.item_.data_, "10")

  def test_setData(self):
    self.item_.data_ = 20
    self.assertEqual(self.item_.data_, 20)

  def test_restore(self):
    self.item_.data_ = self.item_.defaultValue_
    self.assertEqual(self.item_.data_, "10")
    
# --------------------------------------------------------------------------------------------------------------------
class _DummyClass():
  pass
    
# --------------------------------------------------------------------------------------------------------------------
class SerializerTest(unittest.TestCase):
  def setUp(self):
    file = "test.txt"
    self.serializer_ = serializer.Serializer(file)
    self.item_ = serializer.DataItem(20)
    self.serializer_.addItem("key", self.item_)
    if os.path.exists(file):
      os.remove(file)
    
  def test_cleanSettings(self):
    self.serializer_.saveItems()
    self.item_.data_ = 30
    self.serializer_.loadItems()
    self.assertEqual(self.item_.data_, 20)
    
  def test_restoreFactorySettings(self):
    self.item_.data_ = 30
    self.serializer_.restoreFactorySettings()
    self.assertEqual(self.item_.data_, 20)
  
  def test_modifiedSettings(self):
    self.item_.data_ = 30
    self.serializer_.saveItems()
    self.item_.data_ = 10
    self.serializer_.loadItems()
    self.assertEqual(self.item_.data_, 30)

  def test_loadDictionary(self):
    data = {"test":"this"}
    self.item_.data_ = data
    self.serializer_.saveItems()
    self.item_.data_ = 10
    self.serializer_.loadItems()
    self.assertEqual(self.item_.data_, data)

  def test_loadMap(self):
    data = ["test","this"]
    self.item_.data_ = data
    self.serializer_.saveItems()
    self.item_.data_ = 10
    self.serializer_.loadItems()
    self.assertEqual(self.item_.data_, data)
 
  def tests_loadComplex(self):
    data = _DummyClass()
    #todo: fix this!
    self.assertRaises(errors.SerializationError, serializer.DataItem.setData, self.item_, data)
  
  def t():
    self.serializer_.saveItems()
    self.item_.data_ = 10
    self.serializer_.loadItems()
    self.assertEqual(self.item_.data_, data)

# --------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  unittest.main()