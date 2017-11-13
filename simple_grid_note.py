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
default_data = [[str(x), str(y)] for x in range(50000)
                for y in range(20)]


class Data:
    def __init__(self, r = 0, c = 0):
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
        self.max_row = 100
        self.max_col = 100
        self.src_data = [[None for _ in range(100)] for _ in range(100)]
        self.init_src_data(src_data)
        self.src_style = [[None for _ in range(100)] for _ in range(100)]

    def init_src_data(self, input):
        # # for legacy model : 1d list
        # for e in input_list:
        #     self.src_data[e.r][e.c] = e

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
        return self.max_row

    def columnCount(self, parent: QModelIndex = ...):
        return self.max_col

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

    def insert_all_row(self, from_index, rows = 1):
        for r in range(self.rowCount()-1, from_index.row(), -1):
            for c in range(self.columnCount()):
                self.src_data[r][c] = self.src_data[r-1][c]
                self.src_data[r-1][c] = None

        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), self.columnCount()))

    def delete_all_row(self, from_index, rows = 1):
        for r in range(from_index.row(), self.rowCount()):
            for c in range(self.columnCount()):
                if r+1 < self.rowCount():
                    self.src_data[r][c] = self.src_data[r+1][c]
                    self.src_data[r+1][c] = None

        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), self.columnCount()))


class NoteDataDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex):
        return super(NoteDataDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        curr_content = index.data(Qt.EditRole) or index.data(Qt.DisplayRole)
        editor.setText(curr_content)

    def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QModelIndex):
        if index.data():
            # if index.data(Qt.BackgroundRole):
            #     painter.fillRect(option.rect, index.data(Qt.BackgroundRole))

            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            fm = QtGui.QFontMetrics(option.font)
            fh = fm.height() - fm.descent()
            painter.drawText(option.rect.x(), option.rect.y() + fh, index.data())
            fw = fm.boundingRect(index.data()).width()
            # # sample cancel line
            # painter.drawLine(QPoint(option.rect.x(), option.rect.y() + 20), QPoint(option.rect.x() + fw, option.rect.y() + 20))
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

    def set_cell_size(self, w, h):
        for c in range(self.model().columnCount()):
            self.setColumnWidth(c, w)
            self.setRowHeight(c, h)


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
        elif key == Qt.Key_Up and mods == Qt.ControlModifier:
            e.ignore()
        elif key == Qt.Key_Down and mods == Qt.ControlModifier:
            e.ignore()
        elif key == Qt.Key_Left and mods == Qt.ControlModifier:
            e.ignore()
        elif key == Qt.Key_Right and mods == Qt.ControlModifier:
            e.ignore()
        else:
            e.ignore()
            super(NoteView, self).keyPressEvent(e)

    def currentChanged(self, current: QModelIndex, previous: QModelIndex):
        r = previous.row()
        for c in range(100):
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


default_list_data = [NoteData(0, 0, 'a'),
                     NoteData(0, 1, 'b'),
                     NoteData(1, 1, 'c'),
                     NoteData(3, 4, 'd')]


# class MainWindow(QMainWindow, form_class):
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui(self)
        self.init_focus_policy()

        self.undostack = QUndoStack()
        self.curr_path = None

        self.open(co.load_settings('last_file'))
        if not self.model:
            self.model = NoteModel(default_list_data)

        data_delegate = NoteDataDelegate()
        style_delegate = NoteStyleDelegate()

        self.top_view.setItemDelegate(data_delegate)
        self.top_view.setModel(self.model)
        self.top_view.set_cell_size(int(self.txt_cell_width.text()), int(self.txt_cell_height.text()))
        self.top_view.set_cell_font_size(self.txt_cell_font_size.text())
        # self.top_view.setShowGrid(False)

        if self.style_view:
            self.style_view.setItemDelegate(style_delegate)
            self.style_view.setModel(self.model)
            self.style_view.set_cell_size(int(self.txt_cell_width.text()), int(self.txt_cell_height.text()))

        self.view.setItemDelegate(data_delegate)
        self.view.setModel(self.model)
        last_index = self.model.index(co.load_settings('last_row', 0), co.load_settings('last_col', 0))
        self.view.setCurrentIndex(last_index)
        if self.style_view:
            self.style_view.setCurrentIndex(last_index)

        self.view.setShowGrid(False)
        self.view.set_cell_size(int(self.txt_cell_width.text()), int(self.txt_cell_height.text()))
        self.view.set_cell_font_size(self.txt_cell_font_size.text())

        self.txt_cell_width.edit_finished.connect(self.set_all_column_width)
        self.txt_cell_height.edit_finished.connect(self.set_all_row_height)
        self.txt_cell_font_size.edit_finished.connect(self.view.set_cell_font_size)

        self.btn_open.clicked.connect(self.open)
        self.btn_save.clicked.connect(lambda state: self.save(self.curr_path))
        self.btn_save_as.clicked.connect(lambda state: self.save())
        self.btn_bg_color.clicked.connect(self.set_bgcolor)
        self.btn_clear_bg_color.clicked.connect(self.clear_bgcolor)

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
        self.btn_clear_bg_color = QPushButton('clear b-color')
        buttonlayout.addWidget(self.txt_path)
        buttonlayout.addWidget(self.btn_open)
        buttonlayout.addWidget(self.btn_save)
        buttonlayout.addWidget(self.btn_save_as)
        buttonlayout.addWidget(self.btn_bg_color)
        buttonlayout.addWidget(self.btn_clear_bg_color)

        gridlayout.addLayout(settingLayout, 0, 0)
        gridlayout.addLayout(buttonlayout, 1, 0)

        self.top_view = NoteDataView()
        self.top_view.horizontalScrollBar().setVisible(False)
        self.top_view.verticalScrollBar().setVisible(False)
        self.top_view.verticalHeader().setVisible(False)
        self.top_view.setMaximumHeight(100)
        # self.top_view.setStyleSheet('QTableView:item {background: yellow}')
        gridlayout.addWidget(self.top_view, 2, 0)

        self.style_view = None
        # self.style_view = NoteView()
        # self.style_view.horizontalHeader().setVisible(False)
        # self.style_view.verticalHeader().setVisible(False)
        # # self.style_view.setStyleSheet('* {background-color: yellow;; gridline-color: red}')
        # gridlayout.addWidget(self.style_view, 3, 0)

        self.view = NoteDataView()
        self.view.horizontalHeader().setVisible(False)
        self.view.verticalHeader().setVisible(False)
        if self.style_view:
            self.view.setStyleSheet('* {background-color: transparent}')
        gridlayout.addWidget(self.view, 3, 0)

        self.view.horizontalScrollBar().valueChanged.connect(self.sync_hscroll)
        self.view.verticalScrollBar().valueChanged.connect(self.sync_vscroll)

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
        elif key == Qt.Key_C and mod == Qt.ControlModifier:
            self.copy_to_clipboard()
            e.accept()
        elif key == Qt.Key_V and mod == Qt.ControlModifier:
            self.paste_from_clipboard()
            e.accept()
        elif key == Qt.Key_Z and mod == Qt.ControlModifier:
            self.undostack.undo()
            e.accept()
        elif key == Qt.Key_Up and mod == Qt.ControlModifier:
            self.move_to_first_data(key)
            e.accept()
        elif key == Qt.Key_Down and mod == Qt.ControlModifier:
            self.move_to_first_data(key)
            e.accept()
        elif key == Qt.Key_Right and mod == Qt.ControlModifier:
            self.move_to_first_data(key)
            e.accept()
        elif key == Qt.Key_Left and mod == Qt.ControlModifier:
            self.move_to_first_data(key)
            e.accept()
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
            model = NoteModel(pickle.load(f), self.undostack)
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

        self.save_ui_settings()

        QMessageBox.information(self, 'save', 'saved')

    def save_ui_settings(self):
        co.save_settings('col_width', int(self.txt_cell_width.text()))
        co.save_settings('row_height', int(self.txt_cell_height.text()))
        co.save_settings('cell_font_size', int(self.txt_cell_font_size.text()))

    def delete_selected(self):
        indexes = self.view.selectionModel().selectedIndexes()
        for i in indexes:
            self.model.del_data_at(i)

    def insert_all_row(self):
        cur_i = self.view.currentIndex()
        cmd = InsertAllRowCommand(cur_i)
        self.undostack.push(cmd)

    def delete_all_row(self):
        cur_i = self.view.currentIndex()
        cmd = DeleteAllRowCommand(cur_i)
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
        self.model.set_data_at(self.index, self.new_value)

    def undo(self):
        if self.old_value:
            self.model.set_data_at(self.index, self.old_value)
        else:
            self.model.del_data_at(self.index)


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
