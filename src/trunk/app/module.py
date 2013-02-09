#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Base module responsible for the renaming of movies and tv series
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore

from common import interfaces
from common import thread

from app import factory

# --------------------------------------------------------------------------------------------------------------------
class RenameThread(thread.AdvancedWorkerThread):
  def __init__(self, name, renamer, items):
    super(RenameThread, self).__init__(name)
    self._renamer = renamer
    self._items = items

  def _getAllItems(self):
    return [self._renamer.getRenameItem(item) for item in self._items]

  def _applyToItem(self, item):
    ret = item.performAction(self._onPercentageComplete)
    return thread.WorkItem(item, item.resultStr(ret), item.resultToLogItem(ret))

  def _onPercentageComplete(self, percentage):
    overall = int((percentage + 100.0 * self._i) / self._numItems)
    self._onProgress(overall)
    return not self._user_stopped

# --------------------------------------------------------------------------------------------------------------------
class SearchThread(thread.AdvancedWorkerThread):
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
    super(TvSearchThread, self).__init__(interfaces.TV_MODE, manager, config)

  def _getAllItems(self):
    return self._manager.getFolders(self._config.folder, self._config.recursive)

  def _applyToItem(self, item):
    season = self._manager.getSeasonForFolder(item, self._config.getExtensions(), self._config.getMinFileSizeBytes())
    ret = None
    if season:
      ret = thread.WorkItem(season, season.resultStr(season.status))
    return ret

# --------------------------------------------------------------------------------------------------------------------
class MovieSearchThread(SearchThread):
  """ class that performs a search for movie files """
  def __init__(self, manager, config):
    super(MovieSearchThread, self).__init__(interfaces.MOVIE_MODE, manager, config)

  def _getAllItems(self):
    return self._manager.helper.getFiles(self._config.folder,
                                         self._config.getExtensions(),
                                         self._config.recursive,
                                         self._config.getMinFileSizeBytes())

  def _applyToItem(self, item):
    item = self._manager.processFile(item)
    ret = None
    if item:
      ret = thread.WorkItem(item, "File exists" if item.fileExists() else "File not found")
    return ret

def getSearchThread(mode, manager, config):
  if mode == interfaces.MOVIE_MODE:
    return MovieSearchThread(manager, config)
  else:
    return TvSearchThread(manager, config)

# --------------------------------------------------------------------------------------------------------------------
class RenamerModule(QtCore.QObject):
  """ Class responsible for the input, output and workbench components and manages their interactions. """
  log_signal = QtCore.pyqtSignal(object)

  def __init__(self, mode, parent=None):
    super(RenamerModule, self).__init__(parent)

    self.mode = mode
    self.edit_sources_widget = factory.Factory.getEditSourceWidget(mode, parent)
    self.edit_sources_widget.setVisible(False)
    self.input_widget = factory.Factory.getInputWidget(mode, parent)
    self.output_widget = factory.Factory.getOutputWidget(mode, parent)
    self.work_bench = factory.Factory.getWorkBenchWidget(mode, parent)
    self._manager = factory.Factory.getManager(mode)
    self._renamer = factory.Factory.getRenameItemGenerator(mode)
    self._widgets = (self.input_widget, self.output_widget, self.work_bench)

    self.work_bench.workbench_changed_signal.connect(self.output_widget.rename_button.setEnabled)
    self.output_widget.rename_signal.connect(self._rename)
    self.output_widget.stop_signal.connect(self._stopRename)
    self.work_bench.renameItemChangedSignal.connect(self.output_widget.onRenameItemChanged)
    self.work_bench.show_edit_sources_signal.connect(self.edit_sources_widget.show)
    self.input_widget.show_edit_sources_signal.connect(self.edit_sources_widget.show)
    self.edit_sources_widget.accepted.connect(self.input_widget.onSourcesWidgetFinished)

    self.input_widget.explore_signal.connect(self._explore)
    self.input_widget.stop_signal.connect(self._stopSearch)

    self._worker_thread = None
    self._is_shutting_down = False

  def __del__(self):
    self._is_shutting_down = True
    self._stopThread()

  def _explore(self):
    if self._worker_thread and self._worker_thread.isRunning():
      return

    for widget in self._widgets:
      widget.startExploring()

    self._worker_thread = getSearchThread(self.mode, self._manager, self.input_widget.getConfig())
    self._worker_thread.progress_signal.connect(self.input_widget.progress_widget.setProgress)
    self._worker_thread.new_data_signal.connect(self.work_bench.addItem)
    self._worker_thread.log_signal.connect(self.log_signal)
    self._worker_thread.finished.connect(self._onThreadFinished)
    self._worker_thread.terminated.connect(self._onThreadFinished)
    self._worker_thread.start()

  def _rename(self):
    if self._worker_thread and self._worker_thread.isRunning():
      return

    for widget in self._widgets:
      widget.startActioning()

    self._renamer.config = self.output_widget.getConfig()
    self._worker_thread = RenameThread("rename {}".format(self.mode), self._renamer,
        self.work_bench.actionable_items())
    self._worker_thread.progress_signal.connect(self.output_widget.progress_bar.setValue)
    self._worker_thread.log_signal.connect(self.log_signal)
    self._worker_thread.finished.connect(self._onThreadFinished)
    self._worker_thread.terminated.connect(self._onThreadFinished)
    self._worker_thread.start()

  def setActive(self):
    pass

  def setInactive(self):
    self._stopThread() #TODO: maybe prompt? In future, run in background.

  def _stopThread(self):
    if self._worker_thread:
      self._worker_thread.join()

  def _onThreadFinished(self):
    if not self._is_shutting_down:
      for widget in self._widgets:
        widget.stopExploring()
        widget.stopActioning()

  def _stopRename(self):
    self.output_widget.stop_button.setEnabled(False)
    self._stopThread()

  def _stopSearch(self):
    self.input_widget.progress_widget.stop()
    self._stopThread()
