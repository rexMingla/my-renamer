#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: TODO list
# --------------------------------------------------------------------------------------------------------------------
#
# Date Reported  Date Completed  Bug/Impr/Feat Item
# --------------------------------------------------------------------------------------------------------------------
#    2011-04-29  2011-05-01      Impr          Model Items should be composed of source and destination items
#    2011-04-29  2011-05-01      Feat          Move/copy file functionality
#    2011-04-29  2011-05-02      Bug           Figure out cause of: "QObject::startTimer: QTimer ..."
#    2011-05-01  2011-05-01      Impr          Enable/disable buttons
#    2011-05-02  2011-05-02      Impr          Save window layout
#    2011-05-02  2011-05-02      Impr          Use dock widgets
#    2011-05-02  2011-05-22      Impr          Improve logging
#    2011-05-04  2011-05-04      Impr          Restructure libs
#    2011-05-04  2011-05-11      Feat          Package with py2exe
#    2011-05-05  2011-05-05      Bug           Fix Filename resolution bug: "/Season 2/.track" -> epNum: 2 not -1 
#    2011-05-05  2011-05-09      Impr          Thread out move/copy
#    2011-05-05  2011-05-11      Bug           Transition from READY to MISSING_NEW is incorrect in work bench
#    2011-05-05  2011-05-08      Impr          Add filename completer to file/folder dialogs
#    2011-05-16  2012-07-20      Impr          Colour unresolved folders in list
#    2011-05-16  2011-05-16      Impr          Select/deselect all option
#    2011-05-16  2011-05-16      Impr          Tooltips
#    2011-05-16  2011-05-16      Impr          file extension filtering. *.avi will break it at the moment
#    2011-05-23  2012-07-24      Impr          Show preview in changeSeasonWidget denoting how many episode are in the season
#    2011-05-23  2012-07-15      Impr          Remove dependence on Qt in serialization (removed serialization)

#    v 0.2 (really 0.9)
#    2012-07-13  2012-07-15      Impr          Replace serialization with jsonpickle lib
#    2012-07-13  2012-07-22      Impr          Save log to file
#    2012-07-13  2012-07-22      Impr          Increase logging. timing, etc.
#    2012-07-13  2012-07-15      Impr          Allow stopping of search / rename
#    2012-07-13  2012-07-22      Impr          Better gui for tv series lookup (and episode rename)
#    2012-07-13  2012-07-15      Impr          Cache tv series lookups
#    2012-07-13  2012-07-15      Impr          Show progress for folder search
#    2012-07-13  2012-07-20      Impr          Integrate with movie code

#    v 0.3 (probably 0.99)
#    2012-07-15                  Impr          Fix setup.py
#    2012-07-23                  Impr          Support multiple genres. maybe create links?
#    2012-07-23                  Impr          Rename subtitle files too
#    2012-07-23                  Impr          Fix command line opts
#    2012-07-23                  Impr          Clean up and optimise the filth. at least make it more pythonic.
#    2012-07-23                  Impr          Support multiple IMDB and TVDB apis and allow use preference.


