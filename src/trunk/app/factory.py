#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Abstract factory based on item type
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

from common import interfaces
from common import moveItemActioner
from common import outputFormat

from tv import tvManager
from tv import tvInfoClient

from movie import movieManager
from movie import movieInfoClient

import editSourcesWidget
import inputWidget
import outputWidget
import renamerModule
import workBenchWidget

# --------------------------------------------------------------------------------------------------------------------
class Factory:
  @staticmethod
  def getRenamerModule(mode, parent=None):
    if mode == interfaces.Mode.MOVIE_MODE:
      return renamerModule.MovieRenamerModule(parent) 
    else:
      return renamerModule.TvRenamerModule(parent)
  
  @staticmethod
  def getEditSourceWidget(mode, parent=None):
    store = Factory.getStore(mode)
    return editSourcesWidget.EditSourcesWidget(store, parent)
  
  @staticmethod
  def getInputWidget(mode, parent=None):
    store = Factory.getStore(mode)
    return inputWidget.InputWidget(mode, store, parent)
    
  @staticmethod
  def getOutputWidget(mode, parent=None):
    fmt = Factory.getOutputFormat(mode)    
    return outputWidget.OutputWidget(mode, fmt, parent)
    
  @staticmethod
  def getWorkBenchWidget(mode, parent=None):
    manager = Factory.getManager(mode)
    if mode == interfaces.Mode.MOVIE_MODE:
      return workBenchWidget.MovieWorkBenchWidget(manager, parent) 
    else:
      return workBenchWidget.TvWorkBenchWidget(manager, parent)
    
  @staticmethod
  def getRenameItemGenerator(mode):
    if mode == interfaces.Mode.MOVIE_MODE:
      return moveItemActioner.MovieRenameItemGenerator() 
    else:
      return moveItemActioner.TvRenameItemGenerator()
  
  @staticmethod
  def getStore(mode):
    if mode == interfaces.Mode.MOVIE_MODE:
      return movieInfoClient.getStore()
    else:
      return tvInfoClient.getStore()
    
  @staticmethod
  def getManager(mode):
    if mode == interfaces.Mode.MOVIE_MODE:
      return movieManager.getManager()
    else:
      return tvManager.getManager()
    
  @staticmethod
  def getOutputFormat(mode):
    if mode == interfaces.Mode.MOVIE_MODE:
      return outputFormat.MovieInputMap
    else:
      return outputFormat.TvInputMap
    
    
