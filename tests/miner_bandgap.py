#!/usr/bin/env python

# example to query minimal-energy band gaps
# v080514

import sys
import os
import math
import json
import time

starttime = time.time() # benchmarking

sys.path.insert(0, os.path.realpath(os.path.dirname(os.path.abspath(__file__)) + '/../'))
from core.settings import settings, connect_database, check_db_version


db_choice = None
if settings['db']['type'] == 'sqlite':
    try: db_choice = sys.argv[1]
    except IndexError: sys.exit('No DB name defined!')
    
db = connect_database(settings, db_choice)
if not db: sys.exit('Connection to DB failed!')

# check DB_SCHEMA_VERSION
incompatible = check_db_version(db)
if incompatible:
    sys.exit('Sorry, database ' + workpath + ' is incompatible.')

# ^^^ the obligatory code above, the actual procedures of interest below VVV

cursor = db.cursor()
try: cursor.execute( 'SELECT info, energy FROM results' )
except: sys.exit('Fatal error: ' + "%s" % sys.exc_info()[1])

objects = {}

while 1:
    row = cursor.fetchone()
    if not row: break
    item = json.loads(row[0])
    item['e'] = row[1]
    if not item['standard'] in objects:
        if 'bandgap' in item and 0 < item['bandgap'] < 15: # avoid non-physical things
            objects[ item['standard'] ] = {'e': item['e'], 'gap': item['bandgap'] }
    else:
        if objects[ item['standard'] ]['e'] > item['e'] and 'bandgap' in item and 0 < item['bandgap'] < 15: # avoid non-physical things:
            objects[ item['standard'] ] = {'e': item['e'], 'gap': item['bandgap'] }

if not objects: sys.exit('DB contents do not satisfy the criteria!')

# sorting
gaps, formulae = [ i['gap'] for i in objects.values() ], objects.keys()
gaps, formulae = zip( *sorted( zip(gaps, formulae) ) ) # sorting in accordance, by first

for n, i in enumerate(formulae):
    if gaps[n]:
        print i, "\t", gaps[n]

print "Done in %1.2f sc" % (time.time() - starttime)
