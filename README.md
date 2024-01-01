# grbl-gui

Graphical User Interface for the "grbl" CNC controller.

Python scripting and realtime OpenGL 3D visualization of gcode plus
streaming to the [grbl](https://github.com/grbl/grbl) CNC controller,
implemented in Python3 with Qt5 bindings.

![The main window](screenshots/helloworldgui.jpg)

![The simulator window](screenshots/helloworldsim.jpg)

![The simulator window](screenshots/bumpifysim.jpg)

![The simulator window](screenshots/circletestsim.jpg)

![The simulator window](screenshots/lasercutsim.jpg)

![The simulator window](screenshots/pixeltolasersim.jpg)


## Requirements

* Your graphics hardware and drivers need to support at least OpenGL version 2.1 with GLSL version 1.20.
* An Arduino board with grbl version 0.9j flashed onto it (however, the Gcode simulator and scripting will even work without an Arduino board connected)


## Usage

```sh
pipenv run grbl-gui.py gui --path /dev/ttyUSB0 --baud=115200
```

## Development

Update Python code from Qt .ui file

```sh
pyuic5 -o lib/qt/grbl_gui/ui_mainwindow.py lib/qt/grbl_gui/mainwindow.ui
```
