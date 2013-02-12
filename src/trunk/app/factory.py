#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Retrieves objects based on mode type
# --------------------------------------------------------------------------------------------------------------------
from common import renamer
from common import formatting

from media.base import widget as base_widget
from media.base import types as base_types

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
  def getEditInfoClientsWidget(mode, parent=None):
    store = Factory.getInfoClientHolder(mode)
    return base_widget.EditInfoClientsWidget(mode, store, parent)

  @staticmethod
  def getInputWidget(mode, parent=None):
    store = Factory.getInfoClientHolder(mode)
    return base_widget.InputWidget(mode, store, parent)

  @staticmethod
  def getOutputWidget(mode, parent=None):
    helper = Factory.getNameFormatHelper(mode)
    return base_widget.OutputWidget(mode, helper, parent)

  @staticmethod
  def getNameFormatHelper(mode):
    if mode == base_types.MOVIE_MODE:
      return base_widget.NameFormatHelper(formatting.MovieNameFormatter(),
          movie_types.MovieInfo("Title", "Year", ["Genre"], "Part", "Series"),
          movie_types.MovieInfo("The Twin Towers", 2002, ["action"], 1, "LOTR"))
    else:
      return base_widget.NameFormatHelper(formatting.TvNameFormatter(),
          tv_types.AdvancedEpisodeInfo("Show Name", "Series Number", "Episode Number", "Episode Name"),
          tv_types.AdvancedEpisodeInfo("Seinfeld", 9, 3, "The Serenity Now"))

  @staticmethod
  def getWorkBenchWidget(mode, parent=None):
    manager = Factory.getManager(mode)
    if mode == base_types.MOVIE_MODE:
      return movie_widget.MovieWorkBenchWidget(manager, parent)
    else:
      return tv_widget.TvWorkBenchWidget(manager, parent)

  @staticmethod
  def getRenameItemGenerator(mode):
    if mode == base_types.MOVIE_MODE:
      return renamer.RenameItemGenerator(formatting.MovieNameFormatter())
    else:
      return renamer.RenameItemGenerator(formatting.TvNameFormatter())

  @staticmethod
  def getInfoClientHolder(mode):
    if mode == base_types.MOVIE_MODE:
      return movie_client.getInfoClientHolder()
    else:
      return tv_client.getInfoClientHolder()

  @staticmethod
  def getManager(mode):
    if mode == base_types.MOVIE_MODE:
      return movie_manager.getManager()
    else:
      return tv_manager.getManager()

  @staticmethod
  def getEditInfoWidget(mode, parent=None):
    if mode == base_types.MOVIE_MODE:
      return movie_widget.EditMovieInfoWidget(parent)
    else:
      return tv_widget.EditSeasonInfoWidget(parent)

  @staticmethod
  def getSearchParamsWidget(mode, parent=None):
    if mode == base_types.MOVIE_MODE:
      return movie_widget.SearchMovieParamsWidget(parent)
    else:
      return tv_widget.SearchSeasonParamsWidget(parent)

  @staticmethod
  def getSearchWidget(mode, parent=None):
    if mode == base_types.MOVIE_MODE:
      return movie_widget.EditMovieItemWidget(Factory.getInfoClientHolder(mode), parent)
    else:
      return tv_widget.EditSeasonItemWidget(Factory.getInfoClientHolder(mode), parent)
