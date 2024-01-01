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
from lib.qt.gerbil_gui.ui_simulatordialog import Ui_SimulatorDialog

from .simulatorwidget import SimulatorWidget

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, QPoint, QSize, Qt, QCoreApplication, QTimer
from PyQt5.QtGui import QColor,QPalette
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMessageBox, QSlider, QLabel, QPushButton, QWidget, QDialog, QMainWindow, QFileDialog, QLineEdit, QSpacerItem, QListWidgetItem, QMenuBar, QMenu, QAction, QTableWidgetItem, QDialog

class SimulatorDialog(QWidget, Ui_SimulatorDialog):
    def __init__(self, parent, refresh_rate=20):
        super(SimulatorDialog, self).__init__()
        self.setupUi(self)
        
        self.simulator_widget = SimulatorWidget(self, refresh_rate)
        self.gridLayout_simulator.addWidget(self.simulator_widget)
