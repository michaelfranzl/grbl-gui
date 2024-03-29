"""
grbl-gui - Graphical User Interface for the "grbl" CNC controller
Copyright (C) 2015 Michael Franzl

This file is part of grbl-gui.

grbl-gui is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

grbl-gui is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pyglpainter. If not, see <https://www.gnu.org/licenses/>.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLineEdit


class CommandLineEdit(QLineEdit):
    def __init__(self, parent, callback):
        super().__init__(parent)

        self.callback = callback
        self.parent = parent

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Up:
            self.callback("UP")
        elif key == Qt.Key.Key_Down:
            self.callback("DOWN")
        elif key == Qt.Key.Key_Enter:
            self.callback("Enter")
        elif key == Qt.Key.Key_Return:
            self.callback("Enter")
        QLineEdit.keyPressEvent(self, event)
