#!/usr/bin/env python3

import queue
from winreg import FlushKey
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
from PyQt5.QtCore import QThread
from PyQt5.QtCore import QTimer
from appdirs import *
import json
import os
import discord
import asyncio
from enum import Enum

appauthor  = "opentropia"
appname = "raretropia"

default_settings = {
  "Avatar Name": "My Fancy Avatar",
  "Avatar Alias": "Fancy",
  "Token": "dummy",
  "Channel ID": "1234",
  "Foo": True,
}

log_queue = queue.Queue()

class MessageType(Enum):
    RARE = 1
    SOOTO = 2
    GLOBAL = 3
    HOF = 4
    STOP = 5
    MESSAGE = 6

def log(message_type, str):
    #if level != LogLevel.TRACE:
    print(f"{message_type}: {str}".encode("utf-8"), flush=True)

    global log_queue
    log_queue.put((message_type, str))

settings_file_path = os.path.join(user_data_dir(appname, appauthor), "settings.json")

def getData():
    with open(settings_file_path, 'r') as file:
        data = json.load(file)
    return data

def getChannelId():
    return int(getData()["Channel ID"])

class DiscordThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = "Not connected"

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            TOKEN = getData()["Token"]

            intents = discord.Intents.default()

            intents.messages = True

            self._client = discord.Client(intents = intents)

            async def message_handler():
                global log_queue
                while self._client:
                    await asyncio.sleep(0.1)
                    if not log_queue.empty():
                        log_item = log_queue.get()
                        if log_item:
                            message_type = log_item[0]
                            message = log_item[1]
                            if message_type == MessageType.STOP:
                                data = getData()
                                try:
                                    await self._client.get_channel(getChannelId()).send(f'{data["Avatar Alias"]} left')
                                except Exception as e:
                                    print(e)
                                try:
                                    await self._client.close()
                                except Exception as e:
                                    print(e)
                                self._client = None

            @self._client.event
            async def on_ready():
                self.status = "Logged in as {0.user}".format(self._client)
                print(self.status, flush=True)
                data = getData()
                await self._client.get_channel(getChannelId()).send(f'{data["Avatar Alias"]} joined')

            self._client.loop.create_task(message_handler())

            self._client.run(TOKEN)
        except Exception as e:
            print(e)
            self.status = str(e)

    def stop(self):
        log(MessageType.STOP, "")

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
        tabs.addTab(self._createDiscordUI(), "Discord")
        tabs.addTab(self._createAdvancedUI(), "Advanced")

        self.setCentralWidget(tabs)

        self._discord_thread = None
        self._restartDiscord()

    def stopDiscord(self):
        if self._discord_thread:
            self._discord_thread.stop()
            self._discord_thread.wait()
            self._discord_thread = None

    def timerCallback(self):
        if self._discord_thread:
            self._status.showMessage(self._discord_thread.status)
        else:
            self._status.showMessage("Discord not running")

    def _restartDiscord(self):
        self.stopDiscord()
        self._discord_thread = DiscordThread()
        self._discord_thread.start()

    def _datachanged(self, key, value, reloadDiscord = False):
        print(f"foooo {key} - {value}")
        self._data[key] = value

        with open(settings_file_path, 'w') as file:
            file.write(json.dumps(self._data, sort_keys=True, indent=4))

        if reloadDiscord:
            self._restartDiscord()

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

    def _createDiscordUI(self):
        tab = QWidget()

        layout = QFormLayout()
        channel_id = QLineEdit()
        channel_id.setText(str(self._data["Channel ID"]))
        channel_id.editingFinished.connect(lambda: self._datachanged("Channel ID", int(channel_id.text())))
        layout.addRow('Channel ID', channel_id)
        token = QLineEdit()
        token.setEchoMode(QLineEdit.Password)
        token.setText(self._data["Token"])
        token.editingFinished.connect(lambda: self._datachanged("Token", token.text(), reloadDiscord=True))
        layout.addRow('Token', token)
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
        self._status = QStatusBar()
        self._status.showMessage("I'm the Status Bar")
        self.setStatusBar(self._status)

def main():
    os.makedirs(user_data_dir(appname, appauthor), exist_ok=True)

    if not os.path.exists(settings_file_path):
        with open(settings_file_path, 'w') as file:
            file.write(json.dumps(default_settings, sort_keys=True, indent=4))


    app = QApplication([])

    window = Window()
    window.show()

    timer = QTimer()
    timer.timeout.connect(window.timerCallback)
    timer.start(500)

    print("foo")
    app.exec()
    print("bar")

    window.stopDiscord()


if __name__ == "__main__":
    main()