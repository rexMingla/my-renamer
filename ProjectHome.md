## Introduction ##
This [PyQt](http://www.riverbankcomputing.co.uk/software/pyqt/) GUI application allows you to rename files in your media collection using information retrieved from online tv and movie sources. _See below for the libraries used_.

Yes, this is a solved problem but it was something I thought would be interesting enough to try myself. And yes, this is probably only read by me; but if you are here, welcome! Any comments/suggestions are appreciated.

## Basic usage ##

The application is comprised of a single window with 4 widgets.
  * Input Settings - used to sets where to search for media files
  * Workbench - used to modify media metadata
  * Output Settings - used to configure output format and location
  * Message log - to display an important application messages

![https://my-renamer.googlecode.com/svn/wiki/screenshots/renamerWorkflow.jpg](https://my-renamer.googlecode.com/svn/wiki/screenshots/renamerWorkflow.jpg)

  1. Select mode: either movies or tv shows (this may be extended to music later)
  1. Set input parameters: Set the input folder and filters. When you are happy, hit search and the app will start searching the folders for media files. The app will make an educated guess at tv (season name and number) and movie titles based on respective folder and file names. This information is then used to search for more media metadata.
  1. Edit metadata for each of your media files.
  1. Set output filename and hit the rename button.

## Package ##
  * To get the exe go to the downloads section: http://code.google.com/p/my-renamer/downloads/list.
  * Unzip the package and run renamer.exe.
(Sorry no installer)

## Dependencies ##
The projects uses the following libraries:
  * python (tested on 2.7)
  * [PyQt](http://www.riverbankcomputing.co.uk/software/pyqt/)
  * [py2exe](http://www.py2exe.org/)
  * [jsonpickle](https://github.com/jsonpickle/jsonpickle/)
  * tv APIs:
    * [theTVDB.com](http://github.com/dbr/tvdb_api)
    * [tvrage.com](http://pypi.python.org/pypi/python-tvrage/0.1.4)
  * movie APIs:
    * [IMDb.com](https://github.com/caruccio/pymdb)
    * [rottentomatoes.com](https://github.com/zachwill/rottentomatoes,)
    * [themoviedb.org](https://github.com/dbr/themoviedb)

Thanks also to:
  * The wand icon comes from [Umar Irshad](http://www.designkindle.com/2011/10/07/build-icons/)
  * Button images come from [Tomas Gajar](http://www.smashingmagazine.com/2011/12/29/freebie-free-vector-web-icons-91-icons/)

## Bugs / Improvements ##
Lised at http://code.google.com/p/my-renamer/issues/list

## Caveats ##
  * Only tested with:
    * Windows vista and 7
    * Python 2.7