# -*-coding:utf-8-*-

import typing
import pickle
import io
import csv
from itertools import product
from datetime import datetime

from defines import StyledNoteData, Checker
import common_util as cu
from widgets import *


default_single_tab_data = [[None] * 50 for r in range(100)]
default_tabbed_data = [('default', default_single_tab_data)]
test_tabbed_data = [('1st page', default_single_tab_data),
                    ('2nd page', default_single_tab_data)]
test_tabbed_data[0][1][0][0] = StyledNoteData(0, 0, 'aaa')


class NoteModel(QAbstractTableModel):
    def __init__(self, src_data, undostack):
        super().__init__()
        self.undostack = undostack
        self.init_src_data(src_data)

    def init_src_data(self, input):
        self.src_data = [[None for c in range(len(input[r]))] for r in range(len(input))]

        for r in range(len(input)):
            for c in range(len(input[r])):
                self.src_data[r][c] = input[r][c]

    def get_src_data(self):
        return self.src_data

    def data_at(self, r, c):
        return self.src_data[r][c]

    def content_at(self, r, c):
        return self.data_at(r, c).content if self.data_at(r, c) else None

    def style_at(self, r, c):
        return self.data_at(r, c)

    def set_data_at(self, r, c, content):
        if not content:
            return

        self.src_data[r][c] = StyledNoteData(r, c, content)
        index = self.index(r, c)
        self.dataChanged.emit(index, index)

    def set_style_at(self, r, c, bgcolor = None):
        d = self.data_at(r, c)
        if d:
            d.bgcolor = bgcolor
        else:
            self.src_data[r][c] = StyledNoteData(r, c, '', bgcolor)
        index = self.index(r, c)
        self.dataChanged.emit(index, index)

    def del_data_at(self, r, c):
        self.src_data[r][c] = None
        index = self.index(r, c)
        self.dataChanged.emit(index, index)

    def del_style_at(self, r, c):
        d = self.data_at(r, c)
        if not d:
            return
        else:
            if d.content:
                d.bgcolor = None
            else:
                self.del_data_at(r, c)
        index = self.index(4, c)
        self.dataChanged.emit(index, index)

    def has_data_at(self, r, c):
        return self.data_at(r, c) is not None

    def has_style_at(self, r, c):
        return self.style_at(r, c) is not None

    def rowCount(self, parent: QModelIndex = ...):
        return len(self.src_data)

    def columnCount(self, parent: QModelIndex = ...):
        return len(self.src_data[0])

    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid():
            return QVariant()

        data = self.data_at(index.row(), index.column())

        if data:
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
            r = index.row()
            c = index.column()
            if value == '':
                if self.has_data_at(r, c):
                    self.del_data_at(r, c)
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

    def row_col_ranges(self):
        return product(range(self.rowCount()), range(self.columnCount()))

    def get_last_row(self):
        for r, c in product(range(self.rowCount() - 1, 0, -1), range(self.columnCount())):
            if self.data_at(r, c):
               return r
        return 0

    def clear(self):
        for r, c in self.row_col_ranges():
            self.src_data[r][c] = None

        self.layoutChanged.emit()


class JobModel(NoteModel):
    def __init__(self, src_data, undostack):
        super().__init__(src_data, undostack)
        self.date_col = 0
        self.check_col = 4
        self.job_start_col = self.check_col + 1

    def parent_job_index(self, index):
        if not index:
            return None

        left_c = index.column() - 1
        if left_c == self.check_col:
            return None

        for r in range(index.row(), -1, -1):
            i = self.index(r, left_c)
            if self.index(r, left_c).data():
                return i
        return None

    def children_job_indexes(self, index):
        results = []
        for r in range(index.row() + 1, self.rowCount()):
            '''imaginary root 고려'''
            is_next_date_row = r != index.row() + 1 and self.data_at(r, self.date_col) is not None
            is_neighbor = self.data_at(r, index.column()) is not None
            is_checker = index.column() is self.check_col
            if is_next_date_row:
                break
            if is_neighbor and not is_checker:
                break
            i = self.index(r, index.column() + 1)
            if self.index(r, index.column() + 1).data():
                results.append(i)
        return results

    def update_checker(self, index):
        if not index or not index.isValid():
            return
        if index.column() == self.check_col:
            return

        children_indexes = self.children_job_indexes(index)
        is_all_complete = True
        is_progressing = False
        for i in children_indexes:
            checker = self.checker(i.row())
            # if checker in ('-', 'm'):
            if checker in (Checker.IGNORE, Checker.MOVETO):
                continue
            # if checker != 'o':
            if checker != Checker.DONE:
                is_all_complete = False
            # if checker in ('o', '>'):
            if checker in (Checker.DONE, Checker.PROGRESS):
                is_progressing = True
        if is_all_complete:
            self.set_checker(index.row(), Checker.DONE)
        elif is_progressing:
            self.set_checker(index.row(), Checker.PROGRESS)
        else:
            self.set_checker(index.row(), None)

        self.layoutChanged.emit()

    def checker(self, row):
        d = self.content_at(row, self.check_col)
        if d:
            return Checker.get_def(d)
        else:
            return None

    def set_checker(self, row, checker = None):
        if checker:
            i = self.index(row, self.check_col)
            self.set_data_at(row, self.check_col, checker.str)
        else:
            self.del_data_at(row, self.check_col)

        self.update_checker(self.parent_job_index(self.first_data_index_from_checker(row)))

    def first_data_index_from_checker(self, checker_row):
        for c in range(self.check_col + 1, self.columnCount()):
            i = self.index(checker_row, c)
            if i.data():
                return i
        return None

    def get_latest_date_row(self):
        for r in range(self.rowCount() - 1, 0, -1):
            if self.data_at(r, self.date_col):
                return r
        return 0

    def find_child_indexes_with_checker(self, my_index, checker):
        founds = []

        my_index_is_content = my_index.column() >= self.job_start_col
        root_row = my_index.row() if my_index_is_content else my_index.row() - 1
        root_col = my_index.column() if my_index_is_content else self.job_start_col - 1
        root_index = self.index(root_row, root_col)

        if root_row < 0:
            return founds

        children = self.children_job_indexes(root_index)
        for i in children:
            if self.checker(i.row()) is checker:
                founds.append(i)
            child_founds = self.find_child_indexes_with_checker(i, checker)
            founds.extend(child_founds)

        print('\t', 'find_child...', cu.str_index(my_index))
        print('\t' * 2, 'root index:', cu.str_index(root_index))
        print('\t' * 2, 'children:', cu.str_indexes(self.children_job_indexes(root_index)))
        print('\t' * 2, 'founds:', cu.str_indexes(founds))
        return founds

    def collect_all_parent(self, index, coll_list):
        parent_i = self.parent_job_index(index)
        if not parent_i:
            return
        coll_list.append(parent_i.row())
        self.collect_all_parent(parent_i, coll_list)

    def add_copy_from_last_date(self, checker, *copy_checkers):
        checker_content_indexes = self.find_child_indexes_with_checker(self.index(self.get_latest_date_row(), self.date_col), checker)

        copy_rows = []
        for i in checker_content_indexes:
            copy_rows.append(i.row())
            for r in [ci.row() for ci in self.children_job_indexes(i)]:
                if self.checker(r) == checker or self.checker(r) in copy_checkers:
                    copy_rows.append(r)

        for i in checker_content_indexes:
            self.collect_all_parent(i, copy_rows)

        sorted_copy_rows = list(set(copy_rows))
        sorted_copy_rows.sort()

        cur_row = self.get_last_row() + 1
        for r in sorted_copy_rows:
            self.copy_rows(r, cur_row)
            cur_row += 1

    def copy_rows(self, src_r, tgt_r):
        print('copy_rows: {}, {}'.format(src_r, tgt_r))
        for c in range(self.columnCount()):
            self.set_data_at(tgt_r, c, self.content_at(src_r, c))


class MainWindow(QMainWindow):
    def __init__(self, load_last_file = True):
        super().__init__()

        self.is_dev = len(sys.argv) > 1

        self.installEventFilter(self)

        self.cur_model = None
        self.cur_page_name = ''

        self.views = []
        self.cur_view = None

        self.setup_ui()
        self.init_focus_policy()
        self.init_signal_slots()

        self.undostack = QUndoStack()
        self.curr_path = None

        if load_last_file:
            self.open_last_file()

    def setup_ui(self):
        self.setGeometry(100, 100, 800, 600)

        gridlayout = QGridLayout()
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(gridlayout)

        settingLayout = QHBoxLayout()
        self.txt_row_count = LabeledLineEdit('row', 0)
        self.txt_col_count = LabeledLineEdit('col', 0)
        self.txt_cell_width = LabeledLineEdit('cell width', cu.load_settings('col_width', 50))
        self.txt_cell_height = LabeledLineEdit('cell height', cu.load_settings('row_height', 30))
        self.txt_cell_font_size = LabeledLineEdit('font size', cu.load_settings('cell_font_size', 12))
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
        self.btn_add_tab = QPushButton('add tab')
        self.btn_create_new_date = QPushButton('new date')
        buttonlayout.addWidget(self.btn_open)
        buttonlayout.addWidget(self.btn_save)
        buttonlayout.addWidget(self.btn_save_as)
        buttonlayout.addWidget(self.btn_new)
        buttonlayout.addWidget(self.btn_bg_color)
        buttonlayout.addWidget(self.btn_clear_bg_color)
        buttonlayout.addWidget(self.btn_add_tab)
        buttonlayout.addWidget(self.btn_create_new_date)

        gridlayout.addLayout(settingLayout, 0, 0)
        gridlayout.addWidget(self.txt_path, 1, 0)
        gridlayout.addLayout(buttonlayout, 2, 0)

        self.tab_notes = QTabWidget()
        self.tab_notes.setTabBar(EditableTabBar(self))
        gridlayout.addWidget(self.tab_notes, 3, 0)

        self.find_ui = FindWidget(self.centralWidget())
        self.find_ui.hide()

        self.setting_ui = SettingPane(self.centralWidget())
        self.setting_ui.hide()

    def init_view_settings(self, view):
        view.set_cell_size(int(self.txt_cell_width.text()), int(self.txt_cell_height.text()))
        view.set_cell_font_size(self.txt_cell_font_size.text())

    def init_signal_slots(self):
        self.txt_row_count.return_pressed.connect(self.update_model_row_count)
        self.txt_col_count.return_pressed.connect(self.update_model_col_count)
        self.txt_cell_width.return_pressed.connect(self.set_all_column_width)
        self.txt_cell_height.return_pressed.connect(self.set_all_row_height)
        # self.txt_cell_font_size.return_pressed.connect(self.cur_view.set_cell_font_size)
        self.btn_open.clicked.connect(self.open)
        self.btn_save.clicked.connect(lambda state: self.save(self.curr_path))
        self.btn_save_as.clicked.connect(lambda state: self.save())
        self.btn_new.clicked.connect(self.create_new)
        self.btn_bg_color.clicked.connect(self.set_bgcolor)
        self.btn_clear_bg_color.clicked.connect(self.clear_bgcolor)
        self.btn_add_tab.clicked.connect(self.add_tab)
        self.btn_create_new_date.clicked.connect(self.create_new_date)

        self.tab_notes.currentChanged.connect(self.change_tab)

        self.find_ui.find_req.connect(self.find_text)

    def open_last_file(self):
        if self.is_dev:
            self.open('test_note.note')
            return
        self.open(cu.load_settings('last_file'))

    def init_focus_policy(self):
        self.txt_cell_width.setFocusPolicy(Qt.ClickFocus)
        self.txt_cell_height.setFocusPolicy(Qt.ClickFocus)
        self.txt_cell_font_size.setFocusPolicy(Qt.ClickFocus)
        self.txt_path.setFocusPolicy(Qt.NoFocus)

    def toggle_show_settings(self):
        self.setting_ui.setVisible(not self.setting_ui.isVisible())

    def eventFilter(self, widget, e):
        # this doesn't work ao 20171123
        if e.type() == QEvent.KeyPress and e.key() == Qt.Key_Tab and e.mod() == Qt.ControlModifier:
            self.change_tab()
            return True
        return super().eventFilter(widget, e)

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        key = e.key()
        mod = QApplication.keyboardModifiers()
        # # for key check
        # print('key={}, text={}, name={}'.format(key, e.text(), QtGui.QKeySequence(key).toString()))
        if key == Qt.Key_Escape:
            # toto: will introduce state
            if self.find_ui.isVisible():
                self.close_find_ui()
        elif key == Qt.Key_S and mod == Qt.ControlModifier:
            self.save(self.curr_path)
            e.accept()
        elif key == Qt.Key_F and mod == Qt.ControlModifier:
            self.show_find()
            e.accept()
        elif key == Qt.Key_Delete:
            self.delete_selected()
            e.accept()
        elif key == Qt.Key_I and mod == Qt.ControlModifier:
            self.insert_all_row()
            e.accept()
        elif key == Qt.Key_I and mod == Qt.ControlModifier | Qt.ShiftModifier:
            self.insert_all_row(True)
            e.accept()
        elif key == Qt.Key_K and mod == Qt.ControlModifier:
            self.delete_all_row()
            e.accept()
        elif key == Qt.Key_O and mod == Qt.ControlModifier:
            self.insert_sel_col()
            e.accept()
        elif key == Qt.Key_L and mod == Qt.ControlModifier:
            self.delete_sel_col()
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
        elif key == Qt.Key_Period and mod == Qt.ControlModifier:
            self.cur_model.set_checker(self.cur_view.curr_row(), Checker.PROGRESS)
            e.accept()
        elif key == Qt.Key_Comma and mod == Qt.ControlModifier:
            self.cur_model.set_checker(self.cur_view.curr_row())
            e.accept()
        elif key == Qt.Key_Slash and mod == Qt.ControlModifier:
            self.cur_model.set_checker(self.cur_view.curr_row(), Checker.DONE)
            e.accept()
        elif key == 39 and mod == Qt.ControlModifier:
            self.cur_model.set_checker(self.cur_view.curr_row(), Checker.MISSED)
            e.accept()
        elif key == Qt.Key_Minus and mod == Qt.ControlModifier:
            self.cur_model.set_checker(self.cur_view.curr_row(), Checker.IGNORE)
            e.accept()
        elif key == Qt.Key_M and mod == Qt.ControlModifier:
            self.cur_model.set_checker(self.cur_view.curr_row(), Checker.MOVETO)
            e.accept()
        elif key == Qt.Key_H and mod == Qt.ControlModifier:
            self.toggle_show_settings()
            e.accept()
        elif key == Qt.Key_Tab and mod == Qt.ControlModifier:
            self.change_to_next_tab()
            e.accept()
        elif key == Qt.Key_Tab and mod == Qt.ControlModifier | Qt.ShiftModifier:
            self.change_to_next_tab(-1)
            e.accept()
        else:
            e.ignore()
            super().keyPressEvent(e)

    def closeEvent(self, e: QtGui.QCloseEvent):
        cu.save_settings('last_row', self.cur_view.curr_row())
        cu.save_settings('last_col', self.cur_view.curr_col())

    def load_model_from_file(self, path):
        if not path:
            return False

        if not os.path.exists(path):
            return False

        with open(path, 'rb') as f:
            if self.load_models(pickle.load(f)):
                self.set_path(path)
                if not self.is_dev:
                    cu.save_settings('last_file', self.curr_path)
                return True
            else:
                return False

    def set_cur_view(self, view):
        self.cur_view = view
        self.cur_model = view.model()
        self.cur_view.give_focus()

    def add_view(self, page_name, model):
        view = SplitTableView(page_name)
        self.views.append(view)
        self.tab_notes.addTab(view, view.page_name)
        ''' todo : can't connect to multi views - change need'''
        self.txt_cell_font_size.return_pressed.connect(view.set_cell_font_size)
        self.init_view_settings(view)
        view.set_model(model)

        return view

    def load_models(self, data):
        models = []
        if type(data[0][0]) is StyledNoteData:
            models.append(('default', JobModel(data, self.undostack)))
        else:
            for page_name, page_data in data:
                models.append((page_name, JobModel(page_data, self.undostack)))

        if len(models) > 0:
            self.models = models

            for page_name, model in models:
                self.add_view(page_name, model)

            if len(self.views) > 0:
                self.set_cur_view(self.views[0])
                self.cur_view.give_focus()
            self.cur_page_name = self.models[0][0]
            self.cur_model = self.models[0][1]
            self.move_to_last_index()
            self.show_model_row_col()

            return True
        else:
            return False

    def update_model_row_count(self, count):
        ok = self.cur_model.change_row_count(int(count))
        if ok:
            self.cur_view.apply_cell_size()
        else:
            QMessageBox.warning(self, 'fail', 'some row has data')

    def update_model_col_count(self, count):
        if not self.cur_model.change_col_count(int(count)):
            QMessageBox.warning(self, 'fail', 'some row has data')

    def set_all_column_width(self, width):
        w = int(width) if width.isdigit() else 0
        if w > 0 and w <= 100:
            for c in range(self.cur_model.columnCount()):
                self.cur_view.set_column_width(c, w)
                self.top_view.setColumnWidth(c, w)

    def set_all_row_height(self, height):
        h = int(height) if height.isdigit() else 0
        if h > 0 and h <= 100:
            for r in range(self.cur_model.rowCount()):
                self.cur_view.set_row_height(r, h)

    def move_to_last_index(self):
        last_index = self.cur_model.index(cu.load_settings('last_row', 0), cu.load_settings('last_col', 0))
        self.cur_view.set_curr_index(last_index)

    def show_model_row_col(self):
        self.txt_row_count.set_text(self.cur_model.rowCount())
        self.txt_col_count.set_text(self.cur_model.columnCount())

    def open(self, path = None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, 'select open file')

        if not self.load_model_from_file(path):
            QMessageBox.warning(self, 'open', "couldn't find file")

    def make_save_object(self):
        return [(self.tab_notes.tabText(i), v.model().get_src_data()) for i, v in enumerate(self.views)]

    def save(self, path = None):
        is_new_save = path is None
        if is_new_save:
            path, _ = QFileDialog.getSaveFileName(self, 'select save file')

        with open(path, 'wb') as f:
            pickle.dump(self.make_save_object(), f)

        if is_new_save:
            self.open(path)

        self.save_ui_settings()

        QMessageBox.information(self, 'save', 'saved')

    def set_path(self, path):
        self.txt_path.setText(path)
        self.curr_path = path if path != '' else None

    def create_new(self):
        # self.model = JobModel(default_list_data, self.undostack)
        # self.cur_view.set_model(self.model)
        # self.show_model_row_col()

        self.clear_all_views()
        self.set_path('')

        # self.load_models(default_tabbed_data)
        self.load_models(test_tabbed_data)

    def clear_all_views(self):
        for i, v in enumerate(self.views):
            self.tab_notes.removeTab(i)
            v.close()

    def save_ui_settings(self):
        cu.save_settings('col_width', int(self.txt_cell_width.text()))
        cu.save_settings('row_height', int(self.txt_cell_height.text()))
        cu.save_settings('cell_font_size', int(self.txt_cell_font_size.text()))

    def delete_selected(self):
        cmd = DeleteCommand(self.cur_view.selected_indexes())
        self.undostack.push(cmd)
        # indexes = self.cur_view.selected_indexes()
        # for i in indexes:
        #     self.cur_model.del_data_at(i)

    def insert_all_row(self, insert_below = False):
        cur_i = self.cur_view.curr_index()
        cmd = InsertAllRowCommand(cur_i, insert_below, self.cur_view)
        self.undostack.push(cmd)

    def delete_all_row(self):
        cur_i = self.cur_view.curr_index()
        cmd = DeleteAllRowCommand(cur_i)
        self.undostack.push(cmd)

    def insert_sel_col(self):
        cmd = InsertColumnCommand(self.cur_view.selected_indexes())
        self.undostack.push(cmd)

    def delete_sel_col(self):
        cmd = DeleteColumnCommand(self.cur_view.selected_indexes())
        self.undostack.push(cmd)

    def set_bgcolor(self):
        color = QColorDialog.getColor()
        cur_i = self.cur_view.curr_index()
        self.cur_model.set_style_at(cur_i.row(), cur_i.column(), color)
        self.cur_view.update(cur_i)

        for i in self.cur_view.selected_indexes():
            self.cur_model.set_style_at(i.row(), i.column(), color)
            self.cur_view.update(i)

    def clear_bgcolor(self):
        for i in self.cur_view.selected_indexes():
            self.cur_model.del_style_at(i.row(), i.column())
            self.cur_view.update(i)

    def add_tab(self):
        '''default model 달린 view가 추가되면 됨'''
        model = JobModel(default_single_tab_data, self.undostack)
        view = self.add_view('page2', model)
        self.models.append(model)

        '''new view as current'''
        self.set_cur_view(view)
        self.tab_notes.setCurrentWidget(view)

    def change_tab(self, tab_index):
        view = self.tab_notes.widget(tab_index)
        self.set_cur_view(view)

    def change_to_next_tab(self, offset = 1):
        tab_index = (self.tab_notes.currentIndex() + offset) % self.tab_notes.count()
        self.change_tab(tab_index)

    def create_new_date(self):
        '''
        find last row
        add date on col[0]
        copy prev date's moveto checker data(include children, parent)
        '''

        date_row = self.cur_model.get_last_row() + 1

        self.cur_model.add_copy_from_last_date(Checker.MOVETO, Checker.PROGRESS, Checker.MISSED, None)

        date = datetime.now().strftime('%Y-%m-%d')
        self.cur_model.set_data_at(date_row, 0, date)
        self.move_to_index(self.cur_model.index(date_row, 5))
        self.cur_view.give_focus()

    def copy_to_clipboard(self):
        selections = self.cur_view.selected_indexes()
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
        cur_i = self.cur_view.curr_index()
        for r, l in enumerate(csv.reader(text.split('\n'))):
            for c, t in enumerate(l):
                i = self.cur_model.index(cur_i.row() + r, cur_i.column() + c)
                if t == '':
                    self.cur_model.del_data_at(i.row(), i.column())
                else:
                    self.cur_model.set_data_at(i.row(), i.column(), t)

    def move_to_index(self, index):
        self.cur_view.set_curr_index(index)
        self.cur_view.select(index, QItemSelectionModel.ClearAndSelect)

    def move_to_first_data(self, key):
        if key == Qt.Key_Up:
            cur_i = self.cur_view.curr_index()
            for r in range(cur_i.row() - 1, 0, -1):
                i = self.cur_model.index(r, cur_i.column())
                if i.data():
                    self.move_to_index(i)
                    return
        elif key == Qt.Key_Down:
            cur_i = self.cur_view.curr_index()
            for r in range(cur_i.row() + 1, self.cur_model.rowCount()):
                i = self.cur_model.index(r, cur_i.column())
                if i.data():
                    self.move_to_index(i)
                    return
        elif key == Qt.Key_Left:
            cur_i = self.cur_view.curr_index()
            for c in range(cur_i.column() - 1, 0, -1):
                i = self.cur_model.index(cur_i.row(), c)
                if i.data():
                    self.move_to_index(i)
                    return
        elif key == Qt.Key_Right:
            cur_i = self.cur_view.curr_index()
            for c in range(cur_i.column() + 1, self.cur_model.columnCount()):
                i = self.cur_model.index(cur_i.row(), c)
                if i.data():
                    self.move_to_index(i)
                    return

    def move_to_end(self, key):
        cur_i = self.cur_view.curr_index()
        if key == Qt.Key_Up:
            self.move_to_index(self.cur_model.index(0, cur_i.column()))
        elif key == Qt.Key_Down:
            self.move_to_index(self.cur_model.index(self.cur_model.rowCount() - 1, cur_i.column()))
        elif key == Qt.Key_Left:
            self.move_to_index(self.cur_model.index(cur_i.row(), 0))
        elif key == Qt.Key_Right:
            self.move_to_index(self.cur_model.index(cur_i.row(), self.cur_model.columnCount() - 1))

    def show_find(self):
        self.find_ui.show()

    def close_find_ui(self):
        self.find_ui.hide()
        self.cur_view.give_focus()

    def find_text(self, text):
        '''
        일단 간단히 find next 로 구현
        '''
        found_index = None
        cur_i = self.cur_view.curr_index()
        for r, c in product(range(cur_i.row() + 1, self.cur_model.rowCount()), range(self.cur_model.columnCount())):
            content = self.cur_model.content_at(r, c)
            if content and text in content:
                found_index = self.cur_model.index(r, c)
                break
        if found_index:
            self.move_to_index(found_index)
        else:
            cu.debug_msg(self, 'not found')


class SetDataCommand(QUndoCommand):
    def __init__(self, index, value):
        super().__init__('set data')

        self.model = index.model()
        self.index = index
        self.r = index.row()
        self.c = index.column()
        self.new_value = value
        self.old_value = None

    def redo(self):
        old_data = self.model.data_at(self.r, self.c)
        if old_data:
            self.old_value = old_data.content
        if self.index.column() == self.model.check_col:
            self.model.set_checker(self.index.row(), Checker.get_def(self.new_value))
        else:
            self.model.set_data_at(self.r, self.c, self.new_value)

    def undo(self):
        if self.old_value:
            if self.index.column() == self.model.check_col:
                self.model.set_checker(self.r, Checker.get_def(self.old_value))
            else:
                self.model.set_data_at(self.r, self.c, self.old_value)
        else:
            if self.index.column() == self.model.check_col:
                self.model.set_checker(self.r)
            else:
                self.model.del_data_at(self.r, self.c)


class DeleteCommand(QUndoCommand):
    def __init__(self, indexes):
        super().__init__('delete')
        self.indexes = indexes
        if len(indexes) > 0:
            self.model = indexes[0].model()
        self.deleted_data = []

    def redo(self):
        for i in self.indexes:
            d = self.model.data_at(i.row(), i.column())
            if d:
                self.deleted_data.append(d)
                if i.column() == self.model.check_col:
                    self.model.set_checker(i.row(), None)
                else:
                    self.model.del_data_at(i.row(), i.column())

    def undo(self):
        for e in self.deleted_data:
            if e.c == self.model.check_col:
                self.model.set_checker(e.r, Checker.get_def(e.content))
            else:
                self.model.set_data_at(e.r, e.c, e.content)
        self.deleted_data.clear()


class InsertAllRowCommand(QUndoCommand):
    def __init__(self, index, insert_below = False, view = None):
        super().__init__('insert all row')

        self.index = index if not insert_below else index.model().index(index.row() + 1, index.column())
        self.insert_below = insert_below
        self.view = view

    def redo(self):
        self.index.model().insert_all_row(self.index)
        if self.insert_below and self.view:
            self.view.set_curr_index(self.index)

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
            data = model.data_at(r, c)
            if data:
                self.deleted_data.append(data)

        self.index.model().delete_all_row(self.index)

    def undo(self):
        self.index.model().insert_all_row(self.index)

        model = self.index.model()
        for e in self.deleted_data:
            model.set_data_at(e.r, e.c, e.content)
        self.deleted_data.clear()


class InsertColumnCommand(QUndoCommand):
    def __init__(self, indexes):
        super(InsertColumnCommand, self).__init__('insert columns')

        self.model = indexes[0].model()
        self.indexes = indexes
        self.inserted_data = []
        self.deleted_data = []

    def redo(self):
        m = self.model
        for i in self.indexes:
            r, cur_c = i.row(), i.column()
            for c in range(m.columnCount(), cur_c, -1):
                left_c = c - 1
                left_d = m.data_at(r, left_c)
                if left_d:
                    m.set_data_at(r, c, left_d.content)
                    self.inserted_data.append(m.data_at(r, c))
                    m.del_data_at(r, left_c)
                    self.deleted_data.append(left_d)
        m.layoutChanged.emit()

    def undo(self):
        m = self.model
        for e in self.inserted_data:
            self.model.del_data_at(e.r, e.c)
        for e in self.deleted_data:
            self.model.set_data_at(e.r, e.c, e.content)

        self.inserted_data.clear()
        self.deleted_data.clear()
        m.layoutChanged.emit()


class DeleteColumnCommand(QUndoCommand):
    def __init__(self, indexes):
        super(DeleteColumnCommand, self).__init__('delete columns')

        self.model = indexes[0].model()
        self.indexes = indexes
        self.inserted_data = []
        self.deleted_data = []

    def redo(self):
        m = self.model
        for i in self.indexes:
            r, cur_c = i.row(), i.column()
            for c in range(cur_c, m.columnCount()):
                d = m.data_at(r, c)
                right_c = c + 1
                right_d = m.data_at(r, right_c)
                if d:
                    self.deleted_data.append(d)
                    m.del_data_at(r, c)
                    pass
                if right_d:
                    m.set_data_at(r, c, right_d.content)
                    self.inserted_data.append(m.data_at(r, c))
                    m.del_data_at(r, right_c)
                    self.deleted_data.append(right_d)
                else:
                    m.del_data_at(r, c)
        m.layoutChanged.emit()

    def undo(self):
        m = self.model
        for e in self.inserted_data:
            self.model.del_data_at(e.r, e.c)
        for e in self.deleted_data:
            self.model.set_data_at(e.r, e.c, e.content)

        self.inserted_data.clear()
        self.deleted_data.clear()
        m.layoutChanged.emit()


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
