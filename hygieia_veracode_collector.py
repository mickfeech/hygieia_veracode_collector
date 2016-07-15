#!/usr/bin/env python

import re
import xmltodict
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta 
import time 
from pymongo import MongoClient 
from bson.objectid import ObjectId 
import glob


def isNewCollectionItem(db, name):
   collection_items = db.collector_items.find({"niceName": "Veracode", "description": name})
   if collection_items.count() > 0:
      return False
   else:
      return True

def addNewCollectionItem(db, info):
   data = {}
   data['niceName'] = 'Veracode'
   data['enabled'] = False
   data['pushed'] = True
   data['collectorId'] = getCollectorId(db)
   data['description'] = info['description']
   data['options'] = info['options']
   data['_class'] = 'com.capitalone.dashboard.model.CollectorItem'
   db.collector_items.insert(data)
 
def getCollectorId(db):
   return db.collectors.find({'name': 'Veracode'})[0]['_id']

def getCollectorItemId(db, name):
   return db.collector_items.find({'niceName': 'Veracode', 'description': name})[0]['_id']

def isNewCodeItem(db, version):
   code_items = db.code_quality.find({'version': version, 'type': 'SecurityAnalysis'})
   if code_items.count() > 0:
      return False
   else: 
      return True

def loadConfig():
   global cfg
   cfg = configparser.ConfigParser()
   cfg_path = unicode(os.path.dirname(os.path.realpath(__file__)) + '/hygieia_veracode.properties', 'utf8')
   cfg.read(cfg_path)

def main():
   loadConfig()
   mongo_client = MongoClient(cfg['db']['host'])
   db = mongo_client.dashboard
   db.authenticate(cfg['db']['username'], cfg['db']['password'])

   namespace = "{https://www.veracode.com/schema/reports/export/1.0}"
   files = glob.glob('detailedreport*.xml')
   for file in files:
      tree = ET.parse(file)
      root = tree.getroot()
      app_name = root.attrib['app_name']
      app_id = root.attrib['app_id']
      build_id = root.attrib['build_id']
      version = app_name + '#' + str(build_id)
      if isNewCodeItem(db, version):
         if isNewCollectionItem(db, app_name):
            info = {}
            info['description'] = app_name
            info['options'] = {}
            info['options']['projectName'] = app_name
            info['options']['projectId'] = app_id
            info['options']['instanceUrl'] = 'https://analysiscenter.veracode.com'
            addNewCollectionItem(db, info)
         blocker = critical = major = minor = 0
         for flaw in root.findall(".//{0}flaw".format(namespace)):
            if 'accepted' not in flaw.attrib['mitigation_status']:
               if int(flaw.attrib['severity']) == 5:
                  blocker += 1
               elif int(flaw.attrib['severity']) == 4:
                  critical += 1
               elif int(flaw.attrib['severity']) == 3:
                  major += 1
               else:
                  minor += 1
         data = {}
         data['_id'] = ObjectId()
         data['collectorItemId'] = getCollectorItemId(db, app_name)
         data['timestamp'] = int((time.mktime((datetime.strptime(root.attrib['last_update_time'], '%Y-%m-%d %H:%M:%S %Z')).timetuple()))*1000)
         data['name'] = app_name
         data['type'] = 'SecurityAnalysis'
         data['metrics'] = []
         for item in ['blocker', 'critical', 'major', 'minor']:
            flaw = {}
            flaw['name'] = item
            flaw['formattedValue'] = eval(item)
            if (item == 'blocker' or item == 'critical'):
               flaw['status'] = 'Alert'
            elif item == 'major':
               flaw['status'] = 'Warning'
            else:
               flaw['status'] = 'Ok'
            data['metrics'].append(flaw)
            flaw = {}
         data['version'] = version
         data['url'] = 'https://analysiscenter.veracode.com/api/2.0/detailedreportpdf.do?build_id=' + str(build_id)
         db.code_quality.insert(data)

if __name__ == "__main__":
    main()

