# -*-coding:utf-8-*-

import os
import sys
import typing
import pickle
import io
import csv
from time import gmtime, strftime, localtime
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui
from PyQt5.QtCore import *

import common_util as co
from widgets import *


form_class = uic.loadUiType("./resource/mainwindow.ui")[0]

# base_data = [['00', '01', '02'],
#              ['10', '11', '12'],
#              ['20', '21', '22'],
#              ]
default_data = [[]]


class Data:
    def __init__(self, r = 0, c = 0):
        # these are needed on commands undo
        self.r = r
        self.c = c

    def is_data(self):
        return False

    def is_at(self, index):
        return self.r == index.row() and self.c == index.column()


class NoteData(Data):
    def __init__(self, r = 0, c = 0, content = ''):
        super().__init__(r, c)
        self.content = content

    def is_data(self):
        return True


class StyleData(Data):
    def __init__(self, r = 0, c = 0, bgcolor = None):
        super().__init__(r, c)
        self.bgcolor = bgcolor


class NoteModel(QAbstractTableModel):
    def __init__(self, src_data, undostack):
        super().__init__()
        self.undostack = undostack
        self.init_src_data(src_data)

    def init_src_data(self, input):
        self.src_data = [[None for c in range(len(input[r]))] for r in range(len(input))]
        self.src_style = [[None for c in range(len(input[r]))] for r in range(len(input))]

        for r in range(len(input)):
            for c in range(len(input[r])):
                self.src_data[r][c] = input[r][c]

    def get_src_data(self):
        return self.src_data

    def data_at(self, index):
        return self.src_data[index.row()][index.column()]

    def style_at(self, index):
        return self.src_style[index.row()][index.column()]

    def set_data_at(self, index, content):
        self.src_data[index.row()][index.column()] = NoteData(index.row(), index.column(), content)
        self.dataChanged.emit(index, index)

    def set_style_at(self, index, bgcolor = None):
        self.src_style[index.row()][index.column()] = StyleData(index.row(), index.column(), bgcolor)
        self.dataChanged.emit(index, index)

    def del_data_at(self, index):
        self.src_data[index.row()][index.column()] = None
        self.dataChanged.emit(index, index)

    def del_style_at(self, index):
        self.src_style[index.row()][index.column()] = None
        self.dataChanged.emit(index, index)

    def has_data_at(self, index):
        return self.data_at(index) is not None

    def has_style_at(self, index):
        return self.style_at(index) is not None

    def rowCount(self, parent: QModelIndex = ...):
        return len(self.src_data)

    def columnCount(self, parent: QModelIndex = ...):
        return len(self.src_data[0])

    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid():
            return QVariant()

        data = self.data_at(index)
        style = self.style_at(index)

        if role == Qt.DisplayRole:
            if data:
                return QVariant(data.content)
        elif role == Qt.BackgroundRole:
            if style and style.bgcolor:
                return QVariant(QtGui.QBrush(style.bgcolor))

        return QVariant()

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled

        return QAbstractTableModel.flags(self, index) | Qt.ItemIsEditable

    def setData(self, index: QModelIndex, value: typing.Any, role: int = ...):
        if index.isValid() and role == Qt.EditRole:
            if value == '':
                if self.has_data_at(index):
                    self.del_data_at(index)
                    return False
            cmd = SetDataCommand(index, value)
            self.undostack.push(cmd)
            self.dataChanged.emit(index, index)
            return True
        return False

    def emit_all_data_changed(self):
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), self.columnCount()))

    def insert_all_row(self, from_index, rows = 1):
        for r in range(self.rowCount()-1, from_index.row(), -1):
            for c in range(self.columnCount()):
                self.src_data[r][c] = self.src_data[r-1][c]
                self.src_data[r-1][c] = None

        self.emit_all_data_changed()

    def delete_all_row(self, from_index, rows = 1):
        for r in range(from_index.row(), self.rowCount()):
            for c in range(self.columnCount()):
                if r+1 < self.rowCount():
                    self.src_data[r][c] = self.src_data[r+1][c]
                    self.src_data[r+1][c] = None

        self.emit_all_data_changed()

    def is_data_row(self, row):
        for c in range(self.columnCount()):
            if self.src_data[row][c]:
                # this is for bug of paste
                if self.src_data[row][c] != '':
                    return True
        return False

    def is_data_col(self, col):
        for r in range(self.rowCount()):
            if self.src_data[r][col]:
                # this is for bug of paste
                if self.src_data[r][col]:
                    return True
        return False

    def change_row_count(self, count_to):
        if self.rowCount() < count_to:
            for r in range(self.rowCount(), count_to):
                self.src_data.append([None for _ in range(self.columnCount())])
        elif self.rowCount() > count_to:
            for r in range(count_to, self.rowCount()):
                if self.is_data_row(r):
                    return False
            for r in range(self.rowCount(), count_to, -1):
                self.src_data.pop()
        else:
            pass

        self.layoutChanged.emit()
        return True

    def change_col_count(self, count_to):
        cur_col_cnt = self.columnCount()
        if cur_col_cnt < count_to:
            for r in range(self.rowCount()):
                for c in range(cur_col_cnt, count_to):
                    self.src_data[r].append(None)
        elif cur_col_cnt > count_to:
            for c in range(count_to, cur_col_cnt):
                if self.is_data_col(c):
                    return False
            for r in range(self.rowCount()):
                for c in range(cur_col_cnt, count_to, -1):
                    self.src_data[r].pop()
        else:
            pass

        self.layoutChanged.emit()
        return True


class JobModel(NoteModel):
    def __init__(self, src_data, undostack):
        super().__init__(src_data, undostack)
        self.check_col = 4

    def parent_job_index(self, index):
        left_c = index.column() - 1
        for r in range(index.row(), -1, -1):
            i = self.index(r, left_c)
            if self.index(r, left_c).data():
                return i
        return None

    def children_job_indexes(self, index):
        results = []
        for r in range(index.row() + 1, self.rowCount()):
            is_neighbor = self.index(r, index.column()).data() is not None
            if is_neighbor:
                break
            i = self.index(r, index.column() + 1)
            if self.index(r, index.column() + 1).data():
                results.append(i)
        return results

    def update_checker(self, index):
        if index.column() == self.check_col:
            return

        if not index or not index.isValid():
            return
        print('update_checker ({}:{})'.format(index.row(), index.column()))

        children_indexes = self.children_job_indexes(index)
        is_all_complete = True
        is_progressing = False
        for i in children_indexes:
            checker = self.rel_checker(i)
            if checker != 'o':
                is_all_complete = False
            if checker in ('o', '>'):
                is_progressing = True
        if is_all_complete:
            self.set_checker(index.row(), 'o')
        elif is_progressing:
            self.set_checker(index.row(), '>')
        else:
            self.set_checker(index.row(), None)

    def checker(self, row):
        return self.data_at(self.index(row, self.check_col)).content

    def set_checker(self, row, checker = None):
        if checker:
            i = self.index(row, self.check_col)
            self.set_data_at(self.index(row, self.check_col), checker)
        else:
            self.del_data_at(self.index(row, self.check_col))

        self.update_checker(self.parent_job_index(self.first_data_index_from_checker(row)))

    def first_data_index_from_checker(self, checker_row):
        for c in range(self.check_col + 1, self.columnCount()):
            i = self.index(checker_row, c)
            if i.data():
                return i
        return None

    def rel_checker(self, index):
        data = self.data_at(self.index(index.row(), self.check_col))
        if data:
            return data.content
        else:
            return None


class NoteDataDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()

        self.color_complete = Qt.green
        self.color_blank = QtGui.QColor(230, 230, 230)
        self.color_end = Qt.darkCyan

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex):
        return super(NoteDataDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        curr_content = index.data(Qt.EditRole) or index.data(Qt.DisplayRole)
        editor.setText(curr_content)

    def has_left_data(self, index):
        for c in range(index.column()-1, index.model().check_col, -1):
            if index.model().index(index.row(), c).data():
                return True
        return False

    def is_checker_pos(self, index):
        if index.column() <= index.model().check_col:
            return False
        r_index = index.model().index(index.row(), index.column() + 1)
        if r_index.data() and not self.has_left_data(index):
            return True
        return False

    def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QModelIndex):
        if index.row() == index.model().rowCount() - 1 \
                or index.column() == index.model().columnCount() - 1:
            painter.fillRect(option.rect, self.color_end)
        if index.column() == index.model().check_col:
            painter.fillRect(option.rect, Qt.black)
        if index.row() == 0:
            painter.fillRect(option.rect, Qt.yellow)

        # # test : checker on left of data
        # if self.is_checker_pos(index):
        #     painter.fillRect(option.rect, Qt.black)

        if index.data():
            # if index.data(Qt.BackgroundRole):
            #     painter.fillRect(option.rect, index.data(Qt.BackgroundRole))

            fm = QtGui.QFontMetrics(option.font)
            fh = fm.height() - fm.descent()
            fw = fm.boundingRect(index.data()).width() + 10
            box_w = fw if fw > option.rect.width() else option.rect.width()

            text_rect = QRect(option.rect)
            text_rect.setWidth(box_w)
            o_pen = painter.pen()
            check_col = index.model().check_col
            if index.model().index(index.row(), check_col).data() == 'o':
                painter.fillRect(text_rect, self.color_complete)
            elif index.model().index(index.row(), check_col).data() == '>':
                painter.fillRect(text_rect, Qt.blue)
                painter.setPen(Qt.white)
            elif index.model().index(index.row(), check_col).data() == 'x':
                painter.fillRect(text_rect, Qt.red)
                painter.setPen(Qt.white)
            elif index.model().index(index.row(), check_col).data() == None:
                painter.fillRect(text_rect, self.color_blank)

            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            # fm = QtGui.QFontMetrics(option.font)
            # fh = fm.height() - fm.descent()
            painter.drawText(option.rect.x(), option.rect.y() + fh, index.data())
            # fw = fm.boundingRect(index.data()).width()
            # # sample cancel line
            # painter.drawLine(QPoint(option.rect.x(), option.rect.y() + 20), QPoint(option.rect.x() + fw, option.rect.y() + 20))

            painter.setPen(o_pen)
        else:
            # # don't know why this is needed. to avoid automatically fill rect with styledata in super
            # if index.data(Qt.BackgroundRole):
            #     return
            QStyledItemDelegate.paint(self, painter, option, index)


class NoteStyleDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QModelIndex):
        if index.data():
            if index.data(Qt.BackgroundRole):
                painter.fillRect(option.rect, index.data(Qt.BackgroundRole))
        else:
            QStyledItemDelegate.paint(self, painter, option, index)


class NoteView(QTableView):
    def __init__(self):
        super().__init__()
        self.row_h = 0
        self.col_w = 0

    def set_cell_size(self, w, h):
        self.row_h = h
        self.col_w = w

    def setModel(self, model: QAbstractItemModel):
        super(NoteView, self).setModel(model)
        self.apply_cell_size()

    def apply_cell_size(self):
        for r in range(self.model().rowCount()):
            self.setRowHeight(r, self.row_h)
        for c in range(self.model().columnCount()):
            self.setColumnWidth(c, self.col_w)


class NoteDataView(NoteView):
    def __init__(self):
        super().__init__()

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        key = e.key()
        mods = QApplication.keyboardModifiers()
        if key == Qt.Key_Return:
            if mods == Qt.ControlModifier:
                self.enter_edit_mode()
            elif mods == Qt.ShiftModifier:
                self.move_to_prev_row()
            else:
                self.move_to_next_row()
            e.accept()
        # ignore keys
        elif key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right) and mods == Qt.ControlModifier:
            e.ignore()
        elif key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right) and \
                mods == Qt.ControlModifier | Qt.ShiftModifier:
            e.ignore()
        elif key in (Qt.Key_Delete,):
            e.ignore()
        else:
            super(NoteView, self).keyPressEvent(e)

    def currentChanged(self, current: QModelIndex, previous: QModelIndex):
        r = previous.row()
        for c in range(self.model().columnCount()):
            i = self.model().index(r, c)
            if self.model().data(i):
                self.update(i)
        super().currentChanged(current, previous)

    def set_cell_font_size(self, font_size):
        fs = int(font_size) if font_size.isdigit() else 0

        if fs > 0:
            view_font = QtGui.QFont()
            view_font.setPointSize(fs)
            self.setFont(view_font)

    def enter_edit_mode(self):
        self.edit(self.currentIndex())

    def move_to_prev_row(self):
        cur = self.currentIndex()
        self.setCurrentIndex(self.model().index(cur.row() - 1, cur.column()))

    def move_to_next_row(self):
        cur = self.currentIndex()
        self.setCurrentIndex(self.model().index(cur.row() + 1, cur.column()))


default_list_data = [[None for c in range(50)] for r in range(100)]


# class MainWindow(QMainWindow, form_class):
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.init_focus_policy()
        self.init_signal_slots()

        self.undostack = QUndoStack()
        self.curr_path = None

        self.init_views()

        self.open_last_file()

    def setup_ui(self):
        self.setGeometry(100, 100, 800, 600)

        gridlayout = QGridLayout()
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(gridlayout)

        settingLayout = QHBoxLayout()
        self.txt_row_count = LabeledLineEdit('row', 0)
        self.txt_col_count = LabeledLineEdit('col', 0)
        self.txt_cell_width = LabeledLineEdit('cell width', co.load_settings('col_width', 50))
        self.txt_cell_height = LabeledLineEdit('cell height', co.load_settings('row_height', 30))
        self.txt_cell_font_size = LabeledLineEdit('font size', co.load_settings('cell_font_size', 12))
        settingLayout.addWidget(self.txt_row_count)
        settingLayout.addWidget(self.txt_col_count)
        settingLayout.addWidget(self.txt_cell_width)
        settingLayout.addWidget(self.txt_cell_height)
        settingLayout.addWidget(self.txt_cell_font_size)

        self.txt_path = QLineEdit()

        buttonlayout = QHBoxLayout()
        self.btn_open = QPushButton('open')
        self.btn_save = QPushButton('save')
        self.btn_save_as = QPushButton('save as')
        self.btn_new = QPushButton('new')
        self.btn_bg_color = QPushButton('b-color')
        self.btn_clear_bg_color = QPushButton('clear b-color')
        buttonlayout.addWidget(self.btn_open)
        buttonlayout.addWidget(self.btn_save)
        buttonlayout.addWidget(self.btn_save_as)
        buttonlayout.addWidget(self.btn_new)
        buttonlayout.addWidget(self.btn_bg_color)
        buttonlayout.addWidget(self.btn_clear_bg_color)

        gridlayout.addLayout(settingLayout, 0, 0)
        gridlayout.addWidget(self.txt_path, 1, 0)
        gridlayout.addLayout(buttonlayout, 2, 0)

        self.top_view = NoteDataView()
        self.top_view.horizontalScrollBar().setVisible(False)
        self.top_view.verticalScrollBar().setVisible(False)
        # self.top_view.verticalHeader().setVisible(False)
        self.top_view.setMaximumHeight(100)
        # self.top_view.setStyleSheet('QTableView:item {background: yellow}')
        gridlayout.addWidget(self.top_view, 3, 0)

        self.style_view = None
        # self.style_view = NoteView()
        # self.style_view.horizontalHeader().setVisible(False)
        # self.style_view.verticalHeader().setVisible(False)
        # # self.style_view.setStyleSheet('* {background-color: yellow;; gridline-color: red}')
        # gridlayout.addWidget(self.style_view, 3, 0)

        self.view = NoteDataView()
        self.view.horizontalHeader().setVisible(False)
        # self.view.verticalHeader().setVisible(False)
        if self.style_view:
            self.view.setStyleSheet('* {background-color: transparent}')
        gridlayout.addWidget(self.view, 4, 0)

    def init_views(self):
        data_delegate = NoteDataDelegate()
        style_delegate = NoteStyleDelegate()

        self.top_view.setItemDelegate(data_delegate)
        self.top_view.set_cell_size(int(self.txt_cell_width.text()), int(self.txt_cell_height.text()))
        self.top_view.set_cell_font_size(self.txt_cell_font_size.text())

        if self.style_view:
            self.style_view.setItemDelegate(style_delegate)
            self.style_view.setModel(self.model)
            self.style_view.set_cell_size(int(self.txt_cell_width.text()), int(self.txt_cell_height.text()))

        self.view.setItemDelegate(data_delegate)
        self.view.setShowGrid(False)
        self.view.set_cell_size(int(self.txt_cell_width.text()), int(self.txt_cell_height.text()))
        self.view.set_cell_font_size(self.txt_cell_font_size.text())

        self.view.horizontalScrollBar().valueChanged.connect(self.sync_hscroll)
        self.view.verticalScrollBar().valueChanged.connect(self.sync_vscroll)

    def init_signal_slots(self):
        self.txt_row_count.return_pressed.connect(self.update_model_row_count)
        self.txt_col_count.return_pressed.connect(self.update_model_col_count)
        self.txt_cell_width.return_pressed.connect(self.set_all_column_width)
        self.txt_cell_height.return_pressed.connect(self.set_all_row_height)
        self.txt_cell_font_size.return_pressed.connect(self.view.set_cell_font_size)
        self.btn_open.clicked.connect(self.open)
        self.btn_save.clicked.connect(lambda state: self.save(self.curr_path))
        self.btn_save_as.clicked.connect(lambda state: self.save())
        self.btn_new.clicked.connect(self.create_new)
        self.btn_bg_color.clicked.connect(self.set_bgcolor)
        self.btn_clear_bg_color.clicked.connect(self.clear_bgcolor)

    def open_last_file(self):
        self.open(co.load_settings('last_file'))

    def sync_hscroll(self, value):
        self.top_view.horizontalScrollBar().setValue(value)
        if self.style_view:
            self.style_view.horizontalScrollBar().setValue(value)

    def sync_vscroll(self, value):
        if self.style_view:
            self.style_view.verticalScrollBar().setValue(value)

    def init_focus_policy(self):
        self.txt_cell_width.setFocusPolicy(Qt.ClickFocus)
        self.txt_cell_height.setFocusPolicy(Qt.ClickFocus)
        self.txt_cell_font_size.setFocusPolicy(Qt.ClickFocus)
        self.txt_path.setFocusPolicy(Qt.NoFocus)
        self.top_view.setFocusPolicy(Qt.NoFocus)

        self.view.setFocus()

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        key = e.key()
        mod = QApplication.keyboardModifiers()
        if key == Qt.Key_S and mod == Qt.ControlModifier:
            self.save(self.curr_path)
            e.accept()
        elif key == Qt.Key_Delete:
            self.delete_selected()
            e.accept()
        elif key == Qt.Key_I and mod == Qt.ControlModifier:
            self.insert_all_row()
            e.accept()
        elif key == Qt.Key_K and mod == Qt.ControlModifier:
            self.delete_all_row()
            e.accept()
        elif key == Qt.Key_O and mod == Qt.ControlModifier:
            # self.insert_sel_col()
            e.accept()
        elif key == Qt.Key_L and mod == Qt.ControlModifier:
            # self.delete_all_row()
            e.accept()
        elif key == Qt.Key_C and mod == Qt.ControlModifier:
            self.copy_to_clipboard()
            e.accept()
        elif key == Qt.Key_X and mod == Qt.ControlModifier:
            self.copy_to_clipboard()
            self.delete_selected()
            e.accept()
        elif key == Qt.Key_V and mod == Qt.ControlModifier:
            self.paste_from_clipboard()
            e.accept()
        elif key == Qt.Key_Z and mod == Qt.ControlModifier:
            self.undostack.undo()
            e.accept()
        elif key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Right, Qt.Key_Left) and mod == Qt.ControlModifier:
            self.move_to_first_data(key)
            e.accept()
        elif key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Right, Qt.Key_Left)\
                and mod == Qt.ControlModifier | Qt.ShiftModifier:
            self.move_to_end(key)
        else:
            e.ignore()
            super().keyPressEvent(e)

    def closeEvent(self, e: QtGui.QCloseEvent):
        co.save_settings('last_row', self.view.currentIndex().row())
        co.save_settings('last_col', self.view.currentIndex().column())

    def load_model_from_file(self, path):
        if not path:
            return None

        if not os.path.exists(path):
            return None

        with open(path, 'rb') as f:
            model = JobModel(pickle.load(f), self.undostack)
            return model

    def update_model_row_count(self, count):
        ok = self.model.change_row_count(int(count))
        if ok:
            self.view.apply_cell_size()
        else:
            QMessageBox.warning(self, 'fail', 'some row has data')

    def update_model_col_count(self, count):
        if not self.model.change_col_count(int(count)):
            QMessageBox.warning(self, 'fail', 'some row has data')

    def set_all_column_width(self, width):
        w = int(width) if width.isdigit() else 0
        if w > 0 and w <= 100:
            for c in range(self.model.columnCount()):
                self.view.setColumnWidth(c, w)
                self.top_view.setColumnWidth(c, w)

    def set_all_row_height(self, height):
        h = int(height) if height.isdigit() else 0
        if h > 0 and h <= 100:
            for r in range(self.model.rowCount()):
                self.view.setRowHeight(r, h)
                self.top_view.setRowHeight(r, h)

    def move_to_last_index(self):
        last_index = self.model.index(co.load_settings('last_row', 0), co.load_settings('last_col', 0))
        self.view.setCurrentIndex(last_index)
        if self.style_view:
            self.style_view.setCurrentIndex(last_index)

    def show_model_row_col(self):
        self.txt_row_count.set_text(self.model.rowCount())
        self.txt_col_count.set_text(self.model.columnCount())

    def open(self, path = None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, 'select open file')

        model = self.load_model_from_file(path)
        if model:
            self.model = model
            self.txt_path.setText(path)
            self.curr_path = path
            co.save_settings('last_file', self.curr_path)

            self.view.setModel(self.model)
            self.top_view.setModel(self.model)

            self.move_to_last_index()
            self.show_model_row_col()
        else:
            QMessageBox.warning(self, 'open', "couldn't find file")

    def save(self, path = None):
        is_new_save = path is None
        if is_new_save:
            path, _ = QFileDialog.getSaveFileName(self, 'select save file')

        with open(path, 'wb') as f:
            pickle.dump(self.model.get_src_data(), f)

        if is_new_save:
            self.open(path)

        self.save_ui_settings()

        QMessageBox.information(self, 'save', 'saved')

    def create_new(self):
        self.model = JobModel(default_list_data, self.undostack)
        self.view.setModel(self.model)
        self.top_view.setModel(self.model)
        self.show_model_row_col()

    def save_ui_settings(self):
        co.save_settings('col_width', int(self.txt_cell_width.text()))
        co.save_settings('row_height', int(self.txt_cell_height.text()))
        co.save_settings('cell_font_size', int(self.txt_cell_font_size.text()))

    def delete_selected(self):
        cmd = DeleteCommand(self.view.selectionModel().selectedIndexes())
        self.undostack.push(cmd)
        # indexes = self.view.selectionModel().selectedIndexes()
        # for i in indexes:
        #     self.model.del_data_at(i)

    def insert_all_row(self):
        cur_i = self.view.currentIndex()
        cmd = InsertAllRowCommand(cur_i)
        self.undostack.push(cmd)

    def delete_all_row(self):
        cur_i = self.view.currentIndex()
        cmd = DeleteAllRowCommand(cur_i)
        self.undostack.push(cmd)

    def insert_sel_col(self):
        cmd = InsertColumnCommand(self.view.selectedIndexes())
        self.undostack.push(cmd)

    def delete_sel_col(self):
        cmd = DeleteColumnCommand(self.view.selectedIndexes())
        self.undostack.push(cmd)

    def set_bgcolor(self):
        color = QColorDialog.getColor()
        cur_i = self.view.currentIndex()
        self.model.set_style_at(cur_i, color)
        self.view.update(cur_i)

        for i in self.view.selectedIndexes():
            self.model.set_style_at(i, color)
            self.view.update(i)

    def clear_bgcolor(self):
        for i in self.view.selectedIndexes():
            self.model.del_style_at(i)
            self.view.update(i)

    def copy_to_clipboard(self):
        selections = self.view.selectedIndexes()
        if selections:
            rows = sorted(i.row() for i in selections)
            cols = sorted(i.column() for i in selections)
            rowcount = rows[-1] - rows[0] + 1
            colcount = cols[-1] - cols[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            for i in selections:
                row = i.row() - rows[0]
                col = i.column() - cols[0]
                table[row][col] = i.data()
            stream = io.StringIO()
            csv.writer(stream).writerows(table)
            QApplication.clipboard().setText(stream.getvalue())

    def paste_from_clipboard(self):
        text = QApplication.clipboard().text()
        cur_i = self.view.currentIndex()
        for r, l in enumerate(text.splitlines()):
            for c, t in enumerate(l.split(',')):
                if t == '':
                    continue
                i = self.model.index(cur_i.row() + r, cur_i.column() + c)
                self.model.set_data_at(i, t)

    def move_to_index(self, index):
        self.view.setCurrentIndex(index)
        self.view.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)

    def move_to_first_data(self, key):
        if key == Qt.Key_Up:
            cur_i = self.view.currentIndex()
            for r in range(cur_i.row() - 1, 0, -1):
                i = self.model.index(r, cur_i.column())
                if i.data():
                    self.move_to_index(i)
                    return
        elif key == Qt.Key_Down:
            cur_i = self.view.currentIndex()
            for r in range(cur_i.row() + 1, self.model.rowCount()):
                i = self.model.index(r, cur_i.column())
                if i.data():
                    self.move_to_index(i)
                    return
        elif key == Qt.Key_Left:
            cur_i = self.view.currentIndex()
            for c in range(cur_i.column() - 1, 0, -1):
                i = self.model.index(cur_i.row(), c)
                if i.data():
                    self.move_to_index(i)
                    return
        elif key == Qt.Key_Right:
            cur_i = self.view.currentIndex()
            for c in range(cur_i.column() + 1, self.model.columnCount()):
                i = self.model.index(cur_i.row(), c)
                if i.data():
                    self.move_to_index(i)
                    return

    def move_to_end(self, key):
        cur_i = self.view.currentIndex()
        if key == Qt.Key_Up:
            self.move_to_index(self.model.index(0, cur_i.column()))
        elif key == Qt.Key_Down:
            self.move_to_index(self.model.index(self.model.rowCount() - 1, cur_i.column()))
        elif key == Qt.Key_Left:
            self.move_to_index(self.model.index(cur_i.row(), 0))
        elif key == Qt.Key_Right:
            self.move_to_index(self.model.index(cur_i.row(), self.model.columnCount() - 1))


class SetDataCommand(QUndoCommand):
    def __init__(self, index, value):
        super().__init__('set data')

        self.model = index.model()
        self.index = index
        self.new_value = value
        self.old_value = None

    def redo(self):
        old_data = self.model.data_at(self.index)
        if old_data:
            self.old_value = old_data.content
        if self.index.column() == self.model.check_col:
            self.model.set_checker(self.index.row(), self.new_value)
        else:
            self.model.set_data_at(self.index, self.new_value)

    def undo(self):
        if self.old_value:
            if self.index.column() == self.model.check_col:
                self.model.set_checker(self.index.row(), self.old_value)
            else:
                self.model.set_data_at(self.index, self.old_value)
        else:
            if self.index.column() == self.model.check_col:
                self.model.set_checker(self.index.row())
            else:
                self.model.del_data_at(self.index)


class DeleteCommand(QUndoCommand):
    def __init__(self, indexes):
        super().__init__('delete')
        self.indexes = indexes
        if len(indexes) > 0:
            self.model = indexes[0].model()
        self.deleted_data = []

    def redo(self):
        for i in self.indexes:
            d = self.model.data_at(i)
            if d:
                self.deleted_data.append(d)
                if i.column() == self.model.check_col:
                    self.model.set_checker(i.row(), None)
                else:
                    self.model.del_data_at(i)

    def undo(self):
        for e in self.deleted_data:
            if e.c == self.model.check_col:
                self.model.set_checker(e.r, e.content)
            else:
                self.model.set_data_at(self.model.index(e.r, e.c), e.content)
        self.deleted_data.clear()


class InsertAllRowCommand(QUndoCommand):
    def __init__(self, index):
        super().__init__('insert all row')

        self.index = index

    def redo(self):
        self.index.model().insert_all_row(self.index)

    def undo(self):
        self.index.model().delete_all_row(self.index)


class DeleteAllRowCommand(QUndoCommand):
    def __init__(self, index):
        super().__init__('delete all row')

        self.index = index
        self.deleted_data = []

    def redo(self):
        r = self.index.row()
        model = self.index.model()
        for c in range(model.columnCount()):
            data = model.data_at(model.index(r, c))
            if data:
                self.deleted_data.append(data)

        self.index.model().delete_all_row(self.index)

    def undo(self):
        self.index.model().insert_all_row(self.index)

        model = self.index.model()
        for e in self.deleted_data:
            model.set_data_at(model.index(e.r, e.c), e.content)
        self.deleted_data.clear()


class InsertColumnCommand(QUndoCommand):
    def __init__(self, indexes):
        super(InsertColumnCommand, self).__init__('insert columns')

        self.model = indexes[0].model()
        self.indexes = indexes
        self.inserted_data = []
        self.deleted_data = []

    def redo(self):
        for i in self.indexes:
            r, cur_c = i.row(), i.column()
            model = i.model()
            try:
                for c in range(model.columnCount(), cur_c+1, -1):
                    left_d = model.data_at(model.index(r, c-1))
                    if left_d:
                        model.set_data_at(model.index(r, c), left_d.content)
                        self.inserted_data.append(model.data_at(model.index(r, c)))
                        model.del_data_at(model.index(r, c-1))
                        self.deleted_data.append(left_d)
            except Exception as err:
                print(str(err))

    def undo(self):
        for e in self.inserted_data:
            self.model.del_data_at(e.r, e.c)
        for e in self.deleted_data:
            self.model.set_data_at(e.r, e.c, e)

        self.inserted_data.clear()
        self.deleted_data.clear()


class DeleteColumnCommand(QUndoCommand):
    def __init__(self, indexes):
        super(DeleteColumnCommand, self).__init__('delete columns')

    def redo(self):
        pass

    def undo(self):
        pass


def catch_exceptions(self, t, val, tb):
    QMessageBox.critical(None, 'exception', '{}'.format(t))
    old_hook(t, val, tb)


if __name__ == "__main__":
    old_hook = sys.excepthook
    sys.excepthook = catch_exceptions

    app = QApplication(sys.argv)

    mywindow = MainWindow()
    mywindow.show()
    app.exec_()
