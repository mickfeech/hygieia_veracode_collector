# hygieia_veracode_collector

Veracode scan collector / parser for the Hygieia DevOps Dashboard you will need to provide a hygieia_veracode.properties property file (there is a sample provided).

## Python Requirements

* re
* xmltodict
* json
* xml.etree.ElementTree
* time
* pymongo
* bson.Objectid
* glob

## Configuration

*hygieia_veracode.properties*
```
[db]
host=localhost
username=db
password=dbpass
```

## Uses

*Setup a cronjob to regularly gather jenkins build data*

```
*/15 * * * * /home/hygieia/hygieia_veracode_collector.py >/dev/null 2>&1
```
