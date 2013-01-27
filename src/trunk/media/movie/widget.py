  #!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: ??
# --------------------------------------------------------------------------------------------------------------------
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from media.movie import model as movie_model
from media.movie import client as movie_client
from media.movie import types as movie_types

from media.base import client as base_client
from media.base import widget as base_widget

from common import config
from common import interfaces
from common import file_helper
from common import thread 
from common import utils

# --------------------------------------------------------------------------------------------------------------------
class MovieWorkBenchWidget(base_widget.BaseWorkBenchWidget):
  def __init__(self, manager, parent=None):
    super(MovieWorkBenchWidget, self).__init__(interfaces.MOVIE_MODE, manager, parent)
    self._set_model(movie_model.MovieModel(self.movie_view))
    
    self._change_movie_widget = EditMovieWidget(self)
    self._change_movie_widget.accepted.connect(self._on_change_movie_finished)
    self._change_movie_widget.show_edit_sources_signal.connect(self.show_edit_sources_signal.emit)    
    
    self._sort_model = movie_model.SortFilterModel(self)
    self._sort_model.setSourceModel(self._model)  
    self.movie_view.setModel(self._sort_model)
    self.movie_view.horizontalHeader().setResizeMode(movie_model.Columns.COL_CHECK, QtGui.QHeaderView.Fixed)
    self.movie_view.horizontalHeader().resizeSection(movie_model.Columns.COL_CHECK, 25)
    self.movie_view.horizontalHeader().setResizeMode(movie_model.Columns.COL_NEW_NAME, QtGui.QHeaderView.Interactive)
    self.movie_view.horizontalHeader().setResizeMode(movie_model.Columns.COL_OLD_NAME, QtGui.QHeaderView.Interactive)
    self.movie_view.horizontalHeader().setResizeMode(movie_model.Columns.COL_YEAR, QtGui.QHeaderView.Interactive)
    self.movie_view.horizontalHeader().setResizeMode(movie_model.Columns.COL_DISC, QtGui.QHeaderView.Interactive)
    self.movie_view.horizontalHeader().setResizeMode(movie_model.Columns.COL_STATUS, QtGui.QHeaderView.Interactive)
    self.movie_view.horizontalHeader().setResizeMode(movie_model.Columns.COL_GENRE, QtGui.QHeaderView.Interactive)
    self.movie_view.horizontalHeader().setStretchLastSection(True)
    self.movie_view.verticalHeader().setDefaultSectionSize(20)
    self.movie_view.setSortingEnabled(True)
        
    self.require_year_check_box.toggled.connect(self._require_year_changed)
    self.require_genre_check_box.toggled.connect(self._require_genre_changed)
    self.require_non_duplicate_box.toggled.connect(self._flag_duplicate_changed)
    self.movie_view.selectionModel().selectionChanged.connect(self._on_selection_changed)    
    self.movie_view.doubleClicked.connect(self._edit_movie)
    self.edit_movie_button.clicked.connect(self._edit_movie)

    self._require_year_changed(self.require_year_check_box.isChecked())
    self._require_genre_changed(self.require_genre_check_box.isChecked())
    self._flag_duplicate_changed(self.require_non_duplicate_box.isChecked())
    
    self.tv_view.setVisible(False)
    self._on_selection_changed()
     
  def get_config(self):
    ret = config.MovieWorkBenchConfig()
    ret.no_year_as_error = self.require_year_check_box.isChecked()
    ret.no_genre_as_error = self.require_genre_check_box.isChecked()
    ret.duplicate_as_error = self.require_non_duplicate_box.isChecked()
    ret.state = utils.to_string(self.movie_view.horizontalHeader().saveState().toBase64())
    ret.series_list = self._change_movie_widget.get_series_list()
    return ret
  
  def set_config(self, data):
    data = data or config.MovieWorkBenchConfig()

    self.require_year_check_box.setChecked(data.no_year_as_error)
    self.require_genre_check_box.setChecked(data.no_genre_as_error)
    self.require_non_duplicate_box.setChecked(data.duplicate_as_error)
    self.movie_view.horizontalHeader().restoreState(QtCore.QByteArray.fromBase64(data.state))
    self._change_movie_widget.set_series_list(data.series_list)
    
  def _show_item(self):    
    self._edit_movie()

  def _on_selection_changed(self, selection=None):
    selection = selection or self.movie_view.selectionModel().selection()
    indexes = selection.indexes()
    self._current_index = self._sort_model.mapToSource(indexes[0]) if indexes else QtCore.QModelIndex()
    self._update_actions()
    self.renameItemChangedSignal.emit(self._model.get_rename_item(self._current_index))
    
  def _edit_movie(self):
    movie = self._model.data(self._current_index, movie_model.RAW_DATA_ROLE)
    #utils.verify_type(movie, movie_manager.MovieRenameItem)
    self._change_movie_widget.set_data(movie)
    self._change_movie_widget.show()    
      
  def _on_change_movie_finished(self):
    data = self._change_movie_widget.data()    
    #utils.verify_type(data, movie_manager.MovieRenameItem)
    self._manager.set_item(data.get_info())
    self._model.set_data(self._current_index, data, movie_model.RAW_DATA_ROLE)
    self._on_selection_changed()
    
  def _require_year_changed(self, require_year):
    self._disable()
    self._model.require_year_changed(require_year)
    self._enable()

  def _require_genre_changed(self, require_genre):
    self._disable()
    self._model.require_genre_changed(require_genre)
    self._enable()

  def _flag_duplicate_changed(self, flag_duplicate):
    self._disable()
    self._model.flag_duplicate_changed(flag_duplicate)
    self._enable()

# --------------------------------------------------------------------------------------------------------------------
class _GetMovieThread(thread.WorkerThread):
  """ search for movie from sources """
  
  def __init__(self, search_params, is_lucky):
    super(_GetMovieThread, self).__init__("movie search")
    self._search_params = search_params
    self._store = movie_client.get_store_helper()
    self._is_lucky = is_lucky

  def run(self):
    for info in self._store.get_all_info(self._search_params):
      self._on_data(info)
      if self._user_stopped or (info and self._is_lucky):
        break

# --------------------------------------------------------------------------------------------------------------------
class EditMovieWidget(QtGui.QDialog):
  """ The widget allows the user to search and modify movie info. """
  show_edit_sources_signal = QtCore.pyqtSignal()
  def __init__(self, parent=None):
    super(EditMovieWidget, self).__init__(parent)
    uic.loadUi("ui/ui_ChangeMovie.ui", self)
    self._worker_thread = None
    self.setWindowModality(True)
    self.search_edit.setPlaceholderText("Enter movie and year to search")
    self.search_edit.installEventFilter(self)
    self.search_button.clicked.connect(self._search)
    self.search_button.setIcon(QtGui.QIcon("img/search.png"))
    
    self._search_results = base_widget.SearchResultsWidget(self)
    self._search_results.itemSelectedSignal.connect(self._set_movie_info)
    layout = QtGui.QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    self.placeholder_widget.setLayout(layout)
    layout.addWidget(self._search_results)

    self.hide_label.linkActivated.connect(self._hide_results)    
    self.show_label.linkActivated.connect(self._show_results)    
    self.stop_button.clicked.connect(self._stop_thread)    
    self.stop_button.setIcon(QtGui.QIcon("img/stop.png"))
    self.part_check_box.toggled.connect(self.part_spin_box.setEnabled)
    self.show_source_button.clicked.connect(self.show_edit_sources_signal.emit)    
    
    self._item = None
    self._is_lucky = False
    self._found_data = True
    self._on_thread_finished()
    self._hide_results()    
    self.show_label.setVisible(False)
    self._series_list = []
    
  def __del__(self):
    self._stop_thread()
        
  def accept(self):
    series = utils.to_string(self.series_edit.text())
    if series and not series in self._series_list:
      self._series_list.append(series)
      self.set_series_list(self._series_list)    
    return super(EditMovieWidget, self).accept()
        
  def eventFilter(self, obj, event):
    if obj == self.search_edit and event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Return:
      event.ignore()
      self._search()
      return False
    return super(EditMovieWidget, self).eventFilter(obj, event)
    
  def showEvent(self, event):
    self._found_data = True    
    self._on_thread_finished()
    self._hide_results()    
    self.show_label.setVisible(False)    
    super(EditMovieWidget, self).showEvent(event)  

  def _search(self):
    if self._worker_thread and self._worker_thread.isRunning():
      return
    self._is_lucky = self.is_lucky_check_box.isChecked()
    self._found_data = False

    self.search_button.setVisible(False)
    self.stop_button.setEnabled(True)
    self.stop_button.setVisible(True)
    self.dataGroupBox.setEnabled(False)
    self.buttonBox.setEnabled(False)
    self.placeholder_widget.setEnabled(False)    
    self.progress_bar.setVisible(True)
    
    search_text = utils.to_string(self.search_edit.text())
    self._worker_thread = _GetMovieThread(movie_types.MovieSearchParams(search_text), self._is_lucky)
    self._worker_thread.new_data_signal.connect(self._on_movie_info)
    self._worker_thread.finished.connect(self._on_thread_finished)
    self._worker_thread.terminated.connect(self._on_thread_finished)    
    self._worker_thread.start()  
    
  def _stop_thread(self):
    self.stop_button.setEnabled(False)
    if self._worker_thread:
      self._worker_thread.join()
    
  def _on_thread_finished(self):    
    self.stop_button.setVisible(False)
    self.search_button.setVisible(True)
    self.search_button.setEnabled(True)
    self.dataGroupBox.setEnabled(True)
    self.buttonBox.setEnabled(True)
    self.placeholder_widget.setEnabled(True)    
    self.progress_bar.setVisible(False)   
    
    if not self._found_data:
      QtGui.QMessageBox.information(self, "Nothing found", "No results found for search")
    
  def _on_movie_info(self, data):
    if not data:
      return
    
    if self._is_lucky:
      self._set_movie_info(data.info)
    else:
      if not self._found_data:
        self._search_results.clear()
        self._search_results.add_item(base_client.ResultHolder(self._get_movie_info(), "current"))
      self._search_results.add_item(data)
      self._show_results()
    self._found_data = True
    
  def _get_movie_info(self):
    genre_str = utils.to_string(self.genre_edit.text())
    return movie_types.MovieInfo(utils.to_string(self.title_edit.text()),
                                     utils.to_string(self.year_edit.text()),
                                     [genre_str] if genre_str else [])
      
  def _set_movie_info(self, info):
    #utils.verify_type(info, movie_types.MovieInfo)
    self.title_edit.setText(info.title)
    self.year_edit.setText(info.year or "")
    self.genre_edit.setText(info.get_genre())  
    
  def set_series_list(self, obj):
    #utils.verify_type(l, list)
    self._series_list = obj
    completer = QtGui.QCompleter(self._series_list, self)
    completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
    completer.setCompletionMode(QtGui.QCompleter.InlineCompletion)    
    self.series_edit.setCompleter(completer)        
    
  def get_series_list(self):
    return self._series_list
  
  def set_data(self, item):
    """ Fill the dialog with the data prior to being shown """
    #utils.verify_type(item, movie_manager.MovieRenameItem)
    self._item = item  
    self.filename_edit.setText(file_helper.FileHelper.basename(item.filename))
    self.filename_edit.setToolTip(item.filename)
    info = item.info
    self.title_edit.setText(info.title)
    self.search_edit.setText(info.title)
    self.search_edit.selectAll()
    self.year_edit.setText(info.year or "")
    self.genre_edit.setText(info.get_genre(""))
    self.series_edit.setText(info.series)
    if info.part:
      self.part_spin_box.setValue(int(info.part))
    self.part_check_box.setChecked(bool(info.part))
    
  def data(self):
    self._item.info.title = utils.to_string(self.title_edit.text())
    self._item.info.year = utils.to_string(self.year_edit.text())
    genre = utils.to_string(self.genre_edit.text()).strip()
    if genre:
      genre = [genre]
    else:
      genre = []
    self._item.info.genres = genre
    self._item.info.part = None
    if self.part_check_box.isChecked():
      self._item.info.part = self.part_spin_box.value()
    self._item.info.series = utils.to_string(self.series_edit.text()).strip()
    return self._item
  
  def _show_results(self):
    self.placeholder_widget.setVisible(True)
    self.hide_label.setVisible(True)
    self.show_label.setVisible(False)
  
  def _hide_results(self):
    self.placeholder_widget.setVisible(False)
    self.hide_label.setVisible(False)
    self.show_label.setVisible(True)
  