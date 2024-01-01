# grbl-gui

Graphical User Interface for the "grbl" CNC controller; implemented in Python 3 with Qt 6 bindings.


## Features

* Real-time displays of grbl's state (mode, working position, machine position, motion mode, plane
    mode, distance mode, feed mode, unit mode, program mode, spindle mode, spindle RPM, serial read
    buffer untilization)
* Quick push buttons for
   * Abort/reset
   * Kill alarm
   * Homing
   * Check mode
   * Holding and Resuming
   * Generation of g-code that draws the bounding box around all other g-code (automatically goes to
       Hold mode, user can continue by pressing the Resume button)
   * Go to maximum Z
   * Go to upper right corner
   * Go to lower right corner
   * Go to coordinate system origin
   * Spindle off
   * Spindle maximum
* Simulation (dry-run) mode
* Sliding feed override
* interactive preprocessor g-code variable editing
* Buffer display
* interactive grbl's settings table
* Detached-window, real time, 3D visualization of g-code and tool position (using https://github.com/michaelfranzl/pyglpainter)
* Embedded Python scripting for procedural g-code generation and transformation
* Robust streaming of g-code to grbl (using https://github.com/michaelfranzl/grbl-streamer)
* Jogging buttons
* Coordinate system switching
* Interactive, one-line command line interface to grbl
* Supports grbl variant 0.9 (but 1.1 should work too thanks to grbl-streamer)
* Event timeline (of commands sent and received)


## Screenshots

![The main window](screenshots/helloworldgui.jpg)

![The simulator window](screenshots/helloworldsim.jpg)

![The simulator window](screenshots/bumpifysim.jpg)

![The simulator window](screenshots/circletestsim.jpg)

![The simulator window](screenshots/lasercutsim.jpg)

![The simulator window](screenshots/pixeltolasersim.jpg)


## Requirements

* Your graphics hardware and drivers need to support at least OpenGL version 2.1 with GLSL version 1.20.
* An Arduino board with grbl version 0.9j flashed onto it (however, the Gcode simulator and scripting will even work without an Arduino board connected) and connected to your computer.



## Dependencies

Dependencies are managed using pipenv:

```sh
pip install pipenv --user
pipenv install -d
```

## Usage

To start:

```sh
pipenv run grbl-gui.py gui --path /dev/ttyUSB0 --baud=115200
```

## Development

Update Python code from Qt .ui file

```sh
pyuic6 -o lib/qt/grbl_gui/ui_mainwindow.py lib/qt/grbl_gui/mainwindow.ui
```
