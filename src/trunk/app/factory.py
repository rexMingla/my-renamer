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
from tv import tvWorkBench

from movie import movieManager
from movie import movieInfoClient
from movie import movieWorkBench

import editSourcesWidget
import inputWidget
import outputWidget
import renamerModule

# --------------------------------------------------------------------------------------------------------------------
class Factory:
  @staticmethod
  def getRenamerModule(mode, parent=None):
    return renamerModule.RenamerModule(mode, parent) 
    
  @staticmethod
  def getEditSourceWidget(mode, parent=None):
    store = Factory.getStoreHolder(mode)
    return editSourcesWidget.EditSourcesWidget(mode, store, parent)
  
  @staticmethod
  def getInputWidget(mode, parent=None):
    store = Factory.getStoreHolder(mode)
    return inputWidget.InputWidget(mode, store, parent)
    
  @staticmethod
  def getOutputWidget(mode, parent=None):
    fmt = Factory.getOutputFormat(mode)    
    return outputWidget.OutputWidget(mode, fmt, parent)
    
  @staticmethod
  def getWorkBenchWidget(mode, parent=None):
    manager = Factory.getManager(mode)
    if mode == interfaces.Mode.MOVIE_MODE:
      return movieWorkBench.MovieWorkBenchWidget(manager, parent) 
    else:
      return tvWorkBench.TvWorkBenchWidget(manager, parent)
    
  @staticmethod
  def getRenameItemGenerator(mode):
    if mode == interfaces.Mode.MOVIE_MODE:
      return moveItemActioner.MovieRenameItemGenerator() 
    else:
      return moveItemActioner.TvRenameItemGenerator()
  
  @staticmethod
  def getStoreHolder(mode):
    if mode == interfaces.Mode.MOVIE_MODE:
      return movieInfoClient.getStoreHolder()
    else:
      return tvInfoClient.getStoreHolder()
    
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
    
    
