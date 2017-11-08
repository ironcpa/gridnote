from PyQt5.QtCore import QSettings, QPoint

company = 'hjchoi'
app_name = 'gridnote'


def load_settings(key):
    settings = QSettings(company, app_name)
    return settings.value(app_name + '_' + key)


def save_settings(key, value):
    settings = QSettings(company, app_name)
    settings.setValue(app_name + '_' + key, value)
