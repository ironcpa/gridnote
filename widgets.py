import os
import sys

from defines import Checker
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui
from PyQt5.QtCore import *


class LabeledLineEdit(QWidget):
    return_pressed = pyqtSignal(str)

    def __init__(self, label_text = '', edit_text = ''):
        super().__init__()
        self.init_ui()

        self.label.setText(label_text)
        self.lineedit.setText(str(edit_text))

        self.lineedit.returnPressed.connect(lambda: self.return_pressed.emit(self.lineedit.text()))

    def init_ui(self):
        settingLayout = QHBoxLayout()
        settingLayout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel('cell width')
        self.lineedit = QLineEdit()
        settingLayout.addWidget(self.label)
        settingLayout.addWidget(self.lineedit)

        self.setLayout(settingLayout)

    def text(self):
        return self.lineedit.text()

    def set_text(self, text):
        self.lineedit.setText(str(text))


class FileChooser(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

        self.btn_show_dialog.clicked.connect(self.on_show_dialog_clicked)

    def init_ui(self):
        self.txt_path = QLineEdit()
        self.btn_show_dialog = QPushButton('...')

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.txt_path)
        layout.addWidget(self.btn_show_dialog)

        self.setLayout(layout)

    def on_show_dialog_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "select file")
        print(path)
        if path and os.path.exists(path):
            self.txt_path.setText(path)

    def set_path(self, path):
        self.txt_path.setText(path)

    def path(self):
        return self.txt_path.text()


class SettingPane(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.map = {}

        self.init_ui()
        self.setGeometry(0, 0, 800, 600)

    def init_ui(self):
        self.setStyleSheet('background-color: yellow')

        gridlayout = QGridLayout()
        row, col = 0, 0
        gridlayout.addWidget(QLabel('key shortcuts'), row, col); row += 1
        gridlayout.addWidget(QLabel('save'), row, col); row += 1
        gridlayout.addWidget(QLabel('delete contents'), row, col); row += 1
        gridlayout.addWidget(QLabel('insert all rows'), row, col); row += 1
        gridlayout.addWidget(QLabel('insert all rows below'), row, col); row += 1
        gridlayout.addWidget(QLabel('remove all rows'), row, col); row += 1
        gridlayout.addWidget(QLabel('insert selected columns'), row, col); row += 1
        gridlayout.addWidget(QLabel('remove selected columns'), row, col); row += 1

        row, col = 0, 1
        self.txt_save_key = QLineEdit()
        self.txt_del_key = QLineEdit()
        self.txt_ins_all_row_key = QLineEdit()
        self.txt_ins_all_row_below_key = QLineEdit()
        self.txt_del_all_row_key = QLineEdit()
        self.txt_ins_sel_col_key = QLineEdit()
        self.txt_del_sel_col_key = QLineEdit()
        gridlayout.addWidget(self.txt_save_key, row, col); row += 1
        gridlayout.addWidget(self.txt_del_key, row, col); row += 1
        gridlayout.addWidget(self.txt_ins_all_row_key, row, col); row += 1
        gridlayout.addWidget(self.txt_ins_all_row_below_key, row, col); row += 1
        gridlayout.addWidget(self.txt_del_all_row_key, row, col); row += 1
        gridlayout.addWidget(self.txt_ins_sel_col_key, row, col); row += 1
        gridlayout.addWidget(self.txt_del_sel_col_key, row, col); row += 1

        self.setLayout(gridlayout)

    def paintEvent(self, a0: QtGui.QPaintEvent):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.fillRect(self.rect(), Qt.gray)
        painter.end()

    def set_setting(self, key, val):
        self.map[key] = val

    def setting(self, key):
        return self.map[key]


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
        elif key == Qt.Key_Tab and mods == Qt.ControlModifier:
            e.ignore()
        elif key == Qt.Key_Tab and mods == Qt.ControlModifier | Qt.ShiftModifier:
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


class SplitTableView(QWidget):
    def __init__(self, page_name = None):
        super().__init__()
        self.page_name = page_name if page_name is not None else 'default'
        self.init_ui()
        self.init_views()

    def init_ui(self):
        gridlayout = QGridLayout()
        self.setLayout(gridlayout)

        self.top_view = NoteDataView()
        self.top_view.horizontalScrollBar().setVisible(False)
        self.top_view.verticalScrollBar().setVisible(False)
        # self.top_view.verticalHeader().setVisible(False)
        self.top_view.setMaximumHeight(100)
        # self.top_view.setStyleSheet('QTableView:item {background: yellow}')
        gridlayout.addWidget(self.top_view, 0, 0)

        self.data_view = NoteDataView()
        self.data_view.horizontalHeader().setVisible(False)
        # self.view.verticalHeader().setVisible(False)
        gridlayout.addWidget(self.data_view, 1, 0)

    def init_views(self):
        data_delegate = NoteDataDelegate()
        style_delegate = NoteStyleDelegate()

        self.top_view.setItemDelegate(data_delegate)
        self.data_view.setItemDelegate(data_delegate)
        self.data_view.setShowGrid(False)

        self.data_view.horizontalScrollBar().valueChanged.connect(self.sync_hscroll)
        self.data_view.verticalScrollBar().valueChanged.connect(self.sync_vscroll)

    def init_focus_policy(self):
        self.top_view.setFocusPolicy(Qt.NoFocus)

    def give_focus(self):
        self.data_view.setFocus()

    def sync_hscroll(self, value):
        self.top_view.horizontalScrollBar().setValue(value)

    def sync_vscroll(self, value):
        pass

    def set_row_height(self, r, h):
        self.top_view.setRowHeight(r, h)
        self.data_view.setRowHeight(r, h)

    def set_column_width(self, c, w):
        self.top_view.setColumnWidth(c, w)
        self.data_view.setColumnWidth(c, w)

    def set_cell_size(self, w, h):
        self.top_view.set_cell_size(w, h)
        self.data_view.set_cell_size(w, h)

    def apply_cell_size(self):
        self.top_view.apply_cell_size()
        self.data_view.apply_cell_size()

    def set_cell_font_size(self, font_size):
        self.top_view.set_cell_font_size(font_size)
        self.data_view.set_cell_font_size(font_size)

    def model(self):
        return self.data_view.model()

    def set_model(self, model):
        self.top_view.setModel(model)
        self.data_view.setModel(model)

    def curr_index(self):
        return self.data_view.currentIndex()

    def curr_row(self):
        return self.curr_index().row()

    def curr_col(self):
        return self.curr_index().column()

    def set_curr_index(self, index):
        self.data_view.setCurrentIndex(index)

    def select(self, index, option):
        self.data_view.selectionModel().select(index, option)

    def selected_indexes(self):
        return self.data_view.selectedIndexes()

    def update(self, index):
        self.top_view.update(index)
        self.data_view.update(index)


class NoteDataDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()

        self.color_complete = Qt.green
        self.color_blank = QtGui.QColor(230, 230, 230)
        self.color_end = Qt.darkCyan

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex):
        return super(NoteDataDelegate, self).createEditor(parent, option, index)
        # return TestLineEdit(parent)

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

        if index.data(Qt.BackgroundRole):
            painter.fillRect(option.rect, index.data(Qt.BackgroundRole))

        if index.data(Qt.DisplayRole):
            content = index.data(Qt.DisplayRole)
            fm = QtGui.QFontMetrics(option.font)
            fh = fm.height() - fm.descent()
            fw = fm.boundingRect(content).width() + 10
            box_w = fw if fw > option.rect.width() else option.rect.width()

            text_rect = QRect(option.rect)
            text_rect.setWidth(box_w)
            o_pen = painter.pen()
            check_col = index.model().check_col
            checker_def = Checker.get_def(index.model().index(index.row(), check_col).data())
            if checker_def:
                painter.fillRect(text_rect, checker_def.bgcolor)
                if checker_def.fgcolor is not None:
                    painter.setPen(checker_def.fgcolor)
            else:
                painter.fillRect(text_rect, self.color_blank)
            # if index.model().index(index.row(), check_col).data() == Checker.DONE.str:
            #     painter.fillRect(text_rect, self.color_complete)
            # elif index.model().index(index.row(), check_col).data() == Checker.PROGRESS.str:
            #     painter.fillRect(text_rect, Qt.blue)
            #     painter.setPen(Qt.white)
            # elif index.model().index(index.row(), check_col).data() == Checker.MISSED.str:
            #     painter.fillRect(text_rect, Qt.red)
            #     painter.setPen(Qt.white)
            # elif index.model().rel_checker(index) == Checker.IGNORE.str:
            #     painter.fillRect(text_rect, Qt.yellow)
            # elif index.model().rel_checker(index) == Checker.MOVETO.str:
            #     painter.fillRect(text_rect, Qt.cyan)
            # elif index.model().index(index.row(), check_col).data() == None:
            #     painter.fillRect(text_rect, self.color_blank)

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


class EditableTabBar(QTabBar):
    def __init__(self, parent):
        QTabBar.__init__(self, parent)
        self._editor = QLineEdit(self)
        self._editor.setWindowFlags(Qt.Popup)
        '''augie : i don't know what the focusproxy is. original code has it'''
        # self._editor.setFocusProxy(self)
        self._editor.editingFinished.connect(self.handleEditingFinished)
        self._editor.installEventFilter(self)

    def eventFilter(self, widget, event):
        if ((event.type() == QEvent.MouseButtonPress and
             not self._editor.geometry().contains(event.globalPos())) or
            (event.type() == QEvent.KeyPress and
             event.key() == Qt.Key_Escape)):
            self._editor.hide()
            return True
        return QTabBar.eventFilter(self, widget, event)

    def mouseDoubleClickEvent(self, event):
        index = self.tabAt(event.pos())
        if index >= 0:
            self.editTab(index)

    def editTab(self, index):
        rect = self.tabRect(index)
        self._editor.setFixedSize(rect.size())
        self._editor.move(self.parent().mapToGlobal(rect.topLeft()))
        self._editor.setText(self.tabText(index))
        if not self._editor.isVisible():
            self._editor.show()
            self._editor.setCursorPosition(len(self.tabText(index)) - 1)

    def handleEditingFinished(self):
        index = self.currentIndex()
        if index >= 0:
            self.setTabText(index, self._editor.text())
            self._editor.hide()


class FindWidget(QWidget):
    find_req = pyqtSignal(str)

    def __init__(self, parent):
        super(FindWidget, self).__init__(parent)

        # self.setStyleSheet('background-color: yellow')
        self.setup_ui()
        self.init_signal_slots()

    def setup_ui(self):
        self.setGeometry(0, 0, 500, 100)

        base_layout = QVBoxLayout()
        self.setLayout(base_layout)

        self.txt_find_text = QLineEdit()
        self.btn_find = QPushButton('find')
        self.btn_close = QPushButton('close')

        base_layout.addWidget(self.txt_find_text)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_find)
        button_layout.addWidget(self.btn_close)
        base_layout.addLayout(button_layout)

    def init_signal_slots(self):
        self.btn_find.clicked.connect(lambda: self.find_req.emit(self.txt_find_text.text()))
        self.btn_close.clicked.connect(self.hide)
        self.txt_find_text.returnPressed.connect(lambda: self.find_req.emit(self.txt_find_text.text()))

    def paintEvent(self, e):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.fillRect(self.rect(), Qt.blue)
        painter.end()
        super().paintEvent(e)

    def show(self):
        super().show()
        self.txt_find_text.setFocus()


class NotiWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.setGeometry(0, 0, 160, 60)

        base_layout = QHBoxLayout()
        self.setLayout(base_layout)

        self.label = QLabel('saved')
        self.label.setStyleSheet('QLabel {font: 20pt; color: white}')
        self.label.setAlignment(Qt.AlignCenter)
        base_layout.addWidget(self.label)

    def paintEvent(self, e):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.fillRect(self.rect(), Qt.red)
        painter.end()
        super().paintEvent(e)

    def show_noti(self, text, color=None):
        self.move(self.parent().width() - self.width(), 0)
        self.label.setText(text)
        self.show()
        QTimer.singleShot(1000, self.hide)


class TestLineEdit(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.textChanged.connect(self.debug_edit)

    def debug_edit(self):
        print('>>>>>>>>', self.text())


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # setting_ui = SettingPane(self)
        # setting_ui.show()

        layout = QHBoxLayout()
        self.setLayout(layout)

        lineedit = QLineEdit()
        layout.addWidget(lineedit)

        self.tab = QTabWidget()
        self.tab.setTabBar(EditableTabBar(self))
        tab_content1 = QWidget()
        tab_content2 = QWidget()
        split_view = SplitTableView()

        self.tab.addTab(split_view, 'note 1')
        self.tab.addTab(tab_content1, 'tab 1')
        self.tab.addTab(tab_content2, 'tab 2')

        layout.addWidget(self.tab)

        # find_widget = FindWidget(self)
        # find_widget.find_req.connect(self.dummy_slot)
        # find_widget.show()

        btn_test = QPushButton('test')
        btn_test.clicked.connect(self.dummy_slot)
        layout.addWidget(btn_test)

    def dummy_slot(self):
        self.tab.removeTab(0)

    def dummy_slot_1(self, arg):
        QMessageBox.information(self, 'test', str(arg))


def catch_exceptions(self, t, val, tb):
    QMessageBox.critical(None, 'exception', '{}'.format(t))
    old_hook(t, val, tb)


if __name__ == '__main__':
    old_hook = sys.excepthook
    sys.excepthook = catch_exceptions

    app = QApplication(sys.argv)

    test_window = TestWindow()
    test_window.show()
    app.exec_()
