from unittest import TestCase
from widgets import SettingPane
from PyQt5.QtWidgets import QApplication
import sys


class TestSettingPane(TestCase):
    def test_set_n_get_setting(self):
        app = QApplication(sys.argv)
        widget = SettingPane(None)

        widget.set_setting('key:save', 'S')
        self.assertTrue(widget.setting('key:save') == 'S')