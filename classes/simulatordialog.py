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

from PyQt6.QtWidgets import QWidget, QGridLayout

from .simulatorwidget import SimulatorWidget


class SimulatorDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("SimulatorDialog")
        self.resize(807, 550)
        self.gridLayout_2 = QGridLayout(self)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout_simulator = QGridLayout()
        self.gridLayout_simulator.setObjectName("gridLayout_simulator")
        self.gridLayout.addLayout(self.gridLayout_simulator, 0, 0, 1, 2)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.simulator_widget = SimulatorWidget(self)
        self.gridLayout_simulator.addWidget(self.simulator_widget)
