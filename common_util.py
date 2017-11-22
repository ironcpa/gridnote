from PyQt5.QtCore import QSettings, QPoint
from PyQt5.QtWidgets import QMessageBox

company = 'hjchoi'
app_name = 'gridnote'


def load_settings(key, default_val = None):
    settings = QSettings(company, app_name)
    val = settings.value(app_name + '_' + key)
    if val:
        return val
    else:
        return default_val


def save_settings(key, value):
    settings = QSettings(company, app_name)
    settings.setValue(app_name + '_' + key, value)


def debug_msg(parent, str):
    QMessageBox.information(parent, 'debug', str)