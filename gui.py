# -*-coding:utf-8-*-

import os
import sys
import typing
import pickle
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
default_data = [[str(x), str(y)] for x in range(50000)
                for y in range(20)]


class NoteData:
    def __init__(self, r = 0, c = 0, content = '', bgcolor = None):
        self.r = r
        self.c = c
        self.content = content
        self.bgcolor = bgcolor


class StyleData:
    def __init__(self, from_index, to_index, bgcolor = None, fgcolor = None ):
        self.from_index = from_index
        self.to_index = to_index
        self.bgcolor = bgcolor
        self.fgcolor = fgcolor


class NoteModel(QAbstractTableModel):
    def __init__(self, src_data):
        super().__init__()
        self.src_data = src_data
        self.max_row = 100
        self.max_col = 100

    def get_src_data(self):
        return self.src_data

    def data_at(self, index):
        for e in self.src_data:
            if e.r == index.row() and e.c == index.column():
                return e

    def set_data_at(self, index, value):
        data = self.data_at(index)
        if data:
            data.content = value
        else:
            self.src_data.append(NoteData(index.row(), index.column(), value))

    def del_data_at(self, index):
        for i, e in enumerate(self.src_data):
            if e.r == index.row() and e.c == index.column():
                del self.src_data[i]
                self.dataChanged.emit(index, index)
                return

    def has_data_at(self, index):
        return self.data_at(index) is not None

    def rowCount(self, parent: QModelIndex = ...):
        return self.max_row

    def columnCount(self, parent: QModelIndex = ...):
        return self.max_col

    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid():
            return QVariant()

        data = self.data_at(index)
        if not data:
            return QVariant()

        if role == Qt.DisplayRole:
            return QVariant(data.content)
        elif role == Qt.BackgroundRole:
            if data.bgcolor:
                return QVariant(QtGui.QBrush(data.bgcolor))

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
            self.set_data_at(index, value)
            self.dataChanged.emit(index, index)
            return True
        return False

    def insert_all_row(self, from_index, rows = 1):
        for e in self.src_data:
            if e.r >= from_index.row():
                e.r += rows

        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), self.columnCount()))

    def delete_all_row(self, from_index, rows = 1):
        for e in self.src_data:
            if e.r == from_index.row():
                self.src_data.remove(e)

        for e in self.src_data:
            if e.r > from_index.row():
                e.r -= rows

        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), self.columnCount()))


class NoteEditDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex):
        return super(NoteEditDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        curr_content = index.data(Qt.EditRole) or index.data(Qt.DisplayRole)
        editor.setText(curr_content)

    def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QModelIndex):
        if index.data():
            if index.data(Qt.BackgroundRole):
                painter.fillRect(option.rect, index.data(Qt.BackgroundRole))

            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            avail_rect = self.clip_rect_on_row(option.rect, index)
            # if avail_rect:
            #     painter.setClipRect(avail_rect)
            # fm = QtGui.QFontMetrics(option.font)
            # fh = fm.height() + fm.descent()
            # painter.drawText(option.rect.x(), option.rect.y() + fh, index.data())
            painter.drawText(avail_rect, Qt.AlignLeft | Qt.AlignVCenter, index.data())
        else:
            QStyledItemDelegate.paint(self, painter, option, index)

    def clip_rect_on_row(self, cur_rect, cur_index):
        model = cur_index.model()
        r = cur_index.row()
        col_w = 50
        for c in range(cur_index.column() + 1, model.columnCount()):
            i = model.index(r, c)
            if i.isValid() and i.data():
                rect = QRect(cur_rect.x(), cur_rect.y(), cur_rect.width() + (c - cur_index.column() - 1) * col_w,
                        cur_rect.height())
                return rect
        tc = model.columnCount()
        return QRect(cur_rect.x(), cur_rect.y(), cur_rect.width() * (tc - cur_index.column() - 1), cur_rect.height())


class NoteView(QTableView):
    def __init__(self):
        super().__init__()

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        key = e.key()
        mods = QApplication.keyboardModifiers()
        if key == Qt.Key_Return:
            # self.enter_edit_mode()
            if mods == Qt.ControlModifier:
                self.enter_edit_mode()
            elif mods == Qt.ShiftModifier:
                self.move_to_prev_row()
            else:
                self.move_to_next_row()
            e.accept()
        else:
            e.ignore()
        super(NoteView, self).keyPressEvent(e)

    def currentChanged(self, current: QModelIndex, previous: QModelIndex):
        self.update_clipable_cells(previous)
        super(NoteView, self).currentChanged(current, previous)

    def enter_edit_mode(self):
        self.edit(self.currentIndex())

    def move_to_prev_row(self):
        cur = self.currentIndex()
        self.setCurrentIndex(self.model().index(cur.row() - 1, cur.column()))

    def move_to_next_row(self):
        cur = self.currentIndex()
        self.setCurrentIndex(self.model().index(cur.row() + 1, cur.column()))

    def update_clipable_cells(self, base_index):
        for c in range(base_index.column() + 1):
            i = self.model().index(base_index.row(), c)
            self.update(i)


default_list_data = [NoteData(0, 0, 'a'),
                     NoteData(0, 1, 'b'),
                     NoteData(1, 1, 'c'),
                     NoteData(3, 4, 'd')]


# class MainWindow(QMainWindow, form_class):
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui(self)

        self.curr_path = None

        self.open(co.load_settings('last_file'))
        if not self.model:
            self.model = NoteModel(default_list_data)

        self.view.setItemDelegate(NoteEditDelegate())
        self.view.setModel(self.model)

        self.view.setShowGrid(False)
        for c in range(self.model.columnCount()):
            self.view.setColumnWidth(c, int(self.txt_cell_width.text()))
            self.view.setRowHeight(c, int(self.txt_cell_height.text()))
        self.set_all_font_size(self.txt_cell_font_size.text())

        self.txt_cell_width.edit_finished.connect(self.set_all_column_width)
        self.txt_cell_height.edit_finished.connect(self.set_all_row_height)
        self.txt_cell_font_size.edit_finished.connect(self.set_all_font_size)

        self.btn_open.clicked.connect(self.open)
        self.btn_save.clicked.connect(lambda state: self.save(self.curr_path))
        self.btn_save_as.clicked.connect(lambda state: self.save())
        self.btn_bg_color.clicked.connect(self.set_color)

    def setup_ui(self, dummy):
        self.setGeometry(100, 100, 800, 600)

        gridlayout = QGridLayout()
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(gridlayout)

        settingLayout = QHBoxLayout()
        self.txt_cell_width = LabeledLineEdit('cell width', co.load_settings('col_width', 50))
        self.txt_cell_height = LabeledLineEdit('cell height', co.load_settings('row_height', 30))
        self.txt_cell_font_size = LabeledLineEdit('font size', co.load_settings('cell_font_size', 12))
        settingLayout.addWidget(self.txt_cell_width)
        settingLayout.addWidget(self.txt_cell_height)
        settingLayout.addWidget(self.txt_cell_font_size)

        buttonlayout = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.btn_open = QPushButton('open')
        self.btn_save = QPushButton('save')
        self.btn_save_as = QPushButton('save as')
        self.btn_bg_color = QPushButton('b-color')
        buttonlayout.addWidget(self.txt_path)
        buttonlayout.addWidget(self.btn_open)
        buttonlayout.addWidget(self.btn_save)
        buttonlayout.addWidget(self.btn_save_as)
        buttonlayout.addWidget(self.btn_bg_color)

        gridlayout.addLayout(settingLayout, 0, 0)
        gridlayout.addLayout(buttonlayout, 1, 0)

        # self.view = QTableView()
        self.view = NoteView()
        gridlayout.addWidget(self.view, 2, 0)

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
        else:
            e.ignore()
        super().keyPressEvent(e)

    def load_model_from_file(self, path):
        if not path:
            return None

        if not os.path.exists(path):
            return None

        with open(path, 'rb') as f:
            model = NoteModel(pickle.load(f))
            return model

    def set_all_column_width(self, width):
        w = int(width) if width.isdigit() else 0
        if w > 0 and w <= 100:
            for c in range(self.model.columnCount()):
                self.view.setColumnWidth(c, w)

    def set_all_row_height(self, height):
        h = int(height) if height.isdigit() else 0
        if h > 0 and h <= 100:
            for r in range(self.model.rowCount()):
                self.view.setRowHeight(r, h)

    def set_all_font_size(self, font_size):
        fs = int(font_size) if font_size.isdigit() else 0

        if fs > 0:
            view_font = QtGui.QFont()
            view_font.setPointSize(fs)
            self.view.setFont(view_font)

    def open(self, path = None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, 'select open file')

        model = self.load_model_from_file(path)
        if model:
            self.model = model
            self.view.setModel(model)
            self.view.show()
            self.txt_path.setText(path)
            self.curr_path = path
            co.save_settings('last_file', self.curr_path)
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

        self.save_settings()

    def save_settings(self):
        co.save_settings('col_width', int(self.txt_cell_width.text()))
        co.save_settings('row_height', int(self.txt_cell_height.text()))
        co.save_settings('cell_font_size', int(self.txt_cell_font_size.text()))

    def delete_selected(self):
        indexes = self.view.selectionModel().selectedIndexes()
        for i in indexes:
            self.model.del_data_at(i)

    def insert_all_row(self):
        cur_i = self.view.currentIndex()
        self.model.insert_all_row(cur_i)

    def delete_all_row(self):
        cur_i = self.view.currentIndex()
        self.model.delete_all_row(cur_i)

    def set_color(self):
        color = QColorDialog.getColor()
        cur_i = self.view.currentIndex()
        self.model.data_at(cur_i).bgcolor = color
        self.view.update(cur_i)


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
