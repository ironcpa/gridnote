from PyQt5.QtCore import QSettings, QPoint
from PyQt5.QtWidgets import QMessageBox

company = 'hjchoi'
app_name = 'gridnote'


def load_settings(key, default_val = None):
    print('debug> load_settings:9', key)
    settings = QSettings(company, app_name)
    val = settings.value(app_name + '_' + key)
    if val:
        print('debug>   ', val, type(val))
        return val
    else:
        print('debug> load_settings', key)
        return default_val


def save_settings(key, value):
    settings = QSettings(company, app_name)
    settings.setValue(app_name + '_' + key, value)


def debug_msg(parent, str):
    QMessageBox.information(parent, 'debug', str)


def str_index(index):
    if index:
        return '({}:{})'.format(index.row(), index.column())


def str_indexes(indexes):
    return ''.join([str_index(i) for i in indexes])


def make_index(model, *indexes):
    return [model.index(r, c) for r, c in indexes]


def turn_off_pyqt_loop_log():
    # to remove log on pdb debuggin
    from PyQt5.QtCore import pyqtRemoveInputHook
    from pdb import set_trace
    pyqtRemoveInputHook()

