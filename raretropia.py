#!/usr/bin/env python3

import queue
import re
import time
from winreg import FlushKey
from PyQt5 import QtCore
from PyQt5 import QtGui
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
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QThread
from PyQt5.QtCore import QTimer
from appdirs import *
import json
import os
import discord
import asyncio
from enum import Enum
import ctypes.wintypes

appauthor  = "opentropia"
appname = "raretropia"

re_log = re.compile(r'(.*?) \[(.*?)\] \[(.*?)\] (.*)')
re_loot = re.compile(r'You received (.*) x \((\d+)\) Value: (\d+\.\d+) PED')
re_global_rare = re.compile(r'(.*) has found a rare item \((.*)\) with a value of (\d+) P.*')


def get_log_filename(type):
    CSIDL_PERSONAL = 5       # My Documents
    SHGFP_TYPE_CURRENT = 0   # Get current, not default value
    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(
        None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)

    return os.path.join(buf.value, "Entropia Universe", type)

default_settings = {
  "Avatar Name": "My Fancy Avatar",
  "Avatar Alias": "Fancy",
  "Log File": get_log_filename("chat.log"),
  "Token": "dummy",
  "Channel ID": "1234",
  "Foo": True,
}

default_item_filters = [
    'Generic Fuse',
    'Summoning Totem',
    'Turrelion Essence',
    'Tail Tip',
    '.*Adjuster.*',
    'Tier ([3-9]|10).*'
]

log_queue = queue.Queue()

class MessageType(Enum):
    RARE = 1
    SOOTO = 2
    GLOBAL = 3
    RARE_HOF = 4
    STOP = 5
    MESSAGE = 6

def log(message_type, str):
    #if level != LogLevel.TRACE:
    print(f"{message_type}: {str}".encode("utf-8"), flush=True)

    global log_queue
    log_queue.put((message_type, str))

settings_file_path = os.path.join(user_data_dir(appname, appauthor), "settings.json")
items_file_path = os.path.join(user_data_dir(appname, appauthor), "item-filters.json")

def getData():
    with open(settings_file_path, 'r') as file:
        data = json.load(file)
    return data

def getItems():
    with open(items_file_path, 'r') as file:
        data = json.load(file)
    return data

def getChannelId():
    return int(getData()["Channel ID"])

class DiscordThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = "Not connected"
        self._should_stop = False

    async def foo(self):
        await self._client.close()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

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

                        try:
                            if message_type == MessageType.RARE:
                                data = getData()
                                await self._client.get_channel(getChannelId()).send(f'"{data["Avatar Alias"]}" found something rare {message}')
                            if message_type == MessageType.RARE_HOF:
                                data = getData()
                                await self._client.get_channel(getChannelId()).send(f'{message}')
                        except Exception as e:
                            print(e)

        @self._client.event
        async def on_ready():
            self.status = "Logged in as {0.user}".format(self._client)
            print(self.status, flush=True)
            data = getData()
            await self._client.get_channel(getChannelId()).send(f'{data["Avatar Alias"]} joined')

        self._client.loop.create_task(message_handler())

        while not self._should_stop:
            try:
                time.sleep(1)
                self._client.loop.run_until_complete(self._client.start(getData()["Token"]))
            except Exception as e:
                print(e)
                self.status = str(e)
    
        self._client = None

    def reconnect(self):
        log(MessageType.STOP, "")

    def stop(self):
        self._should_stop = True
        log(MessageType.STOP, "")


class LogFileThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.item_filter = []
        self.status = ""

    def run(self):
        while True:
            log_file = getData()["Log File"]
            try:
                logfile = open(os.path.join(log_file), "r", encoding="utf-8")
                logfile.seek(0, os.SEEK_END)
                break
            except Exception as e:
                self.status = str(e)
            time.sleep(0.1)

        self.status = "Reading"
        while True:
            line = logfile.readline()
            if not line:
                time.sleep(0.1)
                continue

            result = re.match(re_log, line)

            time_stamp = result.group(1)
            channel = result.group(2)
            user = result.group(3)
            message = result.group(4)

            if channel == "System":
                # Loot
                result = re.match(re_loot, message)
                if result:
                    item = result.group(1)
                    count = int(result.group(2))
                    value = float(result.group(3))

                    print(f"item {item}")

                    for item_re in self.item_filter:
                        print(f"re {item_re}")
                        if re.match(item_re, item):
                            log(MessageType.RARE, f"'{item}' x '{count}' value '{value}'")
            elif channel == "Globals":
                # Rare HoF
                result = re.match(re_global_rare, message)
                if result:
                    log(MessageType.RARE_HOF, message)

    def setFilter(self, item_filter):
        self.item_filter = []
        for item in item_filter:
            self.item_filter.append(re.compile(item))

class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)

        with open(settings_file_path, 'r') as file:
            self._data = json.load(file)

        self.setWindowTitle(appname)
        self.resize(600, 320)

        # TODO: start/stop and update if path changed
        self._logfile_thread = LogFileThread()
        self._logfile_thread.start()

        self._createMenu()
        self._createStatusBar()

        tabs = QTabWidget()
        tabs.addTab(self._createGeneralUI(), "General")
        tabs.addTab(self._createRareListUI(), "Rare List")
        tabs.addTab(self._createDiscordUI(), "Discord")
        tabs.addTab(self._createAdvancedUI(), "Advanced")

        self.setCentralWidget(tabs)

        self._discord_thread = None
        self._startDiscord()

    def stopDiscord(self):
        if self._discord_thread:
            self._discord_thread.stop()
            self._discord_thread.wait()
            self._discord_thread = None

    def timerCallback(self):
        message = "Discord: "
        if self._discord_thread:
            message += self._discord_thread.status
        else:
            message += "Not running, restart the application to load new settings."

        message += " - EU log: " + self._logfile_thread.status

        self._status.showMessage(message)

    def _startDiscord(self):
        self._discord_thread = DiscordThread()
        self._discord_thread.start()

    def _datachanged(self, key, value, reloadDiscord = False):
        print(f"Value changed {key} - {value}")
        self._data[key] = value

        with open(settings_file_path, 'w') as file:
            file.write(json.dumps(self._data, sort_keys=True, indent=4))

        if reloadDiscord:
            self.stopDiscord()

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
        log_file = QLineEdit()
        log_file.setText(self._data["Log File"])
        log_file.setToolTip("Full path to the chat log")
        log_file.editingFinished.connect(lambda: self._datachanged("Log File", log_file.text()))
        layout.addRow('Log File', log_file)
        toggle = QCheckBox()
        toggle.setChecked(self._data["Foo"])
        toggle.toggled.connect(lambda: self._datachanged("Foo", toggle.isChecked()))
        layout.addRow('Foo', toggle)
        tab.setLayout(layout)

        return tab

    def _updateListBox(self):
        items = getItems()

        self._logfile_thread.setFilter(items)

        self._listWidget.clear()
        for item in items:
            self._listWidget.addItem(item)

        self._listWidget.addItem("")

        for i in range(self._listWidget.count()):
            item = self._listWidget.item(i)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

        self._listWidget.itemChanged.connect(lambda: self._updateItemsFromListBox())

    def _updateItemsFromListBox(self):
        self._listWidget.itemChanged.disconnect()

        new_items = []
        for i in range(self._listWidget.count()):
            item = self._listWidget.item(i)
            if item.text().strip():
                new_items.append(item.text().strip())

        with open(items_file_path, 'w') as file:
            file.write(json.dumps(new_items, sort_keys=True, indent=4))

        self._updateListBox()


    def _createRareListUI(self):
        self._listWidget = QListWidget()

        self._updateListBox()

        return self._listWidget

    def onClicked(self, item):
        QMessageBox.information(self, "Info", item.text())

    def _createDiscordUI(self):
        tab = QWidget()

        layout = QFormLayout()
        channel_id = QLineEdit()
        channel_id.setText(str(self._data["Channel ID"]))
        channel_id.setToolTip("The channel (id) to send messages to")
        channel_id.editingFinished.connect(lambda: self._datachanged("Channel ID", int(channel_id.text())))
        layout.addRow('Channel ID', channel_id)
        token = QLineEdit()
        token.setEchoMode(QLineEdit.Password)
        token.setText(self._data["Token"])
        token.setToolTip("Access token. After changing this the application needs to be restarted")
        token.editingFinished.connect(lambda: self._datachanged("Token", token.text(), reloadDiscord=True))
        layout.addRow('Token', token)
        tab.setLayout(layout)

        return tab

    def _createAdvancedUI(self):
        tab = QWidget()

        layout = QVBoxLayout()
        layout.addWidget(QPushButton('TODO'))
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

    if not os.path.exists(items_file_path):
        with open(items_file_path, 'w') as file:
            file.write(json.dumps(default_item_filters, sort_keys=True, indent=4))


    app = QApplication([])

    window = Window()
    window.show()

    timer = QTimer()
    timer.timeout.connect(window.timerCallback)
    timer.start(500)

    app.exec()

    window.stopDiscord()


if __name__ == "__main__":
    main()