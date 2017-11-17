import os
import sys

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

        # elif key == Qt.Key_K and mod == Qt.ControlModifier:
        #     self.delete_all_row()
        #     e.accept()
        # elif key == Qt.Key_O and mod == Qt.ControlModifier:
        #     self.insert_sel_col()
        #     e.accept()
        # elif key == Qt.Key_L and mod == Qt.ControlModifier:
        #     self.delete_sel_col()
        #     e.accept()
        # elif key == Qt.Key_C and mod == Qt.ControlModifier:
        #     self.copy_to_clipboard()
        #     e.accept()
        # elif key == Qt.Key_X and mod == Qt.ControlModifier:
        #     self.copy_to_clipboard()
        #     self.delete_selected()
        #     e.accept()
        # elif key == Qt.Key_V and mod == Qt.ControlModifier:
        #     self.paste_from_clipboard()
        #     e.accept()
        # elif key == Qt.Key_Z and mod == Qt.ControlModifier:
        #     self.undostack.undo()
        #     e.accept()
        # elif key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Right, Qt.Key_Left) and mod == Qt.ControlModifier:
        #     self.move_to_first_data(key)
        #     e.accept()
        # elif key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Right, Qt.Key_Left)\
        #         and mod == Qt.ControlModifier | Qt.ShiftModifier:
        #     self.move_to_end(key)
        # elif key == Qt.Key_Period and mod == Qt.ControlModifier:
        #     self.model.set_checker(self.view.currentIndex().row(), '>')
        #     e.accept()
        # elif key == Qt.Key_Comma and mod == Qt.ControlModifier:
        #     self.model.set_checker(self.view.currentIndex().row())
        #     e.accept()
        # elif key == Qt.Key_Slash and mod == Qt.ControlModifier:
        #     self.model.set_checker(self.view.currentIndex().row(), 'o')
        #     e.accept()
        # elif key == 39 and mod == Qt.ControlModifier:
        #     self.model.set_checker(self.view.currentIndex().row(), 'x')
        #     e.accept()
        # elif key == Qt.Key_H and mod == Qt.ControlModifier:
        #     self.show_settings()
        #     e.accept()

    def paintEvent(self, a0: QtGui.QPaintEvent):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.fillRect(self.rect(), Qt.gray)
        painter.end()

    def set_setting(self, key, val):
        self.map[key] = val

    def setting(self, key):
        return self.map[key]


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


if __name__ == '__main__':
    app = QApplication(sys.argv)

    test_window = TestWindow()
    test_window.show()
    app.exec_()
