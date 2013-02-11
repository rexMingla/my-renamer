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

from common import config
from common import file_helper
from common import thread
from common import utils

from media.base import client as base_client
from media.base import widget as base_widget
from media.base import types as base_types

from media.tv import types as tv_types
from media.tv import client as tv_client
from media.tv import model as tv_model

_TITLE_COLUMN = 0

# --------------------------------------------------------------------------------------------------------------------
class TvWorkBenchWidget(base_widget.BaseWorkBenchWidget):
  def __init__(self, manager, parent=None):
    super(TvWorkBenchWidget, self).__init__(base_types.TV_MODE, manager, parent)
    self._setModel(tv_model.TvModel(self.tv_view))

    self._change_episode_widget = EditEpisodeWidget(self)
    self._change_episode_widget.accepted.connect(self._onChangeEpisodeFinished)
    self._change_episode_widget.setVisible(False)

    self._change_season_widget = EditSeasonItemWidget(manager.getHolder(), self)
    self._change_season_widget.accepted.connect(self._onChangeSeasonFinished)
    self._change_season_widget.show_edit_sources_signal.connect(self.show_edit_sources_signal.emit)
    self._change_season_widget.setVisible(False)

    self.tv_view.setModel(self._model)
    self.tv_view.header().setResizeMode(tv_model.Columns.COL_NEW_NAME, QtGui.QHeaderView.Interactive)
    self.tv_view.header().setResizeMode(tv_model.Columns.COL_OLD_NAME, QtGui.QHeaderView.Interactive)
    self.tv_view.header().setResizeMode(tv_model.Columns.COL_NEW_NUM, QtGui.QHeaderView.Interactive)
    self.tv_view.header().setResizeMode(tv_model.Columns.COL_STATUS, QtGui.QHeaderView.Interactive)
    self.tv_view.header().setStretchLastSection(True)
    #self.tv_view.setItemDelegateForColumn(tv_model.Columns.COL_NEW_NAME, tv_model.SeriesDelegate(self))

    self.tv_view.selectionModel().selectionChanged.connect(self._onSelectionChanged)
    self.tv_view.doubleClicked.connect(self._showItem)

    self.movie_view.setVisible(False)
    self.movie_group_box.setVisible(False)
    self._onSelectionChanged()

  def getConfig(self):
    ret = config.TvWorkBenchConfig()
    ret.state = utils.toString(self.tv_view.header().saveState().toBase64())
    return ret

  def setConfig(self, data):
    data = data or config.TvWorkBenchConfig()
    self.tv_view.header().restoreState(QtCore.QByteArray.fromBase64(data.state))

  def stopExploring(self):
    super(TvWorkBenchWidget, self).stopExploring()
    self.tv_view.expandAll()

  def _onSelectionChanged(self, selection=None):
    selection = selection or self.tv_view.selectionModel().selection()
    indexes = selection.indexes()
    self._current_index = indexes[0] if indexes else QtCore.QModelIndex()
    self._updateActions()
    self.renameItemChangedSignal.emit(self._model.getRenameItem(self._current_index))

  def _showItem(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._current_index, tv_model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      if self._model.canEdit(self._current_index):
        self._editEpisode()
      else:
        QtGui.QMessageBox.information(self,
          "Can not edit Episode", "Episodes can only be edited for existing files where Season data has been defined.")
    else:
      self._editSeason()

  def _editSeason(self):
    seasonData, isMoveItemCandidate = self._model.data(self._current_index, tv_model.RAW_DATA_ROLE)
    if isMoveItemCandidate:
      self._current_index  = self._current_index.parent()
      seasonData, isMoveItemCandidate = self._model.data(self._current_index, tv_model.RAW_DATA_ROLE)
    utils.verify(not isMoveItemCandidate, "Must be a movie to have gotten here!")
    self._change_season_widget.setItem(seasonData)
    self._change_season_widget.show()

  def _editEpisode(self):
    moveItemCandidateData, isMoveItemCandidate = self._model.data(self._current_index, tv_model.RAW_DATA_ROLE)
    if isMoveItemCandidate and moveItemCandidateData.canEdit:
      seasonData, isMoveItemCandidate = self._model.data(self._current_index.parent(), tv_model.RAW_DATA_ROLE)
      utils.verify(not isMoveItemCandidate, "Must be move item")
      self._change_episode_widget.setItem(seasonData, moveItemCandidateData)
      self._change_episode_widget.show()

  def _onChangeEpisodeFinished(self):
    self._model.setItem(self._current_index, self._change_episode_widget.episodeNumber(), tv_model.RAW_DATA_ROLE)
    self.tv_view.expand(self._current_index.parent())
    self._onSelectionChanged()

  def _onChangeSeasonFinished(self):
    item = self._change_season_widget.getItem()
    #utils.verifyType(data, tv_types.Season)
    self._manager.setItem(item.getInfo())
    self._model.setData(self._current_index, item, tv_model.RAW_DATA_ROLE)
    self.tv_view.expand(self._current_index)

# --------------------------------------------------------------------------------------------------------------------
class SearchSeasonParamsWidget(base_widget.BaseSearchParamsWidget):
  def __init__(self, parent=None):
    super(SearchSeasonParamsWidget, self).__init__(parent)
    uic.loadUi("ui/ui_SearchSeason.ui", self)
    self._setEditWidgets([self.season_spin_box, self.season_edit])

  def setItem(self, item):
    item = item or tv_types.Season("", tv_types.SeasonInfo(), tv_types.SourceFiles())
    self.folder_edit.setText(file_helper.FileHelper.basename(item.input_folder))
    self.folder_edit.setToolTip(item.input_folder)
    self.season_spin_box.setValue(item.getInfo().season_num)
    self.season_edit.setText(item.getInfo().show_name)
    self.season_edit.selectAll()

  def getSearchParams(self):
    return tv_types.TvSearchParams(utils.toString(self.season_edit.text()), self.season_spin_box.value())

# --------------------------------------------------------------------------------------------------------------------
class EditSeasonInfoWidget(base_widget.BaseEditInfoWidget):
  """ The widget allows the user to search and modify tv info. """
  def __init__(self, search_widget, parent=None):
    super(EditSeasonInfoWidget, self).__init__(parent)
    uic.loadUi("ui/ui_EditSeason.ui", self)
    self.setWindowModality(True)

    self.add_button.clicked.connect(self._add)
    self.remove_button.clicked.connect(self._remove)
    self.up_button.clicked.connect(self._moveUp)
    self.down_button.clicked.connect(self._moveDown)
    self.episode_table.cellClicked.connect(self._onSelectionChanged)
    self.index_spin_box.valueChanged.connect(self._updateColumnHeaders)
    self._search_widget = search_widget

  def _moveDown(self):
    currentItem = self.episode_table.currentItem()
    utils.verify(currentItem, "Must have current item to get here")
    nextItem = self.episode_table.item(currentItem.row() + 1, _TITLE_COLUMN)
    temp = nextItem.text()
    nextItem.setText(currentItem.text())
    currentItem.setText(temp)
    self.episode_table.setCurrentItem(nextItem)
    self._onSelectionChanged()

  def _moveUp(self):
    currentItem = self.episode_table.currentItem()
    utils.verify(currentItem, "Must have current item to get here")
    nextItem = self.episode_table.item(currentItem.row() - 1, _TITLE_COLUMN)
    temp = nextItem.text()
    nextItem.setText(currentItem.text())
    currentItem.setText(temp)
    self.episode_table.setCurrentItem(nextItem)
    self._onSelectionChanged()

  def _add(self):
    currentItem = self.episode_table.currentItem()
    row = currentItem.row() if currentItem else self.episode_table.rowCount()
    item = QtGui.QTableWidgetItem("")
    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
    #self.episode_table.setRowCount(self.episode_table.rowCount() + 1)
    self.episode_table.insertRow(row)
    self.episode_table.setItem(row, _TITLE_COLUMN, item)
    self._onSelectionChanged()
    self._updateColumnHeaders()

  def _remove(self):
    currentItem = self.episode_table.currentItem()
    utils.verify(currentItem, "Must have current item to get here")
    self.episode_table.removeRow(currentItem.row())
    self._onSelectionChanged()
    self._updateColumnHeaders()

  def _updateColumnHeaders(self):
    startIndex = self.index_spin_box.value()
    rowCount = self.episode_table.rowCount()
    self.episode_table.setVerticalHeaderLabels([str(i) for i in range(startIndex, rowCount + startIndex)])

  def setInfo(self, info):
    #utils.verifyType(info, tv_types.SeasonInfo)
    info = info or tv_types.SeasonInfo()
    self.episode_table.clearContents()

    minValue = min([ep.ep_num for ep in info.episodes] or [0])
    maxValue = max([ep.ep_num for ep in info.episodes] or [-1])
    self.index_spin_box.setValue(minValue)

    ep_nums = [i for i in range(minValue, maxValue + 1)]
    self.episode_table.setRowCount(len(ep_nums))
    for i, ep_num in enumerate(ep_nums):
      ep = info.getEpisodeByEpisodeNum(ep_num)
      item = QtGui.QTableWidgetItem(ep.ep_name)
      item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
      self.episode_table.setItem(i, _TITLE_COLUMN, item)
    self._onSelectionChanged()

  def getInfo(self):
    search_params = self._search_widget.getSearchParams()
    info = tv_types.SeasonInfo(search_params.show_name, search_params.season_num)
    startIndex = self.index_spin_box.value()
    for i in range(self.episode_table.rowCount()):
      ep_name = self.episode_table.item(i, _TITLE_COLUMN)
      info.episodes.append(tv_types.EpisodeInfo(i + startIndex, utils.toString(ep_name.text())))
    return info

  def _onSelectionChanged(self):
    currentIndex = self.episode_table.currentItem().row() if self.episode_table.currentItem() else -1
    self.remove_button.setEnabled(currentIndex != -1)
    self.up_button.setEnabled(currentIndex >= 1)
    self.down_button.setEnabled((currentIndex + 1) < self.episode_table.rowCount())

# --------------------------------------------------------------------------------------------------------------------
class EditSeasonItemWidget(base_widget.EditItemWidget):
  def __init__(self, holder, parent=None):
    search_params = SearchSeasonParamsWidget(parent)
    super(EditSeasonItemWidget, self).__init__(
        base_types.TV_MODE, holder, search_params, EditSeasonInfoWidget(search_params, parent), parent)

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

  def setItem(self, ssn, ep):
    """ Fill the dialog with the data prior to being shown """
    #utils.verifyType(ssn, tv_types.Season)
    #utils.verifyType(ep, tv_types.EpisodeRenameItem)
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
