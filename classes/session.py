import datetime
import os

from classes.machine import Machine
from classes.svg import SVG

'''
        Session Class

        This class manages all the parts and works as
        a locator and bridge between emitters and receivers
        of GCode. It is also built to scale up to manage multiple
        CNC Machines running the same or separate projects.

        add: adds a machine or emitter class based on the file name
        if it's an svg then it will load and parse it, anything else
        will create a new machine. For instance passing a .txt file
        will create a machine that emits gcode to that file.
'''
class Session:
    def __init__(self):
        self.start = datetime.datetime.now()
        self.machines = []
        self.emitters = []
        
    def add(self, name="", path=""):
        fileName, fileExtension = os.path.splitext(path)
        if fileExtension == '.svg':
            print("Adding emitter for " + path)
            self.emitters.append(SVG(name,path))
        else:
            print("Adding machine for " + path)
            self.machines.append(Machine(name,path))
        return self
    
    def machine(self, name):
        for m in self.machines:
            if m.name == name:
                return m
        return False
    
    def emitter(self,name):
        for e in self.emitters:
            if e.name == name:
                return e
        return False