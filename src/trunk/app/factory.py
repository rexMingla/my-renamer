#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Abstract factory based on item type
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

from common import interfaces
from common import renamer
from common import outputFormat

from tv import tvInfoClient
from tv import tvManager
from tv import tvTypes

from movie import movieInfoClient
from movie import movieManager
from movie import movieTypes

import editSourcesWidget
import inputWidget
import movieWorkBenchWidget
import outputWidget
import renamerModule
import tvWorkBenchWidget

# --------------------------------------------------------------------------------------------------------------------
class Factory:
  """ creates components for the application based on mode value """
  
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
    helper = Factory.getNameFormatHelper(mode)    
    return outputWidget.OutputWidget(mode, helper, parent)
    
  @staticmethod
  def getNameFormatHelper(mode, parent=None):
    if mode == interfaces.Mode.MOVIE_MODE:
      return outputWidget.NameFormatHelper(outputFormat.MovieNameFormatter(),
                                           movieTypes.MovieInfo("Title", "Year", 
                                                                     "Genre", "Part", "Series"),
                                           movieTypes.MovieInfo("The Twin Towers", 2002, "action", 1, "LOTR"))
    else:  
      return outputWidget.NameFormatHelper(outputFormat.TvNameFormatter(),
                                           tvTypes.AdvancedEpisodeInfo("Show Name", "Series Number", 
                                                                      "Episode Number", "Episode Name"),
                                           tvTypes.AdvancedEpisodeInfo("Seinfeld", 9, 3, "The Serenity Now"))
    
  @staticmethod
  def getWorkBenchWidget(mode, parent=None):
    manager = Factory.getManager(mode)
    if mode == interfaces.Mode.MOVIE_MODE:
      return movieWorkBenchWidget.MovieWorkBenchWidget(manager, parent) 
    else:
      return tvWorkBenchWidget.TvWorkBenchWidget(manager, parent)
    
  @staticmethod
  def getRenameItemGenerator(mode):
    if mode == interfaces.Mode.MOVIE_MODE:
      return renamer.RenameItemGenerator(outputFormat.MovieNameFormatter())
    else:  
      return renamer.RenameItemGenerator(outputFormat.TvNameFormatter())
    
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
      return outputFormat.TvInputValues
    
    
