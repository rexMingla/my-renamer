#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: module contains all the widgets required for a particular mode
# --------------------------------------------------------------------------------------------------------------------
from threading import Lock
from PyQt4 import QtCore
from functools import partial

from common import file_helper
from common import thread
from media.base import types as base_types
from app import factory

# --------------------------------------------------------------------------------------------------------------------
class SearchThread(thread.AdvancedWorkerThread):
  """ Thread responsible for finding renamable items 
  
  Args:
    mode: used for logging etc.
    manager: media.base.manager.BaseManager object that uses the config to apply the search
    config: common.config.InputConfig object
  """
  def __init__(self, mode, manager, config):
    super(SearchThread, self).__init__("search {}".format(mode))
    self._manager = manager
    self._config = config

  def _getAllItems(self):
    raise NotImplementedError("SearchThread._getAllItems not implemented")

  def _applyToItem(self, item):
    raise NotImplementedError("SearchThread._applyToItem not implemented")

# --------------------------------------------------------------------------------------------------------------------
class TvSearchThread(SearchThread):
  """ class that performs a search for tv folders and their episode files """
  def __init__(self, manager, config):
    super(TvSearchThread, self).__init__(base_types.TV_MODE, manager, config)

  def _getAllItems(self):
    return file_helper.FileHelper.getFolders(self._config.folder, self._config.recursive)

  def _applyToItem(self, item):
    season = self._manager.getSeasonForFolder(item, self._config.getExtensions(), self._config.getMinFileSizeBytes())
    ret = None
    if season:
      ret = thread.WorkItem(season, season.getStatus())
    return ret

# --------------------------------------------------------------------------------------------------------------------
class MovieSearchThread(SearchThread):
  """ class that performs a search for movie files """
  def __init__(self, manager, config):
    super(MovieSearchThread, self).__init__(base_types.MOVIE_MODE, manager, config)

  def _getAllItems(self):
    return self._manager.helper.getFiles(self._config.folder,
                                         self._config.getExtensions(),
                                         self._config.recursive,
                                         self._config.getMinFileSizeBytes())

  def _applyToItem(self, item):
    item = self._manager.processFile(item)
    ret = None
    if item:
      ret = thread.WorkItem(item, item.getStatus())
    return ret

def getSearchThread(mode, manager, config):
  if mode == base_types.MOVIE_MODE:
    return MovieSearchThread(manager, config)
  else:
    return TvSearchThread(manager, config)

# --------------------------------------------------------------------------------------------------------------------
class RenamerModule(QtCore.QObject):
  """ Class responsible for the input, output and workbench components and manages their interactions. """
  new_rename_items_signal = QtCore.pyqtSignal(object) #sends a list of rename items

  def __init__(self, mode, parent=None):
    super(RenamerModule, self).__init__(parent)

    self.mode = mode
    self.edit_sources_widget = factory.Factory.getEditInfoClientsWidget(mode, parent)
    self.edit_sources_widget.setVisible(False)
    self.input_widget = factory.Factory.getInputWidget(mode, parent)
    self.output_widget = factory.Factory.getOutputWidget(mode, parent)
    self.work_bench = factory.Factory.getWorkBenchWidget(mode, parent)
    self._manager = factory.Factory.getManager(mode)
    self._renamer = factory.Factory.getRenameItemGenerator(mode)
    self._widgets = (self.input_widget, self.output_widget, self.work_bench)

    self.work_bench.workbench_changed_signal.connect(self.output_widget.rename_button.setEnabled)
    self.output_widget.rename_signal.connect(self._rename)
    self.work_bench.renameItemChangedSignal.connect(self.output_widget.onRenameItemChanged)
    self.work_bench.show_edit_info_clients_signal.connect(self.edit_sources_widget.show)
    self.input_widget.show_edit_info_clients_signal.connect(self.edit_sources_widget.show)
    self.edit_sources_widget.accepted.connect(self.input_widget.onSourcesWidgetFinished)

    self.input_widget.explore_signal.connect(self._explore)
    self.input_widget.stop_signal.connect(self._stopSearch)

    self._search_thread = None
    self._is_shutting_down = False

  def __del__(self):
    self._is_shutting_down = True
    self._stopRename()
    self._stopSearch()

  def _explore(self):
    if self._search_thread and self._search_thread.isRunning():
      return

    for widget in self._widgets:
      widget.startExploring()

    self._search_thread = getSearchThread(self.mode, self._manager, self.input_widget.getConfig())
    self._search_thread.progress_signal.connect(self.input_widget.progress_widget.setProgress)
    self._search_thread.new_data_signal.connect(self.work_bench.addItem)
    #self._search_thread.log_signal.connect(self.log_signal)
    self._search_thread.finished.connect(self._onSearchThreadFinished)
    self._search_thread.terminated.connect(self._onSearchThreadFinished)
    self._search_thread.start()

  def _rename(self):
    self._renamer.config = self.output_widget.getConfig()
    items = [self._renamer.getRenameItem(i) for i in self.work_bench.actionableItems()]
    self.new_rename_items_signal.emit(items)

  def setActive(self):
    pass

  def setInactive(self):
    self._stopSearchThread() #TODO: maybe prompt? In future, run in background.

  def _stopSearchThread(self):
    if self._search_thread:
      self._search_thread.join()

  def _onSearchThreadFinished(self):
    if not self._is_shutting_down:
      for widget in self._widgets:
        widget.stopExploring()

  def _stopSearch(self):
    self.input_widget.progress_widget.stop()
    self._stopSearchThread()

  