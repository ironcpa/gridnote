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


class NoteEditDelegate(QStyledItemDelegate):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex):
        return super(NoteEditDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        curr_content = index.data(Qt.EditRole) or index.data(Qt.DisplayRole)
        editor.setText(curr_content)

    def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QModelIndex):
        if index.data():
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            clip_rect = self.clip_rect_on_row(option.rect, index)
            if clip_rect:
                painter.setClipRect(clip_rect)
            fm = QtGui.QFontMetrics(option.font)
            fh = fm.height() + fm.descent()
            painter.drawText(option.rect.x(), option.rect.y() + fh, index.data())
            # painter.drawText(clip_rect, Qt.AlignLeft | Qt.AlignVCenter, index.data())
        else:
            QStyledItemDelegate.paint(self, painter, option, index)

    def clip_rect_on_row(self, cur_rect, cur_index):
        ''' cur to first row has data '''
        r = cur_index.row()
        col_w = 50
        print('{}:{}={}'.format(cur_index.row(), cur_index.column(), cur_index.data()))
        for c in range(cur_index.column() + 1, self.model.columnCount()):
            i = self.model.index(r, c)
            if i.isValid() and i.data():
                rect = QRect(cur_rect.x(), cur_rect.y(), cur_rect.width() + (c - cur_index.column() - 1) * col_w,
                        cur_rect.height())
                print('\t1st right data, c={}, {}:{}={}, rect={},{},{},{}'.format((c - cur_index.column()), i.row(), i.column(), i.data(), rect.x(), rect.y(), rect.width(), rect.height()))
                return rect
        tc = self.model.columnCount()
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

        self.view.setModel(self.model)
        item_delegate = NoteEditDelegate(self.model)
        # item_delegate.setClipping(False)
        self.view.setItemDelegate(item_delegate)
        self.view.setModel(self.model)

        self.view.setShowGrid(False)
        for c in range(self.model.columnCount()):
            self.view.setColumnWidth(c, 50)

        self.btn_open.clicked.connect(self.open)
        self.btn_save.clicked.connect(lambda state: self.save(self.curr_path))
        self.btn_save_as.clicked.connect(lambda state: self.save())

    def setup_ui(self, dummy):
        self.setGeometry(100, 100, 800, 600)

        gridlayout = QGridLayout()
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(gridlayout)

        buttonlayout = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.btn_open = QPushButton('open')
        self.btn_save = QPushButton('save')
        self.btn_save_as = QPushButton('save as')
        buttonlayout.addWidget((self.txt_path))
        buttonlayout.addWidget(self.btn_open)
        buttonlayout.addWidget(self.btn_save)
        buttonlayout.addWidget(self.btn_save_as)

        gridlayout.addLayout(buttonlayout, 0, 0)

        # self.view = QTableView()
        self.view = NoteView()
        gridlayout.addWidget(self.view, 1, 0)

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        key = e.key()
        mod = QApplication.keyboardModifiers()
        if key == Qt.Key_S and mod == Qt.ControlModifier:
            self.save(self.curr_path)
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
