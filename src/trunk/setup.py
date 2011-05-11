#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Building of exe. Run command: 'python setup.py py2exe'
# --------------------------------------------------------------------------------------------------------------------
from py2exe.build_exe import py2exe
from distutils.core import setup
import os

uiFiles = []
for f in os.listdir("ui"):
 if f.endswith(".ui"):
   uiFiles.append("ui/" + f)

setup(
    version = "0.0.1",
    name = "Renamer",
    description = "ReNamer Beta",

    # targets to build
    console = 
    [ 
      {
        "script":"main.py"
      } 
    ],
    options = 
    {
      "py2exe":{"includes":["sip", "PyQt4.uic", "PyQt4.QtCore"],} 
    },
    data_files=[("ui", uiFiles)]
)
