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

import sys,traceback
import os
import math
import numpy as np
import logging
import collections
import time
import re

import random

from classes.highlighter import Highlighter
from classes.jogwidget import JogWidget
from classes.commandlineedit import CommandLineEdit
from classes.simulatordialog import SimulatorDialog
from grbl_streamer import GrblStreamer
from gcode_machine import GcodeMachine

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, QPoint, QSize, Qt, QCoreApplication, QTimer, QSettings
from PyQt5.QtGui import QColor, QPalette, QKeySequence
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMessageBox, QSlider, QLabel, QPushButton, QWidget, QDialog, QMainWindow, QFileDialog, QLineEdit, QSpacerItem, QListWidgetItem, QMenuBar, QMenu, QAction, QTableWidgetItem, QDialog, QShortcut

from lib.qt.gerbil_gui.ui_mainwindow import Ui_MainWindow
from lib import gcodetools
from lib import utility
from lib import pixel2laser


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, path, baud):
        super(MainWindow, self).__init__()
        self.logger = logging.getLogger('cnctoolbox.window')

        _logbuffer_size = 200

        self.devicepath = path
        self.devicebaud = baud

        self.setupUi(self)
        self.modifyUi()
        self.setupScripting()

        # GENERIC SETUP BEGIN -----
        self.setWindowTitle("gerbil_gui")
        self.lcdNumber_feed_current.display("---")
        # GENERIC SETUP END -----

        self.state = None
        self.state_hash = None
        self.state_hash_dirty = False
        self.state_cs_dirty = False
        self.state_stage_dirty = False
        self.state_heightmap_dirty = False

        self.wpos = (0, 0, 0)
        self.mpos = (0, 0, 0)

        # LOGGING SETUP BEGIN ------
        # setup ring buffer for logging
        self.changed_loginput = False
        self.logoutput_items = []
        self.logoutput_current_index = -1
        self.logbuffer = collections.deque(maxlen=_logbuffer_size)

        for i in range(1, _logbuffer_size):
            self.logbuffer.append("")

        self.label_loginput = QLabel()
        self.label_loginput.setTextFormat(Qt.RichText)
        self.label_loginput.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.scrollArea_loginput.setWidget(self.label_loginput)
        self.label_loginput.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        font = QtGui.QFont()
        font.setFamily("DejaVu Sans Mono")
        font.setPointSize(7)
        #self.label_loginput.setStyleSheet("font: 8pt")
        self.label_loginput.setFont(font)

        font = QtGui.QFont()
        font.setFamily("DejaVu Sans Mono")
        font.setPointSize(7)
        self.label_current_gcode.setFont(font)
        # LOGGING SETUP END ------


        # STATE VARIABLES BEGIN -----
        self.changed_state = False
        self._current_grbl_line_number = 0
        self._rx_buffer_fill = 0
        self._rx_buffer_fill_last = 0
        self._progress_percent = 0
        self._progress_percent_last = 0
        # STATE VARIABLES END -----





        # MENU BAR SETUP BEGIN ----------
        self.menuBar = QMenuBar(self)

        self.action_script_load = QAction("Open Script...", self)
        self.action_script_load.triggered.connect(self._pick_script)

        self.action_script_save = QAction("Save Script!", self)
        self.action_script_save.triggered.connect(self._save_script)

        self.action_script_save_as = QAction("Save Script As...", self)
        self.action_script_save_as.triggered.connect(self._save_script_as)

        self.action_file_set = QAction("Load G-Code...", self)
        self.action_file_set.triggered.connect(self._pick_file)

        self.action_file_quit = QAction("Quit!", self)
        self.action_file_quit.triggered.connect(self._quit)

        self.action_grbl_connect = QAction("Connect", self)
        self.action_grbl_connect.triggered.connect(self.cnect)
        self.action_grbl_disconnect = QAction("Disconnect", self)
        self.action_grbl_disconnect.triggered.connect(self.disconnect)

        self.menu_file = self.menuBar.addMenu("File")
        self.menu_grbl = self.menuBar.addMenu("Grbl")

        self.menu_file.addAction(self.action_script_load)
        self.menu_file.addAction(self.action_script_save)
        self.menu_file.addAction(self.action_script_save_as)
        self.menu_file.addAction(self.action_file_set)
        self.menu_file.addAction(self.action_file_quit)
        self.menu_grbl.addAction(self.action_grbl_connect)
        self.menu_grbl.addAction(self.action_grbl_disconnect)
        self.action_grbl_disconnect.setEnabled(False)
        self.action_grbl_connect.setEnabled(True)
        # MENU BAR SETUP END ----------

        # CS SETUP BEGIN ---------
        self.cs_names = {
            1: "G54",
            2: "G55",
            3: "G56",
            4: "G57",
            5: "G58",
            6: "G59",
                }
        self.pushButton_current_cs_setzero.clicked.connect(self.current_cs_setzero)

        for key, val in self.cs_names.items():
            self.comboBox_coordinate_systems.insertItem(key, val)
        self.comboBox_coordinate_systems.activated.connect(self._cs_selected)
        # CS SETUP END ---------


        refresh_rate = 20
        self.sim_dialog = SimulatorDialog(self, refresh_rate)
        self.sim_dialog.show()


        # GRBL SETUP BEGIN -----
        self.grbl = GrblStreamer(self.on_grbl_event)
        self.grbl.setup_logging()
        self.grbl.poll_interval = 0.15
        #self.grbl.cnect()


        # SIGNALS AND SLOTS BEGIN-------
        self.comboBox_target.currentIndexChanged.connect(self._target_selected)
        self.pushButton_homing.clicked.connect(self.homing)
        self.pushButton_killalarm.clicked.connect(self.grbl.killalarm)
        self.pushButton_job_run.clicked.connect(self.job_run)
        self.pushButton_job_halt.clicked.connect(self.job_halt)
        self.pushButton_job_new.clicked.connect(self.new_job)
        self.pushButton_show_buffer.clicked.connect(self._show_buffer)
        self.pushButton_hold.clicked.connect(self.hold)
        self.pushButton_resume.clicked.connect(self.grbl.resume)
        self.pushButton_abort.clicked.connect(self.abort)
        self.pushButton_check.clicked.connect(self.check)
        self.pushButton_g53z0.clicked.connect(self.g53z0)
        self.pushButton_g53min.clicked.connect(self.g53min)
        self.pushButton_g53x0y0.clicked.connect(self.g53x0y0)
        self.pushButton_spindleon.clicked.connect(self.spindleon)
        self.pushButton_spindleoff.clicked.connect(self.spindleoff)
        self.pushButton_g0x0y0.clicked.connect(self.g0x0y0)
        self.pushButton_xminus.clicked.connect(self.xminus)
        self.pushButton_xplus.clicked.connect(self.xplus)
        self.pushButton_yminus.clicked.connect(self.yminus)
        self.pushButton_yplus.clicked.connect(self.yplus)
        self.pushButton_zminus.clicked.connect(self.zminus)
        self.pushButton_zplus.clicked.connect(self.zplus)
        self.horizontalSlider_feed_override.valueChanged.connect(self._feedoverride_value_changed)
        self.horizontalSlider_spindle_factor.valueChanged.connect(self._spindle_factor_value_changed)
        self.checkBox_feed_override.stateChanged.connect(self._feedoverride_changed)
        self.checkBox_incremental.stateChanged.connect(self._incremental_changed)
        self.lineEdit_cmdline = CommandLineEdit(self, self._cmd_line_callback)
        self.gridLayout_right.addWidget(self.lineEdit_cmdline, 7, 0, 1, 0)
        self.listWidget_logoutput.itemDoubleClicked.connect(self._on_logoutput_item_double_clicked)
        self.listWidget_logoutput.itemClicked.connect(self._on_logoutput_item_clicked)
        self.listWidget_logoutput.currentItemChanged.connect(self._on_logoutput_current_item_changed)
        self.spinBox_start_line.valueChanged.connect(self._start_line_changed)
        self.pushButton_settings_download_grbl.clicked.connect(self.grbl.request_settings)
        self.pushButton_settings_save_file.clicked.connect(self.settings_save_into_file)
        self.pushButton_settings_load_file.clicked.connect(self.settings_load_from_file)
        self.pushButton_settings_upload_grbl.clicked.connect(self.settings_upload_to_grbl)
        self.pushButton_bbox.clicked.connect(self.bbox)
        self.tableWidget_variables.cellChanged.connect(self._variables_edited)
        # SIGNALS AND SLOTS END-------


        self._startup_disable_inputs()


        # TIMER SETUP BEGIN ----------
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(150)

        self.timer_second = QTimer()
        self.timer_second.timeout.connect(self.on_second_tick)
        self.timer_second.start(1000)
        # TIMER SETUP END ----------


        # Keyboard shortcuts BEGIN ----------
        self._shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_S), self)
        self._shortcut.activated.connect(self._save_script)

        self._shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_O), self)
        self._shortcut.activated.connect(self._pick_script)

        self._shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_R), self)
        self._shortcut.activated.connect(self.reset)

        self._shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_K), self)
        self._shortcut.activated.connect(self.grbl.killalarm)

        self._shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_H), self)
        self._shortcut.activated.connect(self.homing)

        self._shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_E), self)
        self._shortcut.activated.connect(self.execute_script_clicked)
        # Keyboard shortcuts END ----------






        # initialize vars needed for heightmap/surface probing
        self.heightmap_gldata = None
        self.heightmap_dim = None
        self.heightmap_llc = None
        self.heightmap_urc = None
        self.heightmap_ipolgrid = None
        self.probe_z_first = None
        self.probe_z_at_probestart = None
        self.probe_z_expected_deviation = None
        self.probe_feed = None
        self.probe_points = None
        self.probe_values = None
        self.probe_points_count = None


        self._add_to_logoutput("=calc_eta()")
        self._add_to_logoutput("=bbox()")
        self._add_to_logoutput("=remove_tracer()")
        self._add_to_logoutput("=probe_start(100,100)")
        self._add_to_logoutput("=probe_done()")
        self._add_to_logoutput("=probe_load()")
        self._add_to_logoutput("=goto_marker()")
        self._add_to_logoutput("G38.2 Z-10 F50")
        self._add_to_logoutput("G0 X0 Y0")

        self.on_job_completed_callback = None



        self.targets = ["firmware", "simulator", "file"]
        self.comboBox_target.insertItem(0, self.targets[0])
        self.comboBox_target.insertItem(1, self.targets[1])
        self.comboBox_target.insertItem(2, self.targets[2])
        self.set_target("simulator")
        # GRBL SETUP END -----

        self.tableWidget_settings.setColumnWidth(2, 300)
        for row in range(0, 32):
            self.tableWidget_settings.setRowHeight(row, 15)

        with open("examples/scripts/blank.py", 'r') as f: c = f.read()
        self.plainTextEdit_script.setPlainText(c)

        # JOG WIDGET SETUP BEGIN -------------
        self.jogWidget = JogWidget(self, self.grbl.stream)
        self.gridLayout_jog_container.addWidget(self.jogWidget)
        # JOG WIDGET SETUP END -------------

        self.statusBar.showMessage("Ready", 3000)


        # SETTINGS SETUP BEGIN ---------------------
        self.settings = QSettings("grbl-gui.ini", QSettings.IniFormat)

        self._open_script_location = self.settings.value("open_script_location")
        if self._open_script_location == None:
            self._open_script_location = os.getcwd() + "/examples/scripts"
            self.settings.setValue("open_script_location", self._open_script_location)

        self._open_gcode_location = self.settings.value("open_gcode_location")
        if self._open_gcode_location == None:
            self._open_gcode_location = os.getcwd() + "/examples/gcode"
            self.settings.setValue("open_gcode_location", self._open_gcode_location)

        last_cs = self.settings.value("last_cs")
        if last_cs == None:
            last_cs = 1
            self.settings.setValue("last_cs", last_cs)
        self._last_cs = int(last_cs)
        # SETTINGS SETUP END ---------------------

        self._put_buffer_marker_at_line_nr = None
        self.job_run_timestamp = time.time()
        self.job_current_eta = 0

        self.current_script_filepath = None


    def closeEvent(self, event):
        """
        Overloaded Qt function
        """
        print("Exiting normally...")
        self.grbl.disconnect()
        self.sim_dialog.close()
        #event.ignore()
        event.accept()

    # =log(self.grbl.travel_dist_buffer)
    def log(self, msg, color="black"):
        self._add_to_loginput(msg, color)

    #def conosole_log(self, msg):


    def new_job(self):
        self.job_run_timestamp = time.time()
        self.grbl.job_new()
        self.spinBox_start_line.setValue(0)
        self.sim_dialog.simulator_widget.cleanup_stage()


    # modify whatever was hardcoded in the Qt Form Editor
    def modifyUi(self):
        self.pushButton_homing.setStyleSheet("background-color: rgb(102,217,239);")
        self.pushButton_resume.setStyleSheet("background-color: rgb(166,226,46);")
        self.pushButton_killalarm.setStyleSheet("color: black;")
        self.pushButton_abort.setStyleSheet("background-color: rgb(198,31,31);color: white;")
        self.pushButton_hold.setStyleSheet("background-color: rgb(219,213,50);")
        self.pushButton_check.setStyleSheet("background-color: rgb(235,122,9);")

        self.pushButton_homing.setText("⌂ Homing")
        self.pushButton_abort.setText("☠ ABRT/RST")
        self.pushButton_killalarm.setText("⚐ Kill Alarm")
        self.pushButton_job_new.setText("✧ New")
        self.pushButton_job_halt.setText("⌛ Pause")


    def setupScripting(self):
        print("Setting up Scripting Tab")
        p = self.plainTextEdit_script.palette();

        self.plainTextEdit_script.setStyleSheet("QPlainTextEdit { background-color: rgb(51, 51, 51); color: rgb(255,255,255); }");
        self.highlighter = Highlighter(self.plainTextEdit_script.document())

        self.pushButton_script_run.clicked.connect(self.execute_script_clicked)

    # to be used by scripting only
    def set_target(self, targetname):
        idx = self.targets.index(targetname)
        self.comboBox_target.setCurrentIndex(idx)

    def draw_probepoint(self, xy, z):
        current_cs_offset = self.state_hash[self.cs_names[self.current_cs]]
        z = z - self.probe_z_first

        print("DRAWING PROBE POINT")

        probepoint_origin = (xy[0], xy[1], z)
        probepoint_origin = np.add(probepoint_origin, current_cs_offset)
        self.sim_dialog.simulator_widget.item_create("Star", "probepoint_{}".format(len(self.probe_values)), "simple3d", probepoint_origin, 1, 4, (0.6, 0.6, 0.6, 1))



    def probe_load(self):
        with open("probedata.txt", 'r') as f:
            lines = f.read().split("\n")

        self.sim_dialog.simulator_widget.item_remove("probepoint_.+")

        self.probe_points_count = 0
        self.probe_points = []
        self.probe_values = []
        max_x = -999999
        min_x = 999999
        max_y = -999999
        min_y = 999999
        i = 0
        for line in lines:
            if (line.strip() == ""): continue
            m = re.match('(........) (........) (........)', line)
            x = float(m.group(1))
            y = float(m.group(2))
            z = float(m.group(3))
            self.probe_points.append([x, y])
            self.probe_values.append(z)
            self.probe_points_count += 1
            if (x > max_x): max_x = x
            if (x < min_x): min_x = x
            if (y > max_y): max_y = y
            if (y < min_y): min_y = y
            if (i == 0): self.probe_z_first = z

            self.draw_probepoint(self.probe_points[-1], self.probe_values[-1])
            i += 1

        if (len(self.probe_values) == 0):
            self.log("probedata.txt was empty!", "red")
            return

        print("LLC", self.heightmap_llc)
        print("URC", self.heightmap_urc)
        print("DIM", self.heightmap_dim)
        print("POINTS", self.probe_points)
        print("VALUES", self.probe_values)

        self._init_heightmap(max_x, max_y)



        self.state_heightmap_dirty = True



    def probe_done(self):
        with open("probedata.txt", 'w') as f:
            for i in range(0, len(self.probe_points)):
                f.write("{:8.03f} {:8.03f} {:8.03f}\n".format(self.probe_points[i][0], self.probe_points[i][1], self.probe_values[i]))

        self.probe_points_count = None

        self.log("<b>Probe data available in<br>self.probe_points and self.probe_values<br>and in probedata.txt.</b>", "orange")


    def _init_heightmap(self, dimx, dimy):
        self.sim_dialog.simulator_widget.remove_heightmap()

        dimx = round(dimx) + 1
        dimy = round(dimy) + 1

        self.heightmap_dim = (dimx, dimy)
        self.heightmap_llc = (0, 0)
        self.heightmap_urc = (dimx, dimy)

        self.heightmap_gldata = np.zeros(dimx * dimy, [("position", np.float32, 3), ("color", np.float32, 4)])

        start_x = self.heightmap_llc[0]
        end_x = self.heightmap_urc[0]
        steps_x = (1 + dimx) * 1j

        start_y = self.heightmap_llc[1]
        end_y = self.heightmap_urc[1]
        steps_y = (1 + dimy) * 1j

        grid = np.mgrid[start_x:end_x:steps_x, start_y:end_y:steps_y]
        self.heightmap_ipolgrid = (grid[0], grid[1]) # format required by interpolation


    def probe_start(self, dimx, dimy, z_feed=50, z_expected_deviation=10):
        """
        Probes area.

        Probe must almost touch the surface. First movement is up.
        Current X and Y pos will be Z=0 of resulting probe plane,
        which can be used to offset Gcode.

        @param dimx
        Width of area to be probed, as measured into the X+ direction from the current pos

        @param dimy
        Height of area to be probed, as measured into the Y+ direction from the current pos

        @param z_feed
        The probe feed towards the workpiece.

        @param z_expected_deviation
        Approximate difference in mm between the lowest Z and highest Z of the warped workpiece surface
        """

        if round(self.wpos[0]) != 0 or round(self.wpos[1]) != 0:
            self.log("<b>Probe cycle must start at X0 Y0</b>", "red")
            return

        if z_expected_deviation < 5 or z_expected_deviation > 10:
            self.log("<b>For safety reasons, z_expected_deviation shouldn't be smaller than 5 or larger than 10 mm.</b>", "red")
            return

        self._init_heightmap(dimx, dimy)

        self.probe_points = []
        self.probe_values = []
        self.probe_points_count = 0
        self.probe_z_expected_deviation = z_expected_deviation
        self.probe_feed = z_feed

        self.probe_points_planned = [ # all corners of area are pre-planned
            (0, 0),
            (dimx, 0),
            (dimx, dimy),
            (0, dimy)
        ]

        self.probe_z_at_probestart = self.wpos[2]

        self.grbl.send_immediately("G90") # absolute mode

        self.do_probe_point(self.probe_points_planned[0])


    def do_probe_point(self, pos):
        """
        Lift, go to new point, then probe

        @param pos
        tuple or list of xy coordinates relative to the current CS
        """
        new_x = pos[0]
        new_y = pos[1]

        # fast lift by z_clear from last probe trigger point
        lift_security_margin = 2
        lift_z = self.probe_z_at_probestart + self.probe_z_expected_deviation + lift_security_margin
        self.grbl.send_immediately("G0 Z{:0.3f}".format(lift_z))

        # probe is now clear of any obstacles. do fast move to new probe coord.
        self.grbl.send_immediately("G0 X{} Y{}".format(new_x, new_y))

        # the actual probing
        probe_goto_z = self.probe_z_at_probestart - self.probe_z_expected_deviation

        self.grbl.send_immediately("G38.2 Z{:0.3f} F{}".format(probe_goto_z, self.probe_feed))



    def handle_probe_point(self, mpos):
        """
        @param pos
        3-tuple of machine coordinates
        """

        if self.probe_points_count == None:
            # set to None by self.probe_done(). Stop the infinite probing cycle.
            return

        current_cs_offset = self.state_hash[self.cs_names[self.current_cs]]

        # transform from machine coords into current CS
        probed_pos = np.subtract(mpos, current_cs_offset)

        # record probe points for interpolation
        self.probe_points.append([round(probed_pos[0]), round(probed_pos[1])])
        self.probe_values.append(round(probed_pos[2], 2))

        if self.probe_points_count == 0:
            self.probe_z_first = round(probed_pos[2], 2)

        # probe next point
        self.probe_points_count += 1
        planned_points = len(self.probe_points_planned)
        if self.probe_points_count < planned_points:
            # still planned points available
            nextpoint = self.probe_points_planned[self.probe_points_count]
        else:
            nx = random.randint(self.heightmap_llc[0], self.heightmap_urc[0])
            ny = random.randint(self.heightmap_llc[1], self.heightmap_urc[1])
            nextpoint = [nx, ny]

        self.state_heightmap_dirty = True
        self.do_probe_point(nextpoint)


    def draw_heightmap(self):
        current_cs_offset = self.state_hash[self.cs_names[self.current_cs]]

        if len(self.probe_values) < 4: return # at least 4 for suitable interpol

        # I put this here to not make it a hard requirement
        # it is difficult to install on Windows
        from scipy.interpolate import griddata

        # see http://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html
        interpolated_z = griddata(
            self.probe_points,
            self.probe_values,
            self.heightmap_ipolgrid,
            method='cubic',
            fill_value=-100)

        # construct the vertex attributes in the format needed for pyglpainter
        for y in range(0, self.heightmap_dim[1]):
            for x in range(0, self.heightmap_dim[0]):
                idx = y * self.heightmap_dim[0] + x
                self.heightmap_gldata["position"][idx] = (x, y, interpolated_z[x][y])
                self.heightmap_gldata["color"][idx] = (1, 1, 1, 1)

        origin = (current_cs_offset[0] + self.heightmap_llc[0],
                  current_cs_offset[1] + self.heightmap_llc[1],
                  current_cs_offset[2] - self.probe_z_first
                  )

        print("DRAWING HEIGHTMAP", origin, self.probe_points, self.probe_values)
        self.sim_dialog.simulator_widget.draw_heightmap(self.heightmap_gldata, self.heightmap_dim, origin)


    # CALLBACKS

    def on_grbl_event(self, event, *data):
        if event == "on_stateupdate":
            self.state = data[0]
            self.mpos = data[1]
            self.wpos = data[2]

            if self.grbl.connected:
                self.changed_state = True

        elif event == "on_hash_stateupdate":
            self.state_hash = data[0]
            self.sim_dialog.simulator_widget.cs_offsets = self.state_hash
            self.state_hash_dirty = True

        elif event == "on_probe":
            pos = data[0]
            self.log("Probe: <b>{}</b>".format(pos[2]))
            self.handle_probe_point(pos)



        elif event == "on_gcode_parser_stateupdate":
            gps = data[0]

            mm_string = "G" + gps[0]
            self.label_motionmode.setText(mm_string)

            # current coordinate system
            cs_string = "G" + gps[1]
            ivd = {v: k for k, v in self.cs_names.items()}
            cs_nr = ivd[cs_string]
            self.set_cs(cs_nr)

            pm_string = "G" + gps[2]
            self.label_planemode.setText(pm_string)

            um_string = "G" + gps[3]
            self.label_unitmode.setText(um_string)

            dm_string = "G" + gps[4]
            self.label_distmode.setText(dm_string)

            fm_string = "G" + gps[5]
            self.label_feedmode.setText(fm_string)

            pm_string = "M" + gps[6]
            self.label_programmode.setText(pm_string)

            ss_string = "M" + gps[7]
            self.label_spindle_state.setText(ss_string)

            cr_string = gps[11]
            self.label_current_rpm.setText(cr_string)

        elif event == "on_processed_command":
            txt = "✓ Line {}: {}".format(data[0], data[1])
            self._add_to_loginput(txt, "green")
            self._current_grbl_line_number = int(data[0])

        elif event == "on_line_number_change":
            self._current_grbl_line_number = int(data[0])

        elif event == "on_error":
            self._add_to_loginput("<b>◀ {}</b>".format(data[0]), "red")
            if data[2] > -1:
                self._add_to_loginput("<b>✗ Error was in line {}: {}</b>".format(data[2], data[1]), "red")
            self.reset()

        elif event == "on_alarm":
            self._add_to_loginput("☹ " + data[0], "orange")

        elif event == "on_read":
            self._add_to_loginput("◀ {}".format(data[0]), "#000099")

        elif event == "on_write":
            self._add_to_loginput("▶ {}".format(data[0]), "#990099")

        elif event == "on_log":
            colors = {
                0: "black", # notset
                10: "#999999", # debug
                20: "#555555", # info
                30: "orange", # warning
                40: "red", # error
                50: "red", # critical
                }
            lr = data[0] # LogRecord instance
            message = lr.msg % lr.args
            level = lr.levelno
            levelname = lr.levelname
            filename = lr.filename
            funcname = lr.funcName
            lineno = lr.lineno

            color = colors[level]

            if level >= 40:
                txt = "{}: {} ({}:{}:{})".format(levelname, message, filename, funcname, lineno)
            else:
                txt = message



            self._add_to_loginput("✎ " + message, color)

        elif event == "on_bufsize_change":
            #what = data[0]
            msg = "{:d} Lines".format(data[0])

            self._current_grbl_buffer_size = int(data[0])
            self.label_bufsize.setText(msg)

            #enabled = self._current_grbl_buffer_size == 0
            #self.lineEdit_cmdline.setEnabled(enabled)
            #self.listWidget_logoutput.setEnabled(enabled)

        elif event == "on_rx_buffer_percent":
            self._rx_buffer_fill = data[0]

        elif event == "on_progress_percent":
            self._progress_percent = data[0]

        elif event == "on_feed_change":
            feed = data[0]
            if feed == None:
                self.lcdNumber_feed_current.display("---")
            else:
                self.lcdNumber_feed_current.display("{:d}".format(int(feed)))

        elif event == "on_streaming_complete":
            self.grbl.incremental_streaming = True

        elif event == "on_boot":
            self.grbl.poll_start()

            self.comboBox_target.setEnabled(True)
            self.pushButton_homing.setEnabled(True)
            self.pushButton_killalarm.setEnabled(True)
            self.pushButton_job_halt.setEnabled(True)
            self.pushButton_job_new.setEnabled(True)
            self.pushButton_hold.setEnabled(True)
            self.pushButton_resume.setEnabled(True)
            self.pushButton_abort.setEnabled(True)
            self.pushButton_check.setEnabled(True)
            self.pushButton_g0x0y0.setEnabled(True)
            self.pushButton_xminus.setEnabled(True)
            self.pushButton_xplus.setEnabled(True)
            self.pushButton_yminus.setEnabled(True)
            self.pushButton_yplus.setEnabled(True)
            self.pushButton_zminus.setEnabled(True)
            self.pushButton_zplus.setEnabled(True)
            self.horizontalSlider_feed_override.setEnabled(True)
            self.horizontalSlider_spindle_factor.setEnabled(True)
            self.checkBox_feed_override.setEnabled(True)
            self.checkBox_incremental.setEnabled(True)
            self.comboBox_coordinate_systems.setEnabled(True)
            self.pushButton_current_cs_setzero.setEnabled(True)
            self.pushButton_g53z0.setEnabled(True)
            self.pushButton_g53min.setEnabled(True)
            self.pushButton_g53x0y0.setEnabled(True)
            self.pushButton_spindleon.setEnabled(True)
            self.pushButton_spindleoff.setEnabled(True)
            self.spinBox_start_line.setEnabled(True)

            self.action_grbl_disconnect.setEnabled(True)
            self.action_grbl_connect.setEnabled(False)

            self.lcdNumber_feed_current.display("---")
            self.horizontalSlider_feed_override.setValue(30)
            self._feedoverride_value_changed()

            self.horizontalSlider_spindle_factor.setValue(100)
            self._spindle_factor_value_changed()

            self.spinBox_start_line.setValue(0)
            self._start_line_changed(0)





        elif event == "on_disconnected":
            self.action_grbl_disconnect.setEnabled(False)
            self.action_grbl_connect.setEnabled(True)
            self.lcdNumber_mx.display("{:0.3f}".format(8888.888))
            self.lcdNumber_my.display("{:0.3f}".format(8888.888))
            self.lcdNumber_mz.display("{:0.3f}".format(8888.888))
            self.lcdNumber_wx.display("{:0.3f}".format(8888.888))
            self.lcdNumber_wy.display("{:0.3f}".format(8888.888))
            self.lcdNumber_wz.display("{:0.3f}".format(8888.888))
            self.label_state.setText("disconnected")
            self.label_state.setStyleSheet("background-color: 'transparent'; color: 'black';")
            self._add_to_loginput("<i>Successfully disconnected!</i>")
            self._add_to_loginput("")
            self.state = None
            self._startup_disable_inputs()

        elif event == "on_settings_downloaded":
            settings = data[0] #self.grbl.get_settings()
            self.dict_into_settings_table(settings)
            self.state_stage_dirty = True

        elif event == "on_job_completed":
            self._add_to_loginput("JOB COMPLETED")
            self.grbl.current_line_number = 0
            if self.on_job_completed_callback:
                self.on_job_completed_callback()

        elif event == "on_vars_change":
            keys = data[0]
            self.var_keys_into_var_table(keys)

        elif event == "on_simulation_finished":
            gcode = data[0]
            ccs = self.cs_names[self.current_cs]
            self.sim_dialog.simulator_widget.cs_offsets = self.state_hash
            self.sim_dialog.simulator_widget.draw_gcode(gcode, self.mpos, ccs)
            self._current_grbl_line_number = self.grbl._current_line_nr
            self.spinBox_start_line.setValue(self._current_grbl_line_number)

        elif event == "on_line_sent":
            line_number = data[0]
            line_str = data[1]
            self.sim_dialog.simulator_widget.highlight_gcode_line(line_number)
            self._put_buffer_marker_at_line_nr = line_number

        elif event == "on_standstill":
            self.log("Machine is standing still")
            if (self.grbl.gps[7] == "3" and
            self.grbl.preprocessor.current_spindle_speed > 1):
                self.log("Laser Watchdog: Machine standstill but laser on. Turning off...", "red")
                self.grbl.abort()

            if self.state == "Idle":
                # restore previous CS
                self.comboBox_coordinate_systems.setCurrentIndex(self._last_cs - 1)
                self._cs_selected(self._last_cs - 1)


        elif event == "on_movement":
            pass

        else:
            self._add_to_loginput("Grbl event {} not yet implemented".format(event))


    def remove_tracer(self):
        self.sim_dialog.simulator_widget.remove_item("tracer")


    def goto_marker(self):
        pos = self.sim_dialog.simulator_widget.get_buffer_marker_pos()
        self._add_to_logoutput("G1 G53 X{:0.3f} Y{:0.3f} Z{:0.3f}".format(pos[0], pos[1], pos[2]))


    def on_second_tick(self):
        if self.grbl.job_finished == False:
            self.label_runningtime.setText(self._secs_to_timestring(time.time() - self.job_run_timestamp))
            self.label_eta.setText(self._secs_to_timestring(self.job_current_eta - time.time()))
        else:
            self.label_runningtime.setText("---")
            self.label_eta.setText("---")


    def on_timer(self):
        self.label_current_line_number.setText(str(self._current_grbl_line_number))

        if self._put_buffer_marker_at_line_nr != None:
            self.sim_dialog.simulator_widget.put_buffer_marker_at_line(self._put_buffer_marker_at_line_nr)
            self._put_buffer_marker_at_line_nr = None

        if self.state_hash_dirty == True:
            # used to draw/update origins of coordinate systems (after $# command)
            for key, tpl in self.state_hash.items():
                if re.match("G5[4-9].*", key):
                    self.sim_dialog.simulator_widget.draw_coordinate_system(key, tpl)
            self.state_hash_dirty = False

        if self.state_stage_dirty == True:
            # used to draw/update the workarea (stage) (after $$ command)
            workarea_x = int(float(self.grbl.settings[130]["val"]))
            workarea_y = int(float(self.grbl.settings[131]["val"]))
            self.sim_dialog.simulator_widget.draw_stage(workarea_x, workarea_y)
            self.state_stage_dirty = False


        if self.state_heightmap_dirty == True:
            self.draw_probepoint(self.probe_points[-1], self.probe_values[-1])
            self.draw_heightmap()
            self.state_heightmap_dirty = False


        if self.state_cs_dirty == True:
            # used to highlight coordinate systems (after $G command)
            for idx, val in self.cs_names.items():
                do_highlight = val == self.cs_names[self.current_cs]
                cs_item = self.sim_dialog.simulator_widget.programs["simple3d"].items["cs" + val]
                cs_item.highlight(do_highlight)

            #self.sim_dialog.simulator_widget.cleanup_stage()

            self.sim_dialog.simulator_widget.dirty = True
            self.state_cs_dirty = False

        if self.changed_state:
            # used to update the opengl tool, and UI displays
            mx = self.mpos[0]
            my = self.mpos[1]
            mz = self.mpos[2]
            wx = self.wpos[0]
            wy = self.wpos[1]
            wz = self.wpos[2]
            self.lcdNumber_mx.display("{:0.3f}".format(mx))
            self.lcdNumber_my.display("{:0.3f}".format(my))
            self.lcdNumber_mz.display("{:0.3f}".format(mz))
            self.lcdNumber_wx.display("{:0.3f}".format(wx))
            self.lcdNumber_wy.display("{:0.3f}".format(wy))
            self.lcdNumber_wz.display("{:0.3f}".format(wz))

            self.jogWidget.wx_current = wx
            self.jogWidget.wy_current = wy
            self.jogWidget.wz_current = wz

            # simulator update
            self.sim_dialog.simulator_widget.draw_tool(self.mpos)

            bgcolor = "transparent"
            color = "black"

            if self.state == "Idle":
                bgcolor = "green"
                color = "white"
                self.jogWidget.onIdle()

                if self.probe_points_count == None and self.grbl.streaming_complete == True:
                    # we are currently not probing, or dwell command is active
                    print("on idle: requesting hash ")
                    self.grbl.hash_state_requested = True

                if self._rx_buffer_fill == 0:
                    self.listWidget_logoutput.setEnabled(True)
                    self.lineEdit_cmdline.setEnabled(True)
                    self.spinBox_start_line.setValue(self._current_grbl_line_number)
                    self.spinBox_start_line.setEnabled(True)

            elif self.state == "Run":
                bgcolor = "blue"
                color = "white"
                self.spinBox_start_line.setEnabled(False)

            elif self.state == "Check":
                bgcolor = "orange"
                color = "white"

            elif self.state == "Hold":
                bgcolor = "yellow"
                color = "black"

            elif self.state == "Alarm":
                bgcolor = "red"
                color = "white"

            self.label_state.setText(self.state)
            self.label_state.setStyleSheet("background-color: '{}'; color: '{}';".format(bgcolor, color))

            self.changed_state = False

        if self.changed_loginput == True:
            self._render_logbuffer()
            self.changed_loginput = False

        if self._rx_buffer_fill_last != self._rx_buffer_fill:
            self.progressBar_buffer.setValue(self._rx_buffer_fill)
            self._rx_buffer_fill_last = self._rx_buffer_fill


        if self._progress_percent_last != self._progress_percent:
            self.progressBar_job.setValue(self._progress_percent)
            self._progress_percent_last = self._progress_percent


    def _startup_disable_inputs(self):
        self.comboBox_target.setEnabled(False)
        self.pushButton_homing.setEnabled(False)
        self.pushButton_killalarm.setEnabled(False)
        self.pushButton_job_halt.setEnabled(False)
        self.pushButton_job_new.setEnabled(False)
        self.pushButton_hold.setEnabled(False)
        self.pushButton_resume.setEnabled(False)
        self.pushButton_abort.setEnabled(False)
        self.pushButton_check.setEnabled(False)
        self.pushButton_g0x0y0.setEnabled(False)
        self.pushButton_xminus.setEnabled(False)
        self.pushButton_xplus.setEnabled(False)
        self.pushButton_yminus.setEnabled(False)
        self.pushButton_yplus.setEnabled(False)
        self.pushButton_zminus.setEnabled(False)
        self.pushButton_zplus.setEnabled(False)
        self.horizontalSlider_feed_override.setEnabled(False)
        self.horizontalSlider_spindle_factor.setEnabled(False)
        self.checkBox_feed_override.setEnabled(False)
        self.checkBox_incremental.setEnabled(False)
        self.comboBox_coordinate_systems.setEnabled(False)
        self.pushButton_current_cs_setzero.setEnabled(False)
        self.pushButton_g53z0.setEnabled(False)
        self.pushButton_g53min.setEnabled(False)
        self.pushButton_g53x0y0.setEnabled(False)
        self.pushButton_spindleon.setEnabled(False)
        self.pushButton_spindleoff.setEnabled(False)

    def _cmd_line_callback(self, data):
        if data == "Enter":
            cmd = self.lineEdit_cmdline.text()
            self._exec_cmd(cmd)
        elif data == "UP":
            if self.logoutput_at_end:
                itemcount = len(self.logoutput_items) - 1
                row = itemcount
                self.logoutput_at_end = False
            else:
                row = self.listWidget_logoutput.currentRow()
                row -= 1
            row = 0 if row < 0 else row
            item = self.logoutput_items[row]
            self.listWidget_logoutput.setCurrentItem(item)
            self.lineEdit_cmdline.setText(item.text())

        elif data == "DOWN":
            row = self.listWidget_logoutput.currentRow()
            itemcount = len(self.logoutput_items) - 1
            row += 1
            row = itemcount if row > itemcount else row
            item = self.logoutput_items[row]
            self.listWidget_logoutput.setCurrentItem(item)
            self.lineEdit_cmdline.setText(item.text())


    # UI SLOTS

    def settings_save_into_file(self):
        filename_tuple = QFileDialog.getSaveFileName(self, "Save File", os.getcwd(), "")
        filepath = filename_tuple[0]
        if filepath == "": return

        settings_string = self.settings_table_to_str()
        with open(filepath, 'w') as f:
            f.write(settings_string)


    def settings_load_from_file(self):
        filename_tuple = QFileDialog.getOpenFileName(self, "Open File", os.getcwd(), "")
        filepath = filename_tuple[0]
        if filepath == "": return

        settings = {}
        with open(filepath, 'r') as f:
            for line in f:
                m = re.match("\$(.*)=(.*) \((.*)\)", line)
                if m:
                    key = int(m.group(1))
                    val = m.group(2)
                    comment = m.group(3)
                    settings[key] = {
                        "val" : val,
                        "cmt" : comment
                        }

        self.dict_into_settings_table(settings)




    def settings_upload_to_grbl(self):
        settings_string = self.settings_table_to_str()
        was_incremental = self.checkBox_incremental.isChecked()

        self._add_to_loginput("<i>Stashing current buffer</i>")
        self.grbl.do_buffer_stash()
        self.grbl.incremental_streaming = True
        self.checkBox_incremental.setChecked(True)

        def settings_upload_complete():
            self.checkBox_incremental.setChecked(was_incremental)
            self._add_to_loginput("<i>Successfully uploaded settings!</i>")
            self.on_job_completed_callback = None
            self._add_to_loginput("<i>Unstashing previous buffer</i>")
            self.grbl.do_buffer_unstash()

        self.on_job_completed_callback = settings_upload_complete
        self._add_to_loginput("<i>Sending settings...</i>")
        self.grbl.current_line_number = 0
        self.set_target("firmware")
        self.grbl.stream(settings_string)


    def _start_line_changed(self, nr):
        line_number = int(nr)
        if line_number < self.grbl.buffer_size:
            self.grbl.current_line_number = line_number
            self.sim_dialog.simulator_widget.put_buffer_marker_at_line(line_number)
            self.label_current_gcode.setText(self.grbl.buffer[line_number])

    def execute_script_clicked(self):
        self.grbl.update_preprocessor_position()
        code = self.plainTextEdit_script.toPlainText()
        self.statusBar.showMessage("Executing script. Please wait...")
        try:
            exec(code, globals(), locals())
        except:
            txt = traceback.format_exc()
            txt = re.sub(r"\n", "<br/>", txt)
            self._add_to_loginput(txt)

        self.statusBar.showMessage("Executing script done!", 3000)

    def _on_logoutput_item_double_clicked(self, item):
        self._exec_cmd(item.text())


    def _on_logoutput_item_clicked(self, item):
        self.lineEdit_cmdline.setText(item.text())
        self.lineEdit_cmdline.setFocus()


    def _on_logoutput_current_item_changed(self, item_current, item_previous):
        self.lineEdit_cmdline.setText(item_current.text())
        self.logoutput_at_end = False


    def _quit(self):
        self.grbl.disconnect()
        QApplication.quit()


    def _pick_file(self):
        filename_tuple = QFileDialog.getOpenFileName(self, "Open File",self._open_gcode_location, "GCode Files (*.ngc *.gcode *.nc)")
        fpath = filename_tuple[0]
        if fpath == "": return
        self.grbl.load_file(fpath)
        self._open_gcode_location = os.path.dirname(fpath)
        self.settings.setValue("open_gcode_location", self._open_gcode_location)

    def _pick_script(self):
        filename_tuple = QFileDialog.getOpenFileName(self, "Open Script", self._open_script_location, "Python3 Files (*.py)")

        fpath = filename_tuple[0]
        if fpath == "": return
        with open(fpath, 'r') as content_file: content = content_file.read()
        self.plainTextEdit_script.setPlainText(content)
        self.label_script_filename.setText(os.path.basename(fpath))
        self.current_script_filepath = fpath

        self._open_script_location = os.path.dirname(fpath)
        self.settings.setValue("open_script_location", self._open_script_location)


    def _save_script(self):
        fname = self.current_script_filepath
        if fname == None:
            self._save_script_as()
            return

        with open(fname, 'w') as content_file:
            content_file.write(self.plainTextEdit_script.toPlainText())
        self._add_to_loginput("File {} written.".format(fname))


    def _save_script_as(self):
        filename_tuple = QFileDialog.getSaveFileName(self, "Save Script", self._open_script_location)
        fname = filename_tuple[0]
        if fname == "": return
        with open(fname, 'w') as content_file:
            content_file.write(self.plainTextEdit_script.toPlainText())
        self._add_to_loginput("File {} written.".format(fname))
        self.label_script_filename.setText(os.path.basename(fpath))



    def xminus(self):
        step = - self.doubleSpinBox_jogstep.value()
        self.grbl.send_immediately("G91")
        self.grbl.send_immediately("G0 X" + str(step))
        self.grbl.send_immediately("G90")


    def xplus(self):
        step = self.doubleSpinBox_jogstep.value()
        self.grbl.send_immediately("G91")
        self.grbl.send_immediately("G0 X" + str(step))
        self.grbl.send_immediately("G90")


    def yminus(self):
        step = - self.doubleSpinBox_jogstep.value()
        self.grbl.send_immediately("G91")
        self.grbl.send_immediately("G0 Y" + str(step))
        self.grbl.send_immediately("G90")


    def yplus(self):
        step = self.doubleSpinBox_jogstep.value()
        self.grbl.send_immediately("G91")
        self.grbl.send_immediately("G0 Y" + str(step))
        self.grbl.send_immediately("G90")


    def zminus(self):
        step = - self.doubleSpinBox_jogstep.value()
        self.grbl.send_immediately("G91")
        self.grbl.send_immediately("G0 Z" + str(step))
        self.grbl.send_immediately("G90")


    def zplus(self):
        step = self.doubleSpinBox_jogstep.value()
        self.grbl.send_immediately("G91")
        self.grbl.send_immediately("G0 Z" + str(step))
        self.grbl.send_immediately("G90")


    def _feedoverride_value_changed(self):
        val = self.horizontalSlider_feed_override.value() # 0..100
        val = int(math.exp((val+100)/23)-50) # nice exponential growth between 20 and 6000
        self.lcdNumber_feed_override.display(val)
        self.grbl.request_feed(val)
        if self.state == "Idle":
            self.grbl.send_immediately("F{:d}".format(val))

    def _spindle_factor_value_changed(self):
        val = self.horizontalSlider_spindle_factor.value() # 0..100
        self.grbl.preprocessor.spindle_factor = val / 100

    def _feedoverride_changed(self, val):
        val = False if val == 0 else True
        # first write feed to Grbl
        self._feedoverride_value_changed()
        # next set the boolean flag
        self.grbl.set_feed_override(val)


    def _incremental_changed(self, val):
        val = False if val == 0 else True
        self.grbl.incremental_streaming = val


    def abort(self):
        self.reset()


    def hold(self):
        self.grbl.hold()


    def reset(self):
        self.probe_points_count = None
        self.grbl.abort()


    def job_run(self):
        self.job_run_timestamp = time.time()
        line_nr = self.spinBox_start_line.value()
        self.grbl.job_run(line_nr)


    def job_halt(self):
        self.grbl.job_halt()
        self.grbl.gcode_parser_state_requested = True

    def stream_play(self):
        self.grbl.job_run()


    def check(self):
        self.grbl.send_immediately("$C")


    def g0x0y0(self):
        motion_mode = self.grbl.gps[4] # remember previous
        self.grbl.send_immediately("G90") # absolute mode
        self.grbl.send_immediately("G0 X0 Y0")
        self.grbl.send_immediately("G" + motion_mode) # restore


    def g53z0(self):
        # one millimeter below the limit switch
        self.grbl.send_immediately("G53 G0 Z-1")

    def g53min(self):
        workarea_x = int(float(self.grbl.settings[130]["val"]))
        workarea_y = int(float(self.grbl.settings[131]["val"]))
        self.grbl.send_immediately("G53 G0 X{:0.3f} Y{:0.3f}".format(-workarea_x, -workarea_y))

    def g53x0y0(self):
        self.grbl.send_immediately("G53 G0 X0 Y0")

    def spindleon(self):
        self.grbl.send_immediately("M3")
        self.grbl.send_immediately("S255")
        self.grbl.gcode_parser_state_requested = True

    def spindleoff(self):
        self.grbl.send_immediately("S0")
        self.grbl.send_immediately("M5")
        self.grbl.gcode_parser_state_requested = True

    def cnect(self):
        self.action_grbl_connect.setEnabled(False)
        self.grbl.cnect(self.devicepath, self.devicebaud)


    def disconnect(self):
        self.action_grbl_disconnect.setEnabled(False)
        self.grbl.disconnect()


    def draw_gcode(self, gcode, do_fractionize_arcs=True):
        ccs = self.cs_names[self.current_cs]
        self.sim_dialog.simulator_widget.cs_offsets = self.state_hash
        self.sim_dialog.simulator_widget.draw_gcode(gcode, self.mpos, ccs, do_fractionize_arcs)


    def _show_buffer(self):
        buf = self.grbl.buffer
        output = ""
        for i in range(0, len(buf)):
            output += "L{:06d} {}\n".format(i, buf[i])

        self.plainTextEdit_job.setPlainText(output)

    def _secs_to_timestring(self, secs):
        if secs < 0: return ""
        secs = int(secs)
        hours = math.floor(secs / 3600)
        secs = secs - hours * 3600
        mins = math.floor(secs / 60)
        secs = secs - mins * 60
        result = "{:02d}:{:02d}:{:02d}".format(hours, mins, secs)
        return result

    def _cs_selected(self, idx):
        self.current_cs = idx + 1
        self._last_cs = self.current_cs
        self.settings.setValue("last_cs", self._last_cs)
        self.grbl.send_immediately(self.cs_names[self.current_cs])
        self.grbl.hash_state_requested = True

    # callback for the drop-down
    def _target_selected(self, idx):
        self.current_target = self.targets[idx]
        self.grbl.target = self.current_target
        self.pushButton_job_run.setText("➾ {}".format(self.current_target))
        self.spinBox_start_line.setValue(0)
        self._start_line_changed(0)
        if self.current_target == "firmware":
            self.pushButton_job_run.setText("⚒ RUN MACHINE ⚠")
            self.pushButton_job_run.setStyleSheet("background-color: rgb(198,31,31); color: white;")
        else:
            self.pushButton_job_run.setStyleSheet("background-color: none; color: black;")



    def current_cs_setzero(self):
        self.grbl.send_immediately("G10 L2 P{:d} X{:f} Y{:f} Z{:f}".format(self.current_cs, self.mpos[0], self.mpos[1], self.mpos[2]))
        self.grbl.hash_state_requested = True

    def _variables_edited(self, row, col):
        print("_variables_edited", row, col)
        d = self._var_table_to_dict()
        self.grbl.preprocessor.vars = d

    # UTILITY FUNCTIONS

    def _var_table_to_dict(self):
        row_count = self.tableWidget_variables.rowCount()
        vars = {}
        for row in range(0, row_count):
            cell_a = self.tableWidget_variables.item(row, 0)

            if cell_a == None:
                continue

            key = cell_a.text().strip()
            key = key.replace("#", "")

            cell_b = self.tableWidget_variables.item(row, 1)
            if cell_b:
                val = cell_b.text().strip()
                if val == "":
                    val = None
            else:
                val = None

            vars[key] = val

        return vars

    def var_keys_into_var_table(self, d):
        self.tableWidget_variables.clear()
        row = 0
        for key, val in d.items():
            cell_a = QTableWidgetItem("#" + key)
            cell_b = QTableWidgetItem(val)
            self.tableWidget_variables.setItem(row, 0, cell_a)
            self.tableWidget_variables.setItem(row, 1, cell_b)
            row += 1

    def dict_into_settings_table(self, d):
        self.tableWidget_settings.clear()
        row = 0
        for key, val in sorted(d.items()):
            cell_a = QTableWidgetItem("$" + str(key))
            cell_b = QTableWidgetItem(val["val"])
            cell_c = QTableWidgetItem(val["cmt"])
            self.tableWidget_settings.setItem(row, 0, cell_a)
            self.tableWidget_settings.setItem(row, 1, cell_b)
            self.tableWidget_settings.setItem(row, 2, cell_c)
            self.tableWidget_settings.setRowHeight(row, 20)
            row += 1

    def settings_table_to_str(self):
        row_count = self.tableWidget_settings.rowCount()
        settings_string = ""
        for row in range(0, row_count):
            key = self.tableWidget_settings.item(row, 0).text()
            key = "$" + key.replace("$", "").strip()
            val = self.tableWidget_settings.item(row, 1).text().strip()
            cmt = self.tableWidget_settings.item(row, 2).text().strip()
            settings_string += key + "=" + val + " (" + cmt + ")\n"
        return settings_string

    def _exec_cmd(self, cmd):
        cmd = cmd.strip()
        if len(cmd) == 0:
            return

        self._add_to_logoutput(cmd)
        self.lineEdit_cmdline.setText("")

        if cmd[0] == "=":
            # dynamically executed python code must begin with an equal sign
            # "self." is prepended for convenience
            kls = "self"
            cmd = cmd[1:]
            cmd = "%s.%s" % (kls,cmd)
            try:
                exec(cmd)
            except:
                self._add_to_loginput("Error during dynamic python execution:<br />{}".format(sys.exc_info()))
                print("Exception in user code:")
                traceback.print_exc(file=sys.stdout)
        else:
            self.grbl.send_immediately(cmd)
            self.grbl.gcode_parser_state_requested = True

    def set_cs(self, nr):
        """
        A convenience function update the UI for CS
        """
        self.current_cs = nr
        current_cs_text = self.cs_names[self.current_cs]
        #self.label_current_cs.setText(current_cs_text)
        self.comboBox_coordinate_systems.setCurrentIndex(nr - 1)

        self.state_cs_dirty = True

    def calc_eta(self):
        proc = GcodeMachine()
        proc.cs_offsets = self.grbl.settings_hash
        proc.position_m = [0, 0, 0]

        dists_by_feed = {}

        g0_feed = float(self.grbl.settings[110]["val"])
        feed_is_overridden = self.checkBox_feed_override.isChecked()

        for line in self.grbl.buffer[self.grbl.current_line_number:]:
            proc.set_line(line)
            proc.parse_state()
            proc.override_feed()
            cf = proc.current_feed
            cmm = proc.current_motion_mode
            if cmm == None:
                continue
            elif cmm == 0:
                cf = g0_feed
            else:
                # G1, G2, G3
                if feed_is_overridden:
                    cf = self.grbl.preprocessor.request_feed

            if cf in dists_by_feed:
                dists_by_feed[cf] += proc.dist
            else:
                dists_by_feed[cf] = proc.dist

            proc.done()

        mins = 0
        for feed, dist in dists_by_feed.items():
            mins += dist / feed

        self.job_current_eta = time.time() + mins * 60
        self.label_jobtime.setText(self._secs_to_timestring(mins * 60))

    def bbox(self, move_z=False):
        lines = gcodetools.bbox_draw(self.grbl.buffer, move_z).split("\n")
        for line in lines:
            self.grbl.send_immediately(line)

    def _render_logbuffer(self):
        self.label_loginput.setText("<br />".join(self.logbuffer))
        self.scrollArea_loginput.verticalScrollBar().setValue(self.scrollArea_loginput.verticalScrollBar().maximum())

    def _add_to_loginput(self, msg, color="black"):
        html = "<span style='color: {}'>{}</span>".format(color, msg)
        #print(html)
        self.logbuffer.append(html)
        self.changed_loginput = True

    def _add_to_logoutput(self, line):
        item = QListWidgetItem(line, self.listWidget_logoutput)
        self.logoutput_items.append(item)
        self.listWidget_logoutput.setCurrentItem(item)
        self.listWidget_logoutput.scrollToBottom()
        self.logoutput_at_end = True

    def homing(self):
        self.grbl.homing()
