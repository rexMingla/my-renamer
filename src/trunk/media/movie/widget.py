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
    
    self._change_movie_widget = EditMovieItemWidget(manager.get_holder(), self)
    self._change_movie_widget.accepted.connect(self._on_change_movie_finished)
    self._change_movie_widget.show_edit_sources_signal.connect(self.show_edit_sources_signal.emit)    
    self._change_movie_widget.setVisible(False)
    
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
    #TODO: ret.series_list = self._change_movie_widget.get_series_list()
    return ret
  
  def set_config(self, data):
    data = data or config.MovieWorkBenchConfig()

    self.require_year_check_box.setChecked(data.no_year_as_error)
    self.require_genre_check_box.setChecked(data.no_genre_as_error)
    self.require_non_duplicate_box.setChecked(data.duplicate_as_error)
    self.movie_view.horizontalHeader().restoreState(QtCore.QByteArray.fromBase64(data.state))
    #TODO: self._change_movie_widget.set_series_list(data.series_list)
    
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
    self._change_movie_widget.set_item(movie)
    self._change_movie_widget.show()    
      
  def _on_change_movie_finished(self):
    data = self._change_movie_widget.get_item()    
    #utils.verify_type(data, movie_manager.MovieRenameItem)
    self._manager.set_item(data.get_info())
    self._model.setData(self._current_index, data, movie_model.RAW_DATA_ROLE)
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
class SearchMovieParamsWidget(base_widget.BaseSearchParamsWidget):
  def __init__(self, parent=None):
    super(SearchMovieParamsWidget, self).__init__(parent)
    uic.loadUi("ui/ui_SearchMovie.ui", self)
    self._set_edit_widgets([self.search_edit])
    self.search_edit.setPlaceholderText("Enter movie and year to search")
    
  def set_item(self, item):
    item = item or movie_types.MovieRenameItem("", movie_types.MovieInfo())
    self.filename_edit.setText(file_helper.FileHelper.basename(item.filename))
    self.filename_edit.setToolTip(item.filename)
    self.search_edit.setText(item.get_info().to_search_params().get_key())
    self.search_edit.selectAll()    
  
  def get_search_params(self):
    return movie_types.MovieSearchParams(str(self.search_edit.text()))
    
# --------------------------------------------------------------------------------------------------------------------
class EditMovieInfoWidget(base_widget.BaseEditInfoWidget):
  """ The widget allows the user to search and modify movie info. """
  show_edit_sources_signal = QtCore.pyqtSignal()
  def __init__(self, parent=None):
    super(EditMovieInfoWidget, self).__init__(parent)
    uic.loadUi("ui/ui_EditMovie.ui", self)
    self.setWindowModality(True)
    self.part_check_box.toggled.connect(self.part_spin_box.setEnabled)
    
    self._item = None
    self._series_list = []
    
  def accept(self):
    series = utils.to_string(self.series_edit.text())
    if series and not series in self._series_list:
      self._series_list.append(series)
      #TODO: self.set_series_list(self._series_list)    
    return super(EditMovieItemWidget, self).accept()
    
  def set_info(self, info):
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
  
  def _set_item(self, item):
    """ Fill the dialog with the data prior to being shown """
    #utils.verify_type(item, movie_manager.MovieRenameItem)
    self._item = item or movie_types.MovieRenameItem("", movie_types.MovieInfo())
    info = self._item.get_info()
    self.title_edit.setText(info.title)
    self.year_edit.setText(info.year)
    self.genre_edit.setText(info.get_genre(""))
    self.series_edit.setText(info.series)
    if info.part:
      self.part_spin_box.setValue(int(info.part))
    self.part_check_box.setChecked(bool(info.part))
    
  def get_item(self):
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

# --------------------------------------------------------------------------------------------------------------------
class EditMovieItemWidget(base_widget.EditItemWidget):
  def __init__(self, holder, parent=None):
    super(EditMovieItemWidget, self).__init__(
        interfaces.MOVIE_MODE, holder, SearchMovieParamsWidget(parent), EditMovieInfoWidget(parent), parent)

