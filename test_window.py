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


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.style_model = QtGui.QStandardItemModel(100, 100)
        self.style_view = QTableView(self)
        self.style_view.setModel(self.style_model)
        self.style_view.setStyleSheet('* {background-color: yellow;; gridline-color: red}')
        self.style_view.setGeometry(0, 0, 800, 600)

        self.data_model = QtGui.QStandardItemModel(100, 100)
        self.data_model.setItem(0, 0, QtGui.QStandardItem('aaa'))

        self.data_view = QTableView(self)
        self.data_view.setModel(self.data_model)
        self.data_view.setGeometry(0, 0, 800, 600)
        self.data_view.setStyleSheet('* {background-color: transparent}')
        self.fill_label()

        self.resize(800, 600)

    def fill_label(self):
        for r in range(self.data_model.rowCount()):
            for c in range(self.data_model.columnCount()):
                self.data_view.setIndexWidget(self.data_model.index(r, c), QLabel('cell'))


class LabelTableView(QTableView):
    def __init__(self):
        super().__init__()

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: typing.Iterable[int] = ...):
        label = self.indexWidget(topLeft)
        data = self.model().data(topLeft)
        if data:
            label.setText(data)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    mywindow = TestWindow()
    mywindow.show()
    app.exec_()
