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
    
  def _get_all_items(self):
    return [self._renamer.get_rename_item(item) for item in self._items]
   
  def _apply_to_item(self, item):
    ret = item.perform_action(self._on_percentage_complete)
    return thread.WorkItem(item, item.result_str(ret), item.result_to_log_item(ret))
  
  def _on_percentage_complete(self, percentage):
    overall = int((percentage + 100.0 * self._i) / self._numItems)
    self._on_progress(overall)
    return not self._user_stopped
  
# --------------------------------------------------------------------------------------------------------------------
class SearchThread(thread.AdvancedWorkerThread):  
  def __init__(self, mode, manager, config):
    super(SearchThread, self).__init__("search {}".format(mode))
    self._manager = manager
    self._config = config

  def _get_all_items(self):
    raise NotImplementedError("SearchThread._get_all_items not implemented")
   
  def _apply_to_item(self, item):
    raise NotImplementedError("SearchThread._apply_to_item not implemented")

# --------------------------------------------------------------------------------------------------------------------
class TvSearchThread(SearchThread):
  """ class that performs a search for tv folders and their episode files """  
  def __init__(self, manager, config):
    super(TvSearchThread, self).__init__(interfaces.TV_MODE, manager, config)  
    
  def _get_all_items(self):
    return self._manager.get_folders(self._config.folder, self._config.recursive)
    
  def _apply_to_item(self, item):
    season = self._manager.get_season_for_folder(item, self._config.get_extensions(), self._config.get_min_file_size_bytes()) 
    ret = None
    if season:
      ret = thread.WorkItem(season, season.result_str(season.status))
    return ret
  
# --------------------------------------------------------------------------------------------------------------------
class MovieSearchThread(SearchThread):
  """ class that performs a search for movie files """  
  def __init__(self, manager, config):
    super(MovieSearchThread, self).__init__(interfaces.MOVIE_MODE, manager, config)
   
  def _get_all_items(self):
    return self._manager.helper.get_files(self._config.folder, 
                                         self._config.get_extensions(), 
                                         self._config.recursive, 
                                         self._config.get_min_file_size_bytes())
    
  def _apply_to_item(self, item):
    item = self._manager.process_file(item)
    ret = None
    if item:
      ret = thread.WorkItem(item, "File exists" if item.file_exists() else "File not found")
    return ret

def get_search_thread(mode, manager, config):
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
    self.edit_sources_widget = factory.Factory.get_edit_source_widget(mode, parent)
    self.edit_sources_widget.setVisible(False)    
    self.input_widget = factory.Factory.get_input_widget(mode, parent)
    self.output_widget = factory.Factory.get_output_widget(mode, parent)
    self.work_bench = factory.Factory.get_work_bench_widget(mode, parent)
    self._manager = factory.Factory.get_manager(mode)
    self._renamer = factory.Factory.get_rename_item_generator(mode)
    self._widgets = (self.input_widget, self.output_widget, self.work_bench)
    
    self.work_bench.workbench_changed_signal.connect(self.output_widget.rename_button.setEnabled)
    self.output_widget.renameSignal.connect(self._rename)
    self.output_widget.stop_signal.connect(self._stop_rename)
    self.work_bench.renameItemChangedSignal.connect(self.output_widget.on_rename_item_changed)    
    self.work_bench.show_edit_sources_signal.connect(self.edit_sources_widget.show)
    self.input_widget.show_edit_sources_signal.connect(self.edit_sources_widget.show)
    self.edit_sources_widget.accepted.connect(self.input_widget.on_sources_widget_finished)
    
    self.input_widget.explore_signal.connect(self._explore)
    self.input_widget.stop_signal.connect(self._stop_search)    
    
    self._worker_thread = None
    self._is_shutting_down = False
    
  def __del__(self):
    self._is_shutting_down = True
    self._stop_thread()
    
  def _explore(self):
    if self._worker_thread and self._worker_thread.isRunning():
      return

    for widget in self._widgets:
      widget.start_exploring()
      
    self._worker_thread = get_search_thread(self.mode, self._manager, self.input_widget.get_config()) 
    self._worker_thread.progress_signal.connect(self.input_widget.progress_bar.setValue)
    self._worker_thread.new_data_signal.connect(self.work_bench.add_item)
    self._worker_thread.log_signal.connect(self.log_signal)
    self._worker_thread.finished.connect(self._on_thread_finished)
    self._worker_thread.terminated.connect(self._on_thread_finished)    
    self._worker_thread.start()
    
  def _rename(self):
    if self._worker_thread and self._worker_thread.isRunning():
      return
    
    for widget in self._widgets:
      widget.start_actioning()

    self._renamer.config = self.output_widget.get_config()
    self._worker_thread = RenameThread("rename {}".format(self.mode), self._renamer, 
        self.work_bench.actionable_items())
    self._worker_thread.progress_signal.connect(self.output_widget.progress_bar.setValue)
    self._worker_thread.log_signal.connect(self.log_signal)
    self._worker_thread.finished.connect(self._on_thread_finished)
    self._worker_thread.terminated.connect(self._on_thread_finished)    
    self._worker_thread.start()
    
  def set_active(self):
    pass
        
  def set_inactive(self):
    self._stop_thread() #TODO: maybe prompt? In future, run in background.
    
  def _stop_thread(self):
    if self._worker_thread:
      self._worker_thread.join()
    
  def _on_thread_finished(self):    
    if not self._is_shutting_down:
      for widget in self._widgets:
        widget.stop_exploring()
        widget.stop_actioning()
      
  def _stop_rename(self):
    self.output_widget.stop_button.setEnabled(False)
    self._stop_thread()
   
  def _stop_search(self):
    self.input_widget.stop_button.setEnabled(False)
    self._stop_thread()     
