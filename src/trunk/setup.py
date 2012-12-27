#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Building of exe. Run command: 'python setup.py py2exe'
# --------------------------------------------------------------------------------------------------------------------
import os
import glob

from py2exe.build_exe import py2exe
from distutils.core import setup

import app

setup(
    version = app.__VERSION__,
    name = app.__APP_NAME__,
    description = "Media file renamer tool written in PyQt",
    author = "Tim Mathas",
    author_email = "rexmingla@gmail.com",
    url = "http://code.google.com/p/my-renamer/",
    # targets to build
    console = [{"script":"renamer.py", 
                "icon_resources": [(1, "img/icon.ico")]
               }],
    options = {
      "py2exe": {
        "includes": ["sip", "PyQt4.uic", "PyQt4.QtCore", "jsonpickle", 
                     "pymdb", "tmdb", "rottentomatoes", #movies
                     "tvdb_api", "tvrage", #tv
                    ],
        "dll_excludes": ["MSVCP90.dll"]
      } 
    },
    data_files = [("ui", glob.glob("ui/*.ui")),
                  ("img", glob.glob("img/*")),
                  ("imageformats", [r"C:\Python27\Lib\site-packages\PyQt4\plugins\imageformats\qico4.dll"])]
)

     