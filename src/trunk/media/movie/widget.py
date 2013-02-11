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
from media.base import types as base_types

from common import config
from common import file_helper
from common import thread
from common import utils

# --------------------------------------------------------------------------------------------------------------------
class MovieWorkBenchWidget(base_widget.BaseWorkBenchWidget):
  def __init__(self, manager, parent=None):
    super(MovieWorkBenchWidget, self).__init__(base_types.MOVIE_MODE, manager, parent)
    self._setModel(movie_model.MovieModel(self.movie_view))

    self._change_movie_widget = EditMovieItemWidget(manager.getHolder(), self)
    self._change_movie_widget.accepted.connect(self._onChangeMovieFinished)
    self._change_movie_widget.show_edit_info_clients_signal.connect(self.show_edit_info_clients_signal.emit)
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

    self.require_year_check_box.toggled.connect(self._requireYearChanged)
    self.require_genre_check_box.toggled.connect(self._requireGenreChanged)
    self.require_non_duplicate_box.toggled.connect(self._flagDuplicateChanged)
    self.movie_view.selectionModel().selectionChanged.connect(self._onSelectionChanged)
    self.movie_view.doubleClicked.connect(self._editMovie)
    self.edit_movie_button.clicked.connect(self._editMovie)

    self._requireYearChanged(self.require_year_check_box.isChecked())
    self._requireGenreChanged(self.require_genre_check_box.isChecked())
    self._flagDuplicateChanged(self.require_non_duplicate_box.isChecked())

    self.tv_view.setVisible(False)
    self._onSelectionChanged()

  def getConfig(self):
    ret = config.MovieWorkBenchConfig()
    ret.no_year_as_error = self.require_year_check_box.isChecked()
    ret.no_genre_as_error = self.require_genre_check_box.isChecked()
    ret.duplicate_as_error = self.require_non_duplicate_box.isChecked()
    ret.state = utils.toString(self.movie_view.horizontalHeader().saveState().toBase64())
    #TODO: ret.series_list = self._change_movie_widget.getSeriesList()
    return ret

  def setConfig(self, data):
    data = data or config.MovieWorkBenchConfig()

    self.require_year_check_box.setChecked(data.no_year_as_error)
    self.require_genre_check_box.setChecked(data.no_genre_as_error)
    self.require_non_duplicate_box.setChecked(data.duplicate_as_error)
    self.movie_view.horizontalHeader().restoreState(QtCore.QByteArray.fromBase64(data.state))
    #TODO: self._change_movie_widget.setSeriesList(data.series_list)

  def _showItem(self):
    self._editMovie()

  def _onSelectionChanged(self, selection=None):
    selection = selection or self.movie_view.selectionModel().selection()
    indexes = selection.indexes()
    self._current_index = self._sort_model.mapToSource(indexes[0]) if indexes else QtCore.QModelIndex()
    self._updateActions()
    self.renameItemChangedSignal.emit(self._model.getRenameItem(self._current_index))

  def _editMovie(self):
    movie = self._model.data(self._current_index, movie_model.RAW_DATA_ROLE)
    #utils.verifyType(movie, movie_manager.MovieRenameItem)
    self._change_movie_widget.setItem(movie)
    self._change_movie_widget.show()

  def _onChangeMovieFinished(self):
    item = self._change_movie_widget.getItem()
    #utils.verifyType(item, movie_manager.MovieRenameItem)
    self._manager.setInfo(item.getInfo())
    self._model.setData(self._current_index, item, movie_model.RAW_DATA_ROLE)
    self._onSelectionChanged()

  def _requireYearChanged(self, require_year):
    self._disable()
    self._model.requireYearChanged(require_year)
    self._enable()

  def _requireGenreChanged(self, require_genre):
    self._disable()
    self._model.requireGenreChanged(require_genre)
    self._enable()

  def _flagDuplicateChanged(self, flag_duplicate):
    self._disable()
    self._model.flagDuplicateChanged(flag_duplicate)
    self._enable()

# --------------------------------------------------------------------------------------------------------------------
class SearchMovieParamsWidget(base_widget.BaseSearchParamsWidget):
  def __init__(self, parent=None):
    super(SearchMovieParamsWidget, self).__init__(parent)
    uic.loadUi("ui/ui_SearchMovie.ui", self)
    self._setEditWidgets([self.search_edit])
    self.search_edit.setPlaceholderText("Enter movie and year to search")

  def setItem(self, item):
    item = item or movie_types.MovieRenameItem("", movie_types.MovieInfo())
    self.filename_edit.setText(file_helper.FileHelper.basename(item.filename))
    self.filename_edit.setToolTip(item.filename)
    self.search_edit.setText(item.getInfo().getSearchParams().getKey())
    self.search_edit.selectAll()

  def getSearchParams(self):
    return movie_types.MovieSearchParams(str(self.search_edit.text()))

# --------------------------------------------------------------------------------------------------------------------
class EditMovieInfoWidget(base_widget.BaseEditInfoWidget):
  """ The widget allows the user to search and modify movie info. """
  show_edit_info_clients_signal = QtCore.pyqtSignal()
  def __init__(self, parent=None):
    super(EditMovieInfoWidget, self).__init__(parent)
    uic.loadUi("ui/ui_EditMovie.ui", self)
    self.setWindowModality(True)
    self.part_check_box.toggled.connect(self.part_spin_box.setEnabled)

    self._series_list = []

  def accept(self):
    series = utils.toString(self.series_edit.text())
    if series and not series in self._series_list:
      self._series_list.append(series)
      #TODO: self.setSeriesList(self._series_list)
    return super(EditMovieItemWidget, self).accept()

  def setSeriesList(self, obj):
    #utils.verifyType(l, list)
    self._series_list = obj
    completer = QtGui.QCompleter(self._series_list, self)
    completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
    completer.setCompletionMode(QtGui.QCompleter.InlineCompletion)
    self.series_edit.setCompleter(completer)

  def getSeriesList(self):
    return self._series_list

  def setInfo(self, info):
    """ Fill the dialog with the data prior to being shown """
    #utils.verifyType(item, movie_manager.MovieRenameItem)
    info = info or movie_types.MovieInfo()
    self.title_edit.setText(info.title)
    self.year_edit.setText(info.year)
    self.genre_edit.setText(info.getGenre(""))
    self.series_edit.setText(info.series)
    if info.part:
      self.part_spin_box.setValue(int(info.part))
    self.part_check_box.setChecked(bool(info.part))

  def getInfo(self):
    title = utils.toString(self.title_edit.text())
    year = utils.toString(self.year_edit.text())
    genre = utils.toString(self.genre_edit.text()).strip()
    genres = [genre] if genre else []
    part = None if not self.part_check_box.isChecked() else self.part_spin_box.value()
    series = utils.toString(self.series_edit.text()).strip()
    return movie_types.MovieInfo(title, year, genres, series, part)

# --------------------------------------------------------------------------------------------------------------------
class EditMovieItemWidget(base_widget.EditItemWidget):
  def __init__(self, holder, parent=None):
    super(EditMovieItemWidget, self).__init__(
        base_types.MOVIE_MODE, holder, SearchMovieParamsWidget(parent), EditMovieInfoWidget(parent), parent)

