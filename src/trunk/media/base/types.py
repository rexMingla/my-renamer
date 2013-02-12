#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Base classes to be implented by concrete tv, movie (and whatever else) derived classes
# --------------------------------------------------------------------------------------------------------------------
from common import file_helper

""" Current supported modes are MOVIE_MODE and TV_MODE with the intention to support more in the future. eg MUSIC_MODE,
BOOK_MODE. The mode is the central piece of data within the system. Each mode has its own:
  * Info (deriving from media.base.BaseInfo) describing the metadata properties of the media. Eg. for MOVIE mode
      these properties include title, year, disc number.
  * Item (deriving from media.base.BaseRenameItem) matching a filename to an Info object
  * SearchParams (deriving from media.base.BaseSearchParams) information given to InfoClients that they can return 
      Info objects.
  * Set of custom widgets required for configuration settings, finding files and building rename item lists.

"""

MOVIE_MODE = "movie"
TV_MODE = "tv"

VALID_MODES = (MOVIE_MODE, TV_MODE)

# --------------------------------------------------------------------------------------------------------------------
class BaseInfo(object):
  """ stores all the metadata that can be used to format the renaming of files. 
  Attributes:
    mode: string representation of mode (only really used for logging/gui atm)
  """
  def __init__(self, mode):
    assert(mode in VALID_MODES)
    self.mode = mode
    
  def getSearchParams(self):
    """ returns a base.types.BaseSearchParams that is used by the 
    base.client.InfoClientHolder as search criteria for searches
    """
    raise NotImplementedError("BaseInfo.getSearchParams not implemented")

  def isValid(self):
    """ is the info object usable by the application """
    return True

# --------------------------------------------------------------------------------------------------------------------
class BaseRenameItem(object):
  """ object to represent a file to be renamed. this is represented by a filename and the metadata (info)
  required to rename the file. 
  Attributes:
    filename: absolute path to the file
    _info: media.base.BaseInfo object
    is_enabled: boolean. Does the user want to rename the file? This is controlled through the check box in the 
      Workbench widget.
  """
  #Statuses for the item. Derived classes will add failed states as required
  READY          = "Ready"    # item has enough data to be renamed
  UNKNOWN        = "Unknown"  # initial state
  
  def __init__(self, filename, info, is_enabled=True):
    super(BaseRenameItem, self).__init__()
    self.filename = filename
    self._info = info
    self.is_enabled = is_enabled
    
  def getSourceFolder(self):
    return file_helper.FileHelper.dirname(self.filename)
  
  def getFileSize(self):
    return file_helper.FileHelper.getFileSize(self.filename)
  
  def getFileExt(self):
    return file_helper.FileHelper.extension(self.filename)

  def setInfo(self, info):
    self._info = info

  def getInfo(self):
    return self._info

  def getStatus(self):
    """ returns string representation of status. must return BaseRenameItem.READY on success (see canEdit()), any other 
    value will imply failure. """
    raise NotImplementedError("BaseRenameItem.getStatus not implemented")
  
  def canEdit(self):
    """ can the properties associated with this item be edited? basically if the file exists we can otherwise there 
    is no point setting properties. this function decides whether or not to display a check box in the Workbench widget
    Returns:
      boolean
    """
    return file_helper.FileHelper.getFileSize(self.filename) > 0

  def isValid(self):
    """ is the item is a state where it can be renamed? """
    return self.getStatus() == BaseRenameItem.READY and self.getInfo().isValid()  
  
  def canPerformRename(self):
    """ is this is true the file will be renamed by the Module """
    return self.isValid() and self.is_enabled

# --------------------------------------------------------------------------------------------------------------------
class BaseSearchParams(object):
  """ objects sent to the InfoClients so to retrieve BaseInfo objects """
  def getKey(self):
    """ creates an identifier, primarily used in base.manager.BaseManager as the id for the cache dictionary """
    raise NotImplementedError("BaseSearchParams.getKey not implemented")

  def getInfo(self):
    """ create an base.types.BaseInfo object only used in base.manager.BaseManager.getInfo(). This function is a 
    candidate for deprication as it doesn't really make sense. """
    raise NotImplementedError("BaseSearchParams.getInfo not implemented")

