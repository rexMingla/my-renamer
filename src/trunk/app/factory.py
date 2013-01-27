#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Abstract factory based on item type
# --------------------------------------------------------------------------------------------------------------------
from common import interfaces
from common import renamer
from common import formatting

from media.base import widget as base_widget

from media.tv import client as tv_client
from media.tv import manager as tv_manager
from media.tv import types as tv_types
from media.tv import widget as tv_widget

from media.movie import client as movie_client
from media.movie import manager as movie_manager
from media.movie import types as movie_types
from media.movie import widget as movie_widget

# --------------------------------------------------------------------------------------------------------------------
class Factory:
  """ creates components for the application based on mode value """  
    
  @staticmethod
  def get_edit_source_widget(mode, parent=None):
    store = Factory.get_store_helper(mode)
    return base_widget.EditSourcesWidget(mode, store, parent)
  
  @staticmethod
  def get_input_widget(mode, parent=None):
    store = Factory.get_store_helper(mode)
    return base_widget.InputWidget(mode, store, parent)
    
  @staticmethod
  def get_output_widget(mode, parent=None):
    helper = Factory.get_name_format_helper(mode)    
    return base_widget.OutputWidget(mode, helper, parent)
    
  @staticmethod
  def get_name_format_helper(mode):
    if mode == interfaces.MOVIE_MODE:
      return base_widget.NameFormatHelper(formatting.MovieNameFormatter(),
                                           movie_types.MovieInfo("Title", "Year", 
                                                                     "Genre", "Part", "Series"),
                                           movie_types.MovieInfo("The Twin Towers", 2002, "action", 1, "LOTR"))
    else:  
      return base_widget.NameFormatHelper(formatting.TvNameFormatter(),
                                           tv_types.AdvancedEpisodeInfo("Show Name", "Series Number", 
                                                                      "Episode Number", "Episode Name"),
                                           tv_types.AdvancedEpisodeInfo("Seinfeld", 9, 3, "The Serenity Now"))
    
  @staticmethod
  def get_work_bench_widget(mode, parent=None):
    manager = Factory.get_manager(mode)
    if mode == interfaces.MOVIE_MODE:
      return movie_widget.MovieWorkBenchWidget(manager, parent) 
    else:
      return tv_widget.TvWorkBenchWidget(manager, parent)
    
  @staticmethod
  def get_rename_item_generator(mode):
    if mode == interfaces.MOVIE_MODE:
      return renamer.RenameItemGenerator(formatting.MovieNameFormatter())
    else:  
      return renamer.RenameItemGenerator(formatting.TvNameFormatter())
    
  @staticmethod
  def get_store_helper(mode):
    if mode == interfaces.MOVIE_MODE:
      return movie_client.get_store_helper()
    else:
      return tv_client.get_store_helper()
    
  @staticmethod
  def get_manager(mode):
    if mode == interfaces.MOVIE_MODE:
      return movie_manager.get_manager()
    else:
      return tv_manager.get_manager()
    
