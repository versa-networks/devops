#!/usr/bin/env python2
#si sw=2 sts=2 et
import os, sys, signal
import json
import base64
import logging
import logging.handlers
import collections

pyVer = sys.version_info

class Vnms:
  def __init__(self, _vdict):
    self.data = _vdict

class Analytics:
  def __init__(self, _vdict):
    self.data = _vdict

class Controller:
  def __init__(self, _vdict):
    self.data = _vdict

class Customer:
  def __init__(self, _vdict):
    self.data = _vdict

class Admin:
  def __init__(self, _vdict):
    self.data = _vdict

def json_loads(_str,**kwargs):
    global mlog
    try:
      _jstr = json.loads(_str,**kwargs)
      return _jstr
    except Exception as ex:
       mlog.error('Json load failed: {}'.format(ex))
       sys.test('Json load failed: {}'.format(ex))

def init(infile, logfile,log_size,_name, _debug):
    global vnms, analy, cntlr, cust, admin, auth, debug, mlog, mdict

    fp = open(infile,"r")
    jstr = fp.read()
    fp.close()
    mdict=json_loads(jstr,object_pairs_hook=collections.OrderedDict)
    for _keys,_val in mdict.items():
      if _keys.lower() == "vnms": 
        vnms =  Vnms(_val)
      elif _keys.lower() == "analytics": 
        analy = Analytics(_val)
      elif _keys.lower() == "controller": 
        cntlr =  Controller(_val)
      elif _keys.lower() == "customer": 
        cust = Customer(_val)
      elif _keys.lower() == "admin": 
        admin = Admin(_val)
        if pyVer.major == 3:
          admin.data['new_dir']['auth'] = base64.b64encode(bytes('%s:%s' % (str(admin.data['new_dir']['user']), str(admin.data['new_dir']['password'])),"utf-8")).decode('ascii')
          admin.data['old_dir']['auth'] = base64.b64encode(bytes('%s:%s' % (str(admin.data['old_dir']['user']), str(admin.data['old_dir']['password'])),"utf-8")).decode('ascii')
        else: 
          admin.data['new_dir']['auth'] = base64.encodestring('%s:%s' % (str(admin.data['new_dir']['user']), str(admin.data['new_dir']['password']))).replace('\n', '')
          admin.data['old_dir']['auth'] = base64.encodestring('%s:%s' % (str(admin.data['old_dir']['user']), str(admin.data['old_dir']['password']))).replace('\n', '')
    mlog,fhandler,shandler = setup_logging(logfile,log_size,_name)
    debug = _debug 
    return mlog,fhandler,shandler

def setup_logging(logfile,log_size,_name):
        ## Enable logging
        log = logging.getLogger(_name)
        while len(log.handlers) > 0:
          h = log.handlers[0]
          log.removeHandler(h)
          #print("Number of handlers={}".format(len(log.handlers)))

        # Set logging level
        log.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s")
        cli_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # create a rotating handler
        handler = logging.handlers.RotatingFileHandler(logfile,
                                    maxBytes=log_size, backupCount=5)
        stdouth = logging.StreamHandler(sys.stdout)
        stdouth.setLevel(logging.WARNING)
        handler.setLevel(logging.INFO)

        # add formatter to ch
        stdouth.setFormatter(cli_formatter)
        handler.setFormatter(formatter)

        # Add the log message handler to the logger
        log.addHandler(handler)
        log.addHandler(stdouth)
        #cls.log = log
        #cls.log_info(cls.VERSA_BANNER)
        return log,handler,stdouth

def setup_level(hndlr, level=logging.DEBUG):
    hndlr.setLevel(level) 
    return
