# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'lib/qt/cnctoolbox/simulatordialog.ui'
#
# Created: Thu Dec 10 13:58:11 2015
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SimulatorDialog(object):
    def setupUi(self, SimulatorDialog):
        SimulatorDialog.setObjectName("SimulatorDialog")
        SimulatorDialog.resize(807, 550)
        self.gridLayout_2 = QtWidgets.QGridLayout(SimulatorDialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout_simulator = QtWidgets.QGridLayout()
        self.gridLayout_simulator.setObjectName("gridLayout_simulator")
        self.gridLayout.addLayout(self.gridLayout_simulator, 0, 0, 1, 2)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(SimulatorDialog)
        QtCore.QMetaObject.connectSlotsByName(SimulatorDialog)

    def retranslateUi(self, SimulatorDialog):
        _translate = QtCore.QCoreApplication.translate
        SimulatorDialog.setWindowTitle(_translate("SimulatorDialog", "Dialog"))

