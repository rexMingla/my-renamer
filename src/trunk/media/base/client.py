#!/usr/bin/env python
# --------------------------------------------------------------------------------------------------------------------
# Project:             my-renamer
# Repository:          http://code.google.com/p/my-renamer/
# License:             Creative Commons GNU GPL v2 (http://creativecommons.org/licenses/GPL/2.0/)
# Purpose of document: Module that defines the interface to the info clients and the container to client them
# --------------------------------------------------------------------------------------------------------------------
from common import utils

# --------------------------------------------------------------------------------------------------------------------
class BaseInfoClient(object):
  """ class to retrieve information from an online (or other) resource using a 3rd party library (source)
  Attributes (read only):
    display_name: name of the library used
    source_name: name of the website the library is connected to
    url: url of the website being connected to
    has_lib: was the library loaded successfully? ie. did import succeed.
    requires_key: some sources require a key in order to access
  
  Attributes (configurable via media.base.widget.EditInfoClientsWidget):
    key: string key. The client is not required to do any validation of the key, it is assumed that the 3rd party
      library
    is_enabled: a boolean indicating whether or not to use the client for information retrieval. 
      Perhaps when a client is running slow you may want to disable the client. (default True).
      
  Only one function needs to be overwritten. 
  """
  def __init__(self, display_name, source_name, url, has_lib, requires_key):
    super(BaseInfoClient, self).__init__()
    self.display_name = display_name
    self.source_name = source_name
    self.url = url
    self.has_lib = has_lib
    self.requires_key = requires_key
    self.key = ""
    self.is_enabled = True

  def prettyName(self):
    """ display name, also used to uniquely identify client in """
    return "{} ({})".format(self.source_name, self.display_name)

  def isAvailable(self):
    """ is the library in a state ready for use """
    return self.has_lib and (not self.requires_key or bool(self.key))

  def isActive(self):
    """ is the library in use. only active libraries will be called by the InfoStore """
    return self.isAvailable() and self.is_enabled

  def getInfo(self, search_params):
    """ returns a ResultHolder object for the first match found 
    Args: 
      search_params: media.base.BaseSearchParams object used to assist client finding info    
    """
    infos = self._getAllInfo(search_params)
    return infos[0] if infos else None

  def getAllInfo(self, search_params):
    """ returns a list of ResultHolder objects for all items matching the search parameters 
    Args: 
      search_params: media.base.BaseSearchParams object used to assist client finding info
    """    
    ret = []
    try:
      ret = self._getAllInfo(search_params) if self.isAvailable() else None
    except Exception as ex:
      utils.logWarning("uncaught exception in lib. lib={} params={} ex={}".format(self.display_name,
          search_params.getKey(), ex))
    return ret

  def _getAllInfo(self, search_params):
    raise NotImplementedError("BaseInfoClient._getAllInfo not implemented")

# --------------------------------------------------------------------------------------------------------------------
class ResultHolder(object):
  """ Holds info media.base.types.BaseInfo object and source name (typically 
  media.base.client.BaseInfoClient.prettyName(). Without this object it was difficult to tell which clients were 
  returning which results. 
  
  Currently used for displaying in the search results of media.base.widget.EditItemWidget
  
  Attributes:
    info: media.base.types.BaseInfo
    source_name: string
  """
  def __init__(self, info, source_name):
    super(ResultHolder, self).__init__()
    self.info = info
    self.source_name = source_name

# --------------------------------------------------------------------------------------------------------------------
class InfoClientHolder(object):
  """ Container holding the list of media.base.InfoClient objects.
  The order is important, as it defines the order in which info clients are queried for information. 
  In the case of getInfo(), clients are queried until a non null result is returned. 
  
  See media.tv.client.getInfoClientHolder() and media.movie.client.getInfoClientHolder() for sample usage.
  
  The clients can be modified using the media.base.widget.EditInfoClientsWidget.
  """
  def __init__(self):
    super(InfoClientHolder, self).__init__()
    self.clients = []

  def addClient(self, client):
    """ adds client to the end of list unless it is found to be already in the list """
    index = self.getStoreIndex(client)
    if index == -1:
      self.clients.append(client)
    else:
      self.clients[index] = client

  def getStoreIndex(self, name):
    return next( (i for i, client in enumerate(self.clients) if name == client.prettyName() ), -1)

  def getInfoClientHolder(self, name):
    return next( (client for client in self.clients if name == client.prettyName() ), None)

  def getAllActiveNames(self):
    return [client.prettyName() for client in self.clients if client.isActive()]

  def getConfig(self):
    """ serializes clients so that ordering and is_enabled information can be retrieve on restart """
    ret = []
    for i, client in enumerate(self.clients):
      ret.append({"name": client.prettyName(), "requires_key": client.requires_key, "key": client.key, "index": i})
    return ret

  def setConfig(self, data):
    """ deserializes list of dictionary data so to ordering and is_enabled information as per previous state """
    for i, values in enumerate(data):
      index = self.getStoreIndex(values["name"])
      if index != -1 and index != i:
        client = self.clients.pop(index)
        self.clients.insert(values["index"], client)
        client.requires_key = values["requires_key"]
        client.key = values["key"]

  def getInfo(self, search_params, default=None):
    """ get info api  """
    return next(self.getAllInfo(search_params), ResultHolder(default, "")).info

  def getAllInfo(self, search_params):
    """ returns an iterator to ResultHolder objects """
    for client in self.clients:
      if client.isActive():
        for info in client.getAllInfo(search_params):
          yield ResultHolder(info, client.source_name)

