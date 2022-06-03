#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QCheckBox
from appdirs import *
import json
import os

appauthor  = "opentropia"
appname = "raretropia"

default_settings = {
  "Avatar Name": "My Fancy Avatar",
  "Avatar Alias": "Fancy",
  "Foo": True,
}

settings_file_path = os.path.join(user_data_dir(appname, appauthor), "settings.json")


class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)

        with open(settings_file_path, 'r') as file:
            self._data = json.load(file)

        self.setWindowTitle(appname)
        self.resize(600, 320)

        self._createMenu()
        self._createStatusBar()

        tabs = QTabWidget()
        tabs.addTab(self._createGeneralUI(), "General")
        tabs.addTab(self._createRareListUI(), "Rare List")
        tabs.addTab(self._createTwitchUI(), "Twitch")
        tabs.addTab(self._createAdvancedUI(), "Advanced")

        self.setCentralWidget(tabs)

    def _datachanged(self, key, value):
        print(f"foooo {key} - {value}")
        self._data[key] = value

        with open(settings_file_path, 'w') as file:
            file.write(json.dumps(self._data, sort_keys=True, indent=4))

    def _createGeneralUI(self):
        tab = QWidget()

        layout = QFormLayout()
        avatar_name = QLineEdit()
        avatar_name.setText(self._data["Avatar Name"])
        avatar_name.editingFinished.connect(lambda: self._datachanged("Avatar Name", avatar_name.text()))
        avatar_name.setToolTip("Full avatar name, must match in game name exactly")
        layout.addRow('Avatar Name', avatar_name)
        avatar_alias = QLineEdit()
        avatar_alias.setText(self._data["Avatar Alias"])
        avatar_alias.setToolTip("A custom name used in messages, typically your in game short name")
        avatar_alias.editingFinished.connect(lambda: self._datachanged("Avatar Alias", avatar_alias.text()))
        layout.addRow('Avatar Alias', avatar_alias)
        toggle = QCheckBox()
        toggle.setChecked(self._data["Foo"])
        toggle.toggled.connect(lambda: self._datachanged("Foo", toggle.isChecked()))
        layout.addRow('Foo', toggle)
        tab.setLayout(layout)

        return tab

    def _createRareListUI(self):
        tab = QWidget()

        layout = QVBoxLayout()
        layout.addWidget(QPushButton('Center'))
        layout.addWidget(QPushButton('Top'))
        layout.addWidget(QPushButton('Bottom'))
        tab.setLayout(layout)

        return tab

    def _createTwitchUI(self):
        tab = QWidget()

        layout = QFormLayout()
        layout.addRow('User ID:', QLineEdit())
        layout.addRow('Channel ID:', QLineEdit())
        token = QLineEdit()
        token.setEchoMode(QLineEdit.Password)
        layout.addRow('Token:', token)
        tab.setLayout(layout)

        return tab

    def _createAdvancedUI(self):
        tab = QWidget()

        layout = QVBoxLayout()
        layout.addWidget(QPushButton('Center'))
        layout.addWidget(QPushButton('Top'))
        layout.addWidget(QPushButton('Bottom'))
        tab.setLayout(layout)

        return tab

    def _createMenu(self):
        self.menu = self.menuBar().addMenu("&Menu")
        self.menu.addAction('&Exit', self.close)

    def _createStatusBar(self):
        status = QStatusBar()
        status.showMessage("I'm the Status Bar")
        self.setStatusBar(status)

def main():
    os.makedirs(user_data_dir(appname, appauthor), exist_ok=True)

    if not os.path.exists(settings_file_path):
        with open(settings_file_path, 'w') as file:
            file.write(json.dumps(default_settings, sort_keys=True, indent=4))


    app = QApplication([])

    window = Window()
    #window.set_stylesheet(window, "dark.qss")
    window.show()

    #timer = QtCore.QTimer()
    #timer.timeout.connect(window.on_tick)
    #timer.start(MAIN_EVENT_LOOP_TICK * 1000)

    app.exec()


if __name__ == "__main__":
    main()