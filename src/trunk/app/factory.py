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
from common import formatting

from tv import client as tv_client
from tv import manager as tv_manager
from tv import types as tv_types

from movie import client as movie_client
from movie import manager as movie_manager
from movie import types as movie_types

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
      return outputWidget.NameFormatHelper(formatting.MovieNameFormatter(),
                                           movie_types.MovieInfo("Title", "Year", 
                                                                     "Genre", "Part", "Series"),
                                           movie_types.MovieInfo("The Twin Towers", 2002, "action", 1, "LOTR"))
    else:  
      return outputWidget.NameFormatHelper(formatting.TvNameFormatter(),
                                           tv_types.AdvancedEpisodeInfo("Show Name", "Series Number", 
                                                                      "Episode Number", "Episode Name"),
                                           tv_types.AdvancedEpisodeInfo("Seinfeld", 9, 3, "The Serenity Now"))
    
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
      return renamer.RenameItemGenerator(formatting.MovieNameFormatter())
    else:  
      return renamer.RenameItemGenerator(formatting.TvNameFormatter())
    
  @staticmethod
  def getStoreHolder(mode):
    if mode == interfaces.Mode.MOVIE_MODE:
      return movie_client.getStoreHolder()
    else:
      return tv_client.getStoreHolder()
    
  @staticmethod
  def getManager(mode):
    if mode == interfaces.Mode.MOVIE_MODE:
      return movie_manager.getManager()
    else:
      return tv_manager.getManager()
    
  @staticmethod
  def getOutputFormat(mode):
    if mode == interfaces.Mode.MOVIE_MODE:
      return formatting.MovieInputMap
    else:
      return formatting.TvInputValues
    
    
