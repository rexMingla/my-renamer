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

import copy

from common import config
from common import file_helper
from common import interfaces
from common import thread
from common import utils

from media.base import client as base_client
from media.base import widget as base_widget

from media.tv import types as tv_types
from media.tv import client as tv_client
from media.tv import model as tv_model

_TITLE_COLUMN = 0

# --------------------------------------------------------------------------------------------------------------------
class TvWorkBenchWidget(base_widget.BaseWorkBenchWidget):
  def __init__(self, manager, parent=None):
    super(TvWorkBenchWidget, self).__init__(interfaces.TV_MODE, manager, parent)
    self._set_model(tv_model.TvModel(self.tv_view))

    self._changeEpisodeWidget = EditEpisodeWidget(self)
    self._changeEpisodeWidget.accepted.connect(self._onChangeEpisodeFinished)
    
    self._changeSeasonWidget = EditSeasonWidget(self)
    self._changeSeasonWidget.accepted.connect(self._onChangeSeasonFinished)
    self._changeSeasonWidget.show_edit_sources_signal.connect(self.show_edit_sources_signal.emit)
        
    self.tv_view.setModel(self._model)
    self.tv_view.header().setResizeMode(tv_model.Columns.COL_NEW_NAME, QtGui.QHeaderView.Interactive)
    self.tv_view.header().setResizeMode(tv_model.Columns.COL_OLD_NAME, QtGui.QHeaderView.Interactive)
    self.tv_view.header().setResizeMode(tv_model.Columns.COL_NEW_NUM, QtGui.QHeaderView.Interactive)
    self.tv_view.header().setResizeMode(tv_model.Columns.COL_STATUS, QtGui.QHeaderView.Interactive)
    self.tv_view.header().setStretchLastSection(True)
    #self.tv_view.setItemDelegateForColumn(tv_model.Columns.COL_NEW_NAME, tv_model.SeriesDelegate(self))
    
    self.tv_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
    self.tv_view.doubleClicked.connect(self._show_item)
    
    self.movie_view.setVisible(False)
    self.movie_group_box.setVisible(False)
    self._on_selection_changed()
    
  def get_config(self):
    ret = config.TvWorkBenchConfig()
    ret.state = utils.to_string(self.tv_view.header().saveState().toBase64())
    return ret
  
  def set_config(self, data):
    data = data or config.TvWorkBenchConfig()
    self.tv_view.header().restoreState(QtCore.QByteArray.fromBase64(data.state))
    
  def stop_exploring(self):
    super(TvWorkBenchWidget, self).stop_exploring()
    self.tv_view.expandAll()
    
  def _on_selection_changed(self, selection=None):
    selection = selection or self.tv_view.selectionModel().selection()
    indexes = selection.indexes()
    self._current_index = indexes[0] if indexes else QtCore.QModelIndex()
    self._update_actions()
    self.renameItemChangedSignal.emit(self._model.get_rename_item(self._current_index))
    
  def _show_item(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._current_index, tv_model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      if self._model.can_edit(self._current_index):
        self._edit_episode()
      else:
        QtGui.QMessageBox.information(self, 
          "Can not edit Episode", "Episodes can only be edited for existing files where Season data has been defined.")
    else:
      self._edit_season()
        
  def _edit_season(self):
    seasonData, isMoveItemCandidate = self._model.data(self._current_index, tv_model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      self._current_index  = self._current_index.parent()
      seasonData, isMoveItemCandidate = self._model.data(self._current_index, tv_model.RAW_DATA_ROLE)
    utils.verify(not isMoveItemCandidate, "Must be a movie to have gotten here!")
    self._changeSeasonWidget.set_data(seasonData)
    self._changeSeasonWidget.show()
  
  def _edit_episode(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._current_index, tv_model.RAW_DATA_ROLE)
    if isMoveItemCandidate and moveItemCandidateData.can_edit:
      seasonData, isMoveItemCandidate = self._model.data(self._current_index.parent(), tv_model.RAW_DATA_ROLE)
      utils.verify(not isMoveItemCandidate, "Must be move item")
      self._changeEpisodeWidget.set_data(seasonData, moveItemCandidateData)
      self._changeEpisodeWidget.show()
      
  def _onChangeEpisodeFinished(self):
    self._model.set_data(self._current_index, self._changeEpisodeWidget.episodeNumber(), tv_model.RAW_DATA_ROLE)
    self.tv_view.expand(self._current_index.parent())
    self._on_selection_changed()
    
  def _onChangeSeasonFinished(self):
    data = self._changeSeasonWidget.data()
    #utils.verify_type(data, tv_types.Season)
    self._manager.set_item(data.get_info())
    self._model.setData(self._current_index, data, tv_model.RAW_DATA_ROLE)
    self.tv_view.expand(self._current_index)

# --------------------------------------------------------------------------------------------------------------------
class GetSeasonThread(thread.WorkerThread):
  def __init__(self, search_params, store, is_lucky):
    super(GetSeasonThread, self).__init__("tv search")
    self._search_params = search_params
    self._store = store
    self._is_lucky = is_lucky

  def run(self):
    for info in self._store.get_all_info(self._search_params):
      self._on_data(info)
      if self._user_stopped or (info and self._is_lucky):
        break
    
# --------------------------------------------------------------------------------------------------------------------
class EditSeasonWidget(QtGui.QDialog):
  show_edit_sources_signal = QtCore.pyqtSignal()
  """ The widget allows the user to search and modify tv info. """
  def __init__(self, parent=None):
    super(EditSeasonWidget, self).__init__(parent)
    uic.loadUi("ui/ui_ChangeSeason.ui", self)
    self.setWindowModality(True)
    self._worker_thread = None
    self._data = tv_types.Season("", tv_types.SeasonInfo(), tv_types.SourceFiles())
    
    self.search_button.clicked.connect(self._search)
    self.search_button.setIcon(QtGui.QIcon("img/search.png"))
    self.stop_button.clicked.connect(self._stop_thread)
    self.stop_button.setIcon(QtGui.QIcon("img/stop.png"))
    self.add_button.clicked.connect(self._add)
    self.remove_button.clicked.connect(self._remove)
    self.up_button.clicked.connect(self._move_up)
    self.down_button.clicked.connect(self._move_down)
    self.episode_table.cellClicked.connect(self._on_selection_changed)
    self.index_spin_box.valueChanged.connect(self._updateColumnHeaders)
    self.hide_label.linkActivated.connect(self._hide_results)    
    self.show_label.linkActivated.connect(self._show_results)    
    self.show_source_button.clicked.connect(self.show_edit_sources_signal.emit)    

    self.season_edit.installEventFilter(self)
    self.season_spin_box.installEventFilter(self)

    self._search_results = base_widget.SearchResultsWidget(self)
    self._search_results.itemSelectedSignal.connect(self._setSeasonInfo)
    layout = QtGui.QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    self.placeholder_widget.setLayout(layout)
    layout.addWidget(self._search_results)
    
    self._is_lucky = False
    self._found_data = True    
    self._on_thread_finished()
    self._hide_results()    
    self.show_label.setVisible(False)
    
  def __del__(self):
    self._stop_thread()
    
  def showEvent(self, e):
    self._found_data = True    
    self._on_thread_finished()
    self._hide_results()    
    self.show_label.setVisible(False)    
    super(EditSeasonWidget, self).showEvent(e)
    
  def eventFilter(self, o, e):
    if o in (self.season_spin_box, self.season_edit) and \
      e.type() == QtCore.QEvent.KeyPress and e.key() == QtCore.Qt.Key_Return:
      e.ignore()
      self._search()
      return False
    return super(EditSeasonWidget, self).eventFilter(o, e)  
    
  def _search(self):
    if self._worker_thread and self._worker_thread.isRunning():
      return
    self._is_lucky = self.is_lucky_check_box.isChecked()
    self._found_data = False

    self.search_button.setVisible(False)
    self.stop_button.setEnabled(True)
    self.stop_button.setVisible(True)
    self.episode_group_box.setEnabled(False)
    self.buttonBox.setEnabled(False)
    self.placeholder_widget.setEnabled(False)    
    self.progress_bar.setVisible(True)
    
    self._worker_thread = GetSeasonThread(tv_types.TvSearchParams(utils.to_string(self.season_edit.text()), 
                                                                     self.season_spin_box.value()),
                                         tv_client.get_store_helper(),
                                         self._is_lucky)
    self._worker_thread.new_data_signal.connect(self._onDataFound)
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
    self.episode_group_box.setEnabled(True)
    self.buttonBox.setEnabled(True)
    self.placeholder_widget.setEnabled(True)
    self.progress_bar.setVisible(False)

    self._on_selection_changed()
    if not self._found_data:
      QtGui.QMessageBox.information(self, "Nothing found", "No results found for search")    
    
  def _onDataFound(self, data):
    if not data:
      return
    
    if self._is_lucky:
      self._setSeasonInfo(data.info)
    else:
      if not self._found_data:
        self._search_results.clear()
        self._search_results.add_item(base_client.ResultHolder(self.data().info, "current"))
      self._search_results.add_item(data)
      self._show_results()
    self._found_data = True
    
  def _on_selection_changed(self):
    currentIndex = self.episode_table.currentItem().row() if self.episode_table.currentItem() else -1
    self.remove_button.setEnabled(currentIndex != -1)
    self.up_button.setEnabled(currentIndex >= 1)
    self.down_button.setEnabled((currentIndex + 1) < self.episode_table.rowCount())
    
  def _move_down(self):
    currentItem = self.episode_table.currentItem()
    utils.verify(currentItem, "Must have current item to get here")
    nextItem = self.episode_table.item(currentItem.row() + 1, _TITLE_COLUMN)
    temp = nextItem.text()
    nextItem.setText(currentItem.text())
    currentItem.setText(temp)
    self.episode_table.setCurrentItem(nextItem)
    self._on_selection_changed()
    
  def _move_up(self):
    currentItem = self.episode_table.currentItem()
    utils.verify(currentItem, "Must have current item to get here")
    nextItem = self.episode_table.item(currentItem.row() - 1, _TITLE_COLUMN)
    temp = nextItem.text()
    nextItem.setText(currentItem.text())
    currentItem.setText(temp)
    self.episode_table.setCurrentItem(nextItem)
    self._on_selection_changed()
  
  def _add(self):
    currentItem = self.episode_table.currentItem()
    row = currentItem.row() if currentItem else self.episode_table.rowCount()
    item = QtGui.QTableWidgetItem("")
    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)    
    #self.episode_table.setRowCount(self.episode_table.rowCount() + 1)
    self.episode_table.insertRow(row)
    self.episode_table.setItem(row, _TITLE_COLUMN, item)
    self._on_selection_changed()
    self._updateColumnHeaders()
  
  def _remove(self):
    currentItem = self.episode_table.currentItem()
    utils.verify(currentItem, "Must have current item to get here")
    self.episode_table.removeRow(currentItem.row())
    self._on_selection_changed()
    self._updateColumnHeaders()
      
  def _updateColumnHeaders(self):
    startIndex = self.index_spin_box.value()
    rowCount = self.episode_table.rowCount()
    self.episode_table.setVerticalHeaderLabels([str(i) for i in range(startIndex, rowCount + startIndex)])
  
  def set_data(self, s):
    """ Fill the dialog with the data prior to being shown """
    #utils.verify_type(s, tv_types.Season)
    self._data = s
    self.folder_edit.setText(file_helper.FileHelper.basename(s.input_folder))    
    self.folder_edit.setToolTip(s.input_folder)    
    self._setSeasonInfo(s.info)
    self.season_edit.selectAll()    
    
  def _setSeasonInfo(self, info):
    #utils.verify_type(info, tv_types.SeasonInfo)
    self.season_edit.setText(info.show_name)
    self.season_spin_box.setValue(info.season_num)    
    self.episode_table.clearContents()
    
    minValue = min([ep.ep_num for ep in info.episodes] or [0])
    maxValue = max([ep.ep_num for ep in info.episodes] or [-1])
    self.index_spin_box.setValue(minValue)
    
    ep_nums = [i for i in range(minValue, maxValue + 1)]
    self.episode_table.setRowCount(len(ep_nums))
    for i, ep_num in enumerate(ep_nums):
      ep = info.get_episode_by_episode_num(ep_num)
      item = QtGui.QTableWidgetItem(ep.ep_name)
      item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
      self.episode_table.setItem(i, _TITLE_COLUMN, item)
    self._on_selection_changed()
    
  def data(self):   
    info = tv_types.SeasonInfo(utils.to_string(self.season_edit.text()), self.season_spin_box.value()) 
    startIndex = self.index_spin_box.value()
    for i in range(self.episode_table.rowCount()):
      ep_name = self.episode_table.item(i, _TITLE_COLUMN)
      info.episodes.append(tv_types.EpisodeInfo(i + startIndex, utils.to_string(ep_name.text())))
    self._data.update_season_info(info)
    return copy.copy(self._data)
  
  def _show_results(self):
    self.placeholder_widget.setVisible(True)
    self.hide_label.setVisible(True)
    self.show_label.setVisible(False)
  
  def _hide_results(self):
    self.placeholder_widget.setVisible(False)
    self.hide_label.setVisible(False)
    self.show_label.setVisible(True)

# --------------------------------------------------------------------------------------------------------------------
class EditEpisodeWidget(QtGui.QDialog):
  """ Allows the user to assign an episode to a given file """
  def __init__(self, parent=None):
    super(QtGui.QDialog, self).__init__(parent)
    self._ui = uic.loadUi("ui/ui_ChangeEpisode.ui", self)
    self.pick_from_list_radio.toggled.connect(self.episode_combo_box.setEnabled)
    self.setWindowModality(True)
    
  def showEvent(self, _event):
    """ protected Qt function """
    utils.verify(self.episode_combo_box.count() > 0, "No items in list")
    self.setMaximumHeight(self.sizeHint().height())
    self.setMinimumHeight(self.sizeHint().height())
  
  def set_data(self, ssn, ep):
    """ Fill the dialog with the data prior to being shown """
    #utils.verify_type(ssn, tv_types.Season)
    #utils.verify_type(ep, tv_types.EpisodeRenameItem)
    self.episode_combo_box.clear()
    #episode_move_items = copy.copy(ssn.episode_move_items)
    #episode_move_items = sorted(episode_move_items, key=lambda item: item.info.ep_num)
    for mi in ssn.episode_move_items:
      if mi.info.ep_num != tv_types.UNRESOLVED_KEY:
        display_name = "{}: {}".format(mi.info.ep_num, mi.info.ep_name)
        self.episode_combo_box.addItem(display_name, mi.info.ep_num)
    index = self.episode_combo_box.findData(ep.info.ep_num)
    if index != -1:
      self.pick_from_list_radio.setChecked(True)
      self.episode_combo_box.setCurrentIndex(index)
    else:
      self.ignore_radio.setChecked(True)
    self.filename_edit.setText(file_helper.FileHelper.basename(ep.filename))
    self.filename_edit.setToolTip(ep.filename)
    self.episode_combo_box.setEnabled(index != -1)
    
  def episodeNumber(self):
    """ 
    Returns the currently selected episode number from the dialog. 
    Returns tv_types.UNRESOLVED_KEY if non is selected. 
    """
    if self.ignore_radio.isChecked():
      return tv_types.UNRESOLVED_KEY
    else:
      return self.episode_combo_box.itemData(self.episode_combo_box.currentIndex()).toInt()[0]